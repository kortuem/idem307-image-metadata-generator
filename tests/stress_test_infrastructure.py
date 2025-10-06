#!/usr/bin/env python3
"""
Infrastructure Stress Test (No API Calls)

Tests Render.com infrastructure without burning API quota.
Tests: session handling, memory, upload processing, server capacity.
Skips: actual caption generation (to save API costs).

Usage:
    python3 tests/stress_test_infrastructure.py --students 30 --images 30
"""

import argparse
import asyncio
import aiohttp
import base64
import os
import sys
import time
from io import BytesIO
from PIL import Image

BASE_URL = "https://idem307-image-metadata-generator.onrender.com"
ACCESS_CODE = os.getenv('SECRET_ACCESS_CODE', '')


def create_fake_image(width=1920, height=1080):
    """Create a fake image and return base64 data URL."""
    img = Image.new('RGB', (width, height), color=(73, 109, 137))
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    img_bytes = buffer.getvalue()
    b64_string = base64.b64encode(img_bytes).decode('utf-8')
    return f"data:image/jpeg;base64,{b64_string}"


class InfrastructureTester:
    def __init__(self, base_url=BASE_URL, access_code=ACCESS_CODE):
        self.base_url = base_url
        self.access_code = access_code

    async def test_student_workflow(self, session, student_id, num_images=30):
        """Test student workflow WITHOUT caption generation (saves API quota)."""
        result = {
            'student_id': student_id,
            'success': False,
            'phases': {},
            'total_time': 0,
            'error': None
        }

        start_time = time.time()

        try:
            # Phase 1: Initialize session
            phase_start = time.time()
            async with session.post(
                f"{self.base_url}/api/init",
                json={'access_code': self.access_code}
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    result['error'] = f"Init failed ({resp.status}): {text[:100]}"
                    return result
                data = await resp.json()
                session_id = data.get('session_id')
            result['phases']['init'] = time.time() - phase_start

            # Phase 2: Upload images
            phase_start = time.time()
            images_data = [
                {
                    'name': f'test_{i}.jpg',
                    'data': create_fake_image()
                }
                for i in range(num_images)
            ]

            async with session.post(
                f"{self.base_url}/api/upload",
                json={
                    'session_id': session_id,
                    'images': images_data,
                    'category': 'interior',
                    'semantic_context': 'modern office building'
                }
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    result['error'] = f"Upload failed ({resp.status}): {text[:100]}"
                    return result
            result['phases']['upload'] = time.time() - phase_start

            # Phase 3: SKIP caption generation (save API quota)
            # In real workflow, this would call /api/generate
            # For infrastructure test, we just test session cleanup

            # Phase 4: Delete session (cleanup test)
            phase_start = time.time()
            async with session.post(
                f"{self.base_url}/api/delete_session",
                json={'session_id': session_id}
            ) as resp:
                # May be 200 or 404 (if endpoint doesn't exist yet)
                pass
            result['phases']['cleanup'] = time.time() - phase_start

            result['success'] = True
            result['total_time'] = time.time() - start_time

        except Exception as e:
            result['error'] = str(e)
            result['total_time'] = time.time() - start_time

        return result

    async def run_test(self, num_students=30, images_per_student=30):
        """Run infrastructure stress test."""
        print("=" * 80)
        print(f"INFRASTRUCTURE STRESS TEST (No API calls)")
        print(f"Target: {self.base_url}")
        print(f"Students: {num_students}, Images: {images_per_student}")
        print("=" * 80)
        print("\nThis test checks:")
        print("  ✓ Session initialization")
        print("  ✓ Image upload handling")
        print("  ✓ Memory capacity")
        print("  ✓ Server concurrency")
        print("  ✗ Caption generation (SKIPPED - saves API quota)")
        print()

        start_time = time.time()

        timeout = aiohttp.ClientTimeout(total=300)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            tasks = [
                self.test_student_workflow(session, f"student_{i:03d}", images_per_student)
                for i in range(num_students)
            ]

            print(f"Starting {num_students} concurrent workflows...")
            results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start_time

        # Analyze results
        successful = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
        failed = num_students - successful

        print(f"\n{'='*80}")
        print(f"RESULTS")
        print(f"{'='*80}")
        print(f"Duration: {total_time:.1f}s")
        print(f"Successful: {successful}/{num_students} ({successful/num_students*100:.1f}%)")
        print(f"Failed: {failed}/{num_students}")

        # Phase timing
        if successful > 0:
            phase_times = {'init': [], 'upload': [], 'cleanup': []}
            for r in results:
                if isinstance(r, dict) and r.get('success'):
                    for phase in phase_times.keys():
                        if phase in r['phases']:
                            phase_times[phase].append(r['phases'][phase])

            print(f"\nPhase timing:")
            for phase, times in phase_times.items():
                if times:
                    avg = sum(times) / len(times)
                    print(f"  {phase.capitalize()}: avg={avg:.2f}s, min={min(times):.2f}s, max={max(times):.2f}s")

        # Errors
        errors = [r.get('error') for r in results if isinstance(r, dict) and r.get('error')]
        if errors:
            print(f"\n⚠️  ERRORS ({len(errors)} total):")
            # Group by error type
            error_counts = {}
            for error in errors:
                error_counts[error] = error_counts.get(error, 0) + 1
            for error, count in sorted(error_counts.items(), key=lambda x: -x[1]):
                print(f"  [{count}x] {error}")

        # Recommendations
        print(f"\n{'='*80}")
        print(f"INFRASTRUCTURE ASSESSMENT:")
        if successful == num_students:
            print(f"  ✅ Server handled {num_students} concurrent sessions")
            print(f"  ✅ Memory capacity is adequate")
            print(f"  ✅ Upload processing works correctly")
            print(f"\n  Next step: Run FULL test with caption generation:")
            print(f"    python3 tests/stress_test_production.py --students 5 --images 5")
            print(f"    (Start small to avoid burning API quota)")
        elif successful >= num_students * 0.8:
            print(f"  ⚠️  {failed}/{num_students} students failed")
            print(f"  💡 Check errors above - may be transient or rate limiting")
        else:
            print(f"  ❌ High failure rate: {failed}/{num_students}")
            print(f"  ❌ Infrastructure NOT ready")
            print(f"  💡 Check Render dashboard for:")
            print(f"     - Memory errors")
            print(f"     - 503 Service Unavailable")
            print(f"     - Request timeouts")

        print("=" * 80)


async def main():
    parser = argparse.ArgumentParser(description='Infrastructure stress test (no API calls)')
    parser.add_argument('--students', type=int, default=30, help='Number of concurrent students')
    parser.add_argument('--images', type=int, default=30, help='Images per student')
    parser.add_argument('--url', type=str, default=BASE_URL, help='Base URL')
    args = parser.parse_args()

    if not ACCESS_CODE:
        print("ERROR: SECRET_ACCESS_CODE not set")
        print("Run: export SECRET_ACCESS_CODE='your_code'")
        sys.exit(1)

    tester = InfrastructureTester(args.url, ACCESS_CODE)
    await tester.run_test(args.students, args.images)


if __name__ == "__main__":
    asyncio.run(main())
