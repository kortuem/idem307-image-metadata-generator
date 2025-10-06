#!/usr/bin/env python3
"""
Live Production Stress Test

Tests actual Render.com deployment with concurrent students.
Uses requests library (synchronous) with threading.

Usage:
    python3 tests/stress_test_live.py --students 5 --images 10
"""

import argparse
import base64
import json
import os
import sys
import time
import threading
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
except ImportError:
    print("ERROR: requests library not found")
    print("Install with: pip3 install --break-system-packages requests")
    sys.exit(1)

BASE_URL = "https://idem307-image-metadata-generator.onrender.com"
ACCESS_CODE = os.getenv('SECRET_ACCESS_CODE', 'kind_gemini_key')


def create_fake_image(width=1920, height=1080):
    """Create test image as base64 data URL."""
    img = Image.new('RGB', (width, height), color=(73, 109, 137))
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    img_bytes = buffer.getvalue()
    b64_string = base64.b64encode(img_bytes).decode('utf-8')
    return f"data:image/jpeg;base64,{b64_string}"


def simulate_student(student_id, num_images, base_url=BASE_URL, access_code=ACCESS_CODE):
    """Simulate complete student workflow."""
    result = {
        'student_id': student_id,
        'success': False,
        'phases': {},
        'total_time': 0,
        'error': None
    }

    start_time = time.time()

    try:
        # Phase 1: Init session
        phase_start = time.time()
        resp = requests.post(
            f"{base_url}/api/init",
            json={'access_code': access_code},
            timeout=30
        )
        if resp.status_code != 200:
            result['error'] = f"Init failed: {resp.status_code} - {resp.text[:100]}"
            return result
        session_id = resp.json().get('session_id')
        result['phases']['init'] = time.time() - phase_start

        # Phase 2: Upload images
        phase_start = time.time()
        images_data = [
            {'name': f'img_{i}.jpg', 'data': create_fake_image()}
            for i in range(num_images)
        ]
        resp = requests.post(
            f"{base_url}/api/upload",
            json={
                'session_id': session_id,
                'images': images_data,
                'category': 'interior',
                'semantic_context': 'modern office building'
            },
            timeout=60
        )
        if resp.status_code != 200:
            result['error'] = f"Upload failed: {resp.status_code} - {resp.text[:100]}"
            return result
        result['phases']['upload'] = time.time() - phase_start

        # Phase 3: Generate captions (THIS USES REAL API!)
        phase_start = time.time()
        resp = requests.post(
            f"{base_url}/api/generate",
            json={'session_id': session_id},
            timeout=600  # 10 min timeout
        )
        if resp.status_code != 200:
            result['error'] = f"Generate failed: {resp.status_code} - {resp.text[:100]}"
            return result
        result['phases']['generate'] = time.time() - phase_start

        # Phase 4: Export (cleanup)
        phase_start = time.time()
        resp = requests.post(
            f"{base_url}/api/export",
            json={'session_id': session_id, 'trigger_word': 'test_trigger'},
            timeout=30
        )
        if resp.status_code != 200:
            result['error'] = f"Export failed: {resp.status_code}"
            # Not critical, continue
        result['phases']['export'] = time.time() - phase_start

        result['success'] = True
        result['total_time'] = time.time() - start_time

    except requests.Timeout as e:
        result['error'] = f"Timeout: {str(e)}"
    except Exception as e:
        result['error'] = f"{type(e).__name__}: {str(e)}"

    finally:
        result['total_time'] = time.time() - start_time

    return result


def run_stress_test(num_students=5, num_images=10):
    """Run production stress test."""
    print("=" * 80)
    print(f"LIVE PRODUCTION STRESS TEST")
    print(f"Target: {BASE_URL}")
    print(f"Students: {num_students}, Images: {num_images}")
    print("=" * 80)
    print("\n⚠️  WARNING: This will use REAL Gemini API quota!")
    print(f"   Estimated API calls: {num_students * num_images}")
    print()

    start_time = time.time()

    # Use ThreadPoolExecutor for concurrent requests
    with ThreadPoolExecutor(max_workers=num_students) as executor:
        futures = {
            executor.submit(simulate_student, f"student_{i:03d}", num_images): i
            for i in range(num_students)
        }

        results = []
        for future in as_completed(futures):
            student_num = futures[future]
            try:
                result = future.result()
                results.append(result)
                status = "✅" if result['success'] else "❌"
                print(f"  {status} Student {student_num}: {result['total_time']:.1f}s - {result.get('error') or 'Success'}")
            except Exception as e:
                print(f"  ❌ Student {student_num}: Exception - {e}")
                results.append({'student_id': f'student_{student_num:03d}', 'success': False, 'error': str(e)})

    total_time = time.time() - start_time

    # Analyze results
    print(f"\n{'='*80}")
    print(f"RESULTS")
    print(f"{'='*80}")

    successful = sum(1 for r in results if r.get('success'))
    failed = num_students - successful

    print(f"Duration: {total_time:.1f}s")
    print(f"Successful: {successful}/{num_students} ({successful/num_students*100:.1f}%)")
    print(f"Failed: {failed}")

    # Phase analysis
    if successful > 0:
        phases = ['init', 'upload', 'generate', 'export']
        phase_times = {p: [] for p in phases}

        for r in results:
            if r.get('success'):
                for phase in phases:
                    if phase in r.get('phases', {}):
                        phase_times[phase].append(r['phases'][phase])

        print(f"\nPhase timing (successful students only):")
        for phase in phases:
            if phase_times[phase]:
                times = phase_times[phase]
                print(f"  {phase.capitalize():10s}: avg={sum(times)/len(times):.1f}s, min={min(times):.1f}s, max={max(times):.1f}s")

    # Errors
    errors = [r.get('error') for r in results if r.get('error')]
    if errors:
        print(f"\n❌ ERRORS ({len(errors)} total):")
        error_counts = {}
        for err in errors:
            error_counts[err] = error_counts.get(err, 0) + 1
        for err, count in sorted(error_counts.items(), key=lambda x: -x[1]):
            print(f"  [{count}x] {err}")

    # Recommendations
    print(f"\n{'='*80}")
    print(f"ASSESSMENT:")
    if successful == num_students:
        print(f"  ✅ All students completed successfully!")
        print(f"  ✅ Production ready for workshop")
    elif successful >= num_students * 0.8:
        print(f"  ⚠️  Some failures ({failed}/{num_students})")
        print(f"  💡 Review errors - may need adjustments")
    else:
        print(f"  ❌ High failure rate ({failed}/{num_students})")
        print(f"  ❌ NOT ready for workshop")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Live production stress test')
    parser.add_argument('--students', type=int, default=5, help='Concurrent students')
    parser.add_argument('--images', type=int, default=10, help='Images per student')
    args = parser.parse_args()

    run_stress_test(args.students, args.images)
