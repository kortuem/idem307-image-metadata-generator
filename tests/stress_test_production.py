#!/usr/bin/env python3
"""
Production Infrastructure Stress Test

Tests the actual deployed Render.com app with real HTTP requests.
Simulates N concurrent students uploading images and generating captions.

Usage:
    python3 tests/stress_test_production.py --students 30 --images 10
"""

import argparse
import asyncio
import aiohttp
import base64
import json
import os
import sys
import time
from pathlib import Path
from io import BytesIO
from PIL import Image
from datetime import datetime

# Configuration
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


class ProductionStressTester:
    def __init__(self, base_url=BASE_URL, access_code=ACCESS_CODE):
        self.base_url = base_url
        self.access_code = access_code

        # Metrics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times = []
        self.errors = []
        self.student_results = []

    async def simulate_student(self, session, student_id, num_images=30):
        """Simulate a complete student workflow: init → upload → generate → export."""
        student_start = time.time()

        result = {
            'student_id': student_id,
            'success': False,
            'phases': {},
            'total_time': 0,
            'error': None
        }

        try:
            # Phase 1: Initialize session
            phase_start = time.time()
            async with session.post(
                f"{self.base_url}/api/init",
                json={'access_code': self.access_code}
            ) as resp:
                if resp.status != 200:
                    result['error'] = f"Init failed: {resp.status}"
                    return result

                data = await resp.json()
                session_id = data.get('session_id')

            result['phases']['init'] = time.time() - phase_start

            # Phase 2: Upload images
            phase_start = time.time()
            images_data = []
            for i in range(num_images):
                images_data.append({
                    'name': f'test_image_{i}.jpg',
                    'data': create_fake_image()
                })

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
                    result['error'] = f"Upload failed: {resp.status}"
                    return result

            result['phases']['upload'] = time.time() - phase_start

            # Phase 3: Generate captions
            phase_start = time.time()
            async with session.post(
                f"{self.base_url}/api/generate",
                json={'session_id': session_id}
            ) as resp:
                if resp.status != 200:
                    result['error'] = f"Generate failed: {resp.status}"
                    return result

            result['phases']['generate'] = time.time() - phase_start

            # Phase 4: Export (cleanup)
            phase_start = time.time()
            async with session.post(
                f"{self.base_url}/api/export",
                json={
                    'session_id': session_id,
                    'trigger_word': 'test_trigger'
                }
            ) as resp:
                if resp.status != 200:
                    result['error'] = f"Export failed: {resp.status}"
                    return result

            result['phases']['export'] = time.time() - phase_start

            # Success!
            result['success'] = True
            result['total_time'] = time.time() - student_start

        except Exception as e:
            result['error'] = str(e)

        return result

    async def run_concurrent_students(self, num_students=30, images_per_student=30):
        """Simulate N students working concurrently."""
        print("=" * 80)
        print(f"PRODUCTION STRESS TEST")
        print(f"Target: {self.base_url}")
        print(f"Students: {num_students}, Images per student: {images_per_student}")
        print("=" * 80)

        start_time = time.time()

        # Create aiohttp session with timeout
        timeout = aiohttp.ClientTimeout(total=600)  # 10 minute timeout
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Create tasks for all students
            tasks = [
                self.simulate_student(session, f"student_{i:03d}", images_per_student)
                for i in range(num_students)
            ]

            # Run all concurrently
            print(f"\nStarting {num_students} concurrent student simulations...")
            results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start_time

        # Analyze results
        self._print_results(results, total_time, num_students, images_per_student)

        return results

    def _print_results(self, results, total_time, num_students, images_per_student):
        """Print detailed results."""
        successful = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
        failed = num_students - successful

        print(f"\n{'='*80}")
        print(f"RESULTS")
        print(f"{'='*80}")
        print(f"Total duration: {total_time:.1f}s")
        print(f"Successful students: {successful}/{num_students} ({successful/num_students*100:.1f}%)")
        print(f"Failed students: {failed}/{num_students}")

        # Phase timing analysis
        if successful > 0:
            phase_times = {'init': [], 'upload': [], 'generate': [], 'export': []}
            for r in results:
                if isinstance(r, dict) and r.get('success'):
                    for phase, time_val in r['phases'].items():
                        phase_times[phase].append(time_val)

            print(f"\nPhase timing (average):")
            for phase, times in phase_times.items():
                if times:
                    avg = sum(times) / len(times)
                    print(f"  {phase.capitalize()}: {avg:.2f}s (min: {min(times):.2f}s, max: {max(times):.2f}s)")

            # Total workflow time
            total_workflow_times = [r['total_time'] for r in results if isinstance(r, dict) and r.get('success')]
            if total_workflow_times:
                avg_workflow = sum(total_workflow_times) / len(total_workflow_times)
                print(f"\nComplete workflow time per student:")
                print(f"  Average: {avg_workflow:.1f}s")
                print(f"  Min: {min(total_workflow_times):.1f}s")
                print(f"  Max: {max(total_workflow_times):.1f}s")

        # Errors
        errors = [r.get('error') for r in results if isinstance(r, dict) and r.get('error')]
        if errors:
            print(f"\n⚠️  ERRORS:")
            error_counts = {}
            for error in errors:
                error_counts[error] = error_counts.get(error, 0) + 1
            for error, count in error_counts.items():
                print(f"  [{count}x] {error}")

        # Recommendations
        print(f"\n{'='*80}")
        print(f"RECOMMENDATIONS:")
        if successful == num_students:
            print(f"  ✅ All {num_students} students completed successfully!")
            print(f"  ✅ Production infrastructure can handle workshop load")
            if avg_workflow > 120:
                print(f"  ⚠️  Average workflow time is {avg_workflow:.0f}s - consider slow mode warning")
        elif successful >= num_students * 0.8:
            print(f"  ⚠️  {failed} students failed ({failed/num_students*100:.0f}%)")
            print(f"  💡 Review errors above - may need rate limiting or retries")
        else:
            print(f"  ❌ High failure rate: {failed}/{num_students} students failed")
            print(f"  ❌ System NOT ready for workshop")
            print(f"  💡 Check Render logs and fix infrastructure issues")


async def main():
    parser = argparse.ArgumentParser(description='Production infrastructure stress test')
    parser.add_argument('--students', type=int, default=30, help='Number of concurrent students')
    parser.add_argument('--images', type=int, default=30, help='Images per student')
    parser.add_argument('--url', type=str, default=BASE_URL, help='Base URL to test')

    args = parser.parse_args()

    # Validate access code
    if not ACCESS_CODE:
        print("ERROR: SECRET_ACCESS_CODE environment variable not set")
        print("Set it with: export SECRET_ACCESS_CODE='your_code'")
        sys.exit(1)

    tester = ProductionStressTester(base_url=args.url, access_code=ACCESS_CODE)

    try:
        await tester.run_concurrent_students(args.students, args.images)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
