#!/usr/bin/env python3
"""
Hammer Test - Hit production server until it breaks

Uploads real images to Render.com to find breaking point.
Test 1: Upload capacity (no caption generation)
Test 2: Gemini API rate limits (separate)

Usage:
    python3 tests/hammer_test.py --test upload --concurrent 50
    python3 tests/hammer_test.py --test gemini --rate 100
"""

import argparse
import base64
import os
import sys
import time
import threading
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

try:
    import requests
except ImportError:
    print("ERROR: pip3 install --break-system-packages requests")
    sys.exit(1)

BASE_URL = "https://idem307-image-metadata-generator.onrender.com"
ACCESS_CODE = 'kind_gemini_key'


def create_test_image(size_kb=100):
    """Create JPEG image of specified size."""
    # Calculate dimensions for target file size
    # Rough estimate: 1920x1080 JPEG ≈ 200KB at quality 85
    if size_kb <= 50:
        width, height, quality = 960, 540, 85
    elif size_kb <= 150:
        width, height, quality = 1920, 1080, 85
    else:
        width, height, quality = 2560, 1440, 85

    img = Image.new('RGB', (width, height), color=(73, 109, 137))
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=quality)
    img_bytes = buffer.getvalue()
    actual_size_kb = len(img_bytes) / 1024

    return img_bytes, actual_size_kb


def upload_batch(batch_id, num_images=30):
    """Upload N images to server - single session."""
    result = {
        'batch_id': batch_id,
        'success': False,
        'status_code': None,
        'error': None,
        'upload_time': 0,
        'response_size': 0,
        'num_images': num_images
    }

    start = time.time()

    try:
        # Create FormData with images + metadata
        files = []
        data_fields = {
            'access_code': ACCESS_CODE,
            'semantic_context': 'modern office building',
            'category': 'interior'
        }

        # Add images as files
        for i in range(num_images):
            img_bytes, size_kb = create_test_image()
            files.append(('images', (f'test_{i}.jpg', img_bytes, 'image/jpeg')))

        # Send multipart/form-data request
        resp = requests.post(
            f"{BASE_URL}/api/upload",
            data=data_fields,
            files=files,
            timeout=120
        )

        result['status_code'] = resp.status_code
        result['upload_time'] = time.time() - start
        result['response_size'] = len(resp.content)

        if resp.status_code == 200:
            result['success'] = True
            json_data = resp.json()
            if not json_data.get('success'):
                result['error'] = json_data.get('error', 'Unknown error')
                result['success'] = False
        elif resp.status_code == 503:
            result['error'] = 'Server busy (503)'
        else:
            result['error'] = f"HTTP {resp.status_code}"
            try:
                result['error'] += f" - {resp.json().get('error', '')}"
            except:
                result['error'] += f" - {resp.text[:100]}"

    except requests.Timeout:
        result['error'] = 'Timeout (>120s)'
        result['upload_time'] = time.time() - start
    except Exception as e:
        result['error'] = f"{type(e).__name__}: {str(e)}"
        result['upload_time'] = time.time() - start

    return result


def test_upload_capacity(max_concurrent=50, images_per_batch=30):
    """Test: How many concurrent uploads can Render handle?"""
    print("=" * 80)
    print(f"UPLOAD CAPACITY TEST")
    print(f"Target: {BASE_URL}")
    print(f"Strategy: Increase concurrent uploads until server breaks")
    print(f"Images per upload: {images_per_batch}")
    print("=" * 80)

    # Test increasing concurrency levels
    concurrency_levels = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
    concurrency_levels = [c for c in concurrency_levels if c <= max_concurrent]

    all_results = []

    for num_concurrent in concurrency_levels:
        print(f"\n--- Testing {num_concurrent} concurrent uploads ---")

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [
                executor.submit(upload_batch, f"batch_{i}", images_per_batch)
                for i in range(num_concurrent)
            ]

            batch_results = []
            for future in as_completed(futures):
                result = future.result()
                batch_results.append(result)
                status = "✅" if result['success'] else "❌"
                print(f"  {status} {result['batch_id']}: {result['upload_time']:.1f}s - {result.get('error') or 'OK'}")

        total_time = time.time() - start_time

        # Analyze this level
        successful = sum(1 for r in batch_results if r['success'])
        failed = num_concurrent - successful

        print(f"\nLevel {num_concurrent} results:")
        print(f"  Success: {successful}/{num_concurrent} ({successful/num_concurrent*100:.0f}%)")
        print(f"  Failed: {failed}")
        print(f"  Total time: {total_time:.1f}s")

        all_results.extend(batch_results)

        # Check if we're hitting failures
        if failed > num_concurrent * 0.2:  # >20% failure rate
            print(f"\n⚠️  HIGH FAILURE RATE at {num_concurrent} concurrent")
            print(f"  Breaking point found!")
            break

        # Small delay between levels
        time.sleep(2)

    # Final summary
    print(f"\n{'='*80}")
    print(f"UPLOAD CAPACITY RESULTS")
    print(f"{'='*80}")

    # Group by status code
    status_counts = defaultdict(int)
    error_counts = defaultdict(int)

    for r in all_results:
        status_counts[r['status_code']] += 1
        if r['error']:
            error_counts[r['error']] += 1

    print(f"\nStatus codes:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")

    if error_counts:
        print(f"\nErrors:")
        for error, count in sorted(error_counts.items(), key=lambda x: -x[1]):
            print(f"  [{count}x] {error}")

    # Find max successful concurrency
    success_by_level = defaultdict(list)
    for r in all_results:
        # Extract concurrency level from batch_id
        level = len([x for x in all_results if x['batch_id'].split('_')[0] == r['batch_id'].split('_')[0]])
        success_by_level[level].append(r['success'])

    max_safe_concurrent = 0
    for level in sorted(success_by_level.keys()):
        successes = success_by_level[level]
        success_rate = sum(successes) / len(successes)
        if success_rate >= 0.9:  # 90%+ success rate
            max_safe_concurrent = level

    print(f"\n{'='*80}")
    print(f"RECOMMENDATIONS:")
    print(f"  Max safe concurrent uploads: ~{max_safe_concurrent}")
    print(f"  At {images_per_batch} images per upload")
    print(f"  Total capacity: ~{max_safe_concurrent * images_per_batch} images simultaneously")
    print("=" * 80)


def test_gemini_rate(target_rate=100):
    """Test: What's the max Gemini API rate we can sustain?"""
    print("=" * 80)
    print(f"GEMINI API RATE TEST")
    print(f"Target: {target_rate} requests/minute")
    print("=" * 80)

    import google.generativeai as genai
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    # Test image
    test_img = Image.new('RGB', (1920, 1080), color=(73, 109, 137))

    # Caption prompt (simplified)
    prompt = "Describe this image in 10 words or less."

    results = []
    start_time = time.time()
    request_times = []

    # Calculate delay between requests for target rate
    delay = 60.0 / target_rate  # seconds between requests

    print(f"\nSending requests at {target_rate}/min (1 req every {delay:.2f}s)...")
    print("Press Ctrl+C to stop\n")

    request_num = 0
    try:
        while request_num < 100:  # Max 100 requests
            req_start = time.time()

            try:
                response = model.generate_content([prompt, test_img])
                elapsed = time.time() - req_start
                request_times.append(elapsed)
                results.append({'success': True, 'elapsed': elapsed})
                print(f"  ✅ Request {request_num+1}: {elapsed:.2f}s")
            except Exception as e:
                elapsed = time.time() - req_start
                results.append({'success': False, 'error': str(e), 'elapsed': elapsed})
                print(f"  ❌ Request {request_num+1}: {str(e)[:50]}")

                # If rate limit, slow down
                if '429' in str(e) or 'quota' in str(e).lower():
                    print(f"  ⚠️  RATE LIMIT HIT at {target_rate} req/min")
                    break

            request_num += 1

            # Wait for next request
            time.sleep(delay)

    except KeyboardInterrupt:
        print("\n\nStopped by user")

    total_time = time.time() - start_time
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful

    print(f"\n{'='*80}")
    print(f"GEMINI RATE TEST RESULTS")
    print(f"{'='*80}")
    print(f"Requests sent: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Duration: {total_time:.1f}s")
    print(f"Actual rate: {len(results) / (total_time/60):.1f} req/min")

    if request_times:
        avg_time = sum(request_times) / len(request_times)
        print(f"\nResponse times:")
        print(f"  Average: {avg_time:.2f}s")
        print(f"  Min: {min(request_times):.2f}s")
        print(f"  Max: {max(request_times):.2f}s")

    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Hammer test for production server')
    parser.add_argument('--test', choices=['upload', 'gemini'], required=True, help='Which test to run')
    parser.add_argument('--concurrent', type=int, default=50, help='Max concurrent uploads to test')
    parser.add_argument('--images', type=int, default=30, help='Images per upload')
    parser.add_argument('--rate', type=int, default=100, help='Target Gemini API rate (req/min)')

    args = parser.parse_args()

    if args.test == 'upload':
        test_upload_capacity(args.concurrent, args.images)
    elif args.test == 'gemini':
        test_gemini_rate(args.rate)
