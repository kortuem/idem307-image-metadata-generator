#!/usr/bin/env python3
"""
Gemini API Concurrency Stress Test

Tests concurrent API calls to find rate limits and throttling behavior.
Uses actual Gemini API to test real-world limits.

Usage:
    python3 tests/stress_test_gemini.py --concurrent 30 --duration 60
"""

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO

# Load environment variables
load_dotenv()


class GeminiStressTester:
    def __init__(self, api_key=None, use_vision=False):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.use_vision = use_vision

        # Metrics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.rate_limit_errors = 0
        self.other_errors = 0
        self.response_times = []
        self.errors_by_type = defaultdict(int)
        self.start_time = None

    def create_test_image(self, width=1920, height=1080):
        """Create a test image for vision API."""
        img = Image.new('RGB', (width, height), color=(73, 109, 137))
        return img

    def get_test_prompt(self, request_num):
        """Get test prompt - either text or vision with real caption prompt."""
        if self.use_vision:
            # Use actual caption generation prompt
            return """You are analyzing an image for AI training purposes.

CRITICAL OUTPUT FORMAT:
- Start with: "photo of ide_main_hall " (lowercase, space after trigger word)
- Then describe the scene
- No punctuation at end
- No introductory phrases

SEMANTIC CONTEXT: modern university building interior

Analyze this image and provide a training caption following the format exactly.
Example: "photo of ide_main_hall spacious atrium with natural lighting"

Your caption:"""
        else:
            return f"Test request #{request_num}: What is 2+2? Answer with just the number."

    async def make_request(self, request_num, delay=0):
        """Make a single API request and track metrics."""
        if delay > 0:
            await asyncio.sleep(delay)

        start = time.time()
        try:
            prompt = self.get_test_prompt(request_num)

            # If using vision, include an image
            if self.use_vision:
                test_image = self.create_test_image()
                response = await asyncio.to_thread(
                    self.model.generate_content, [prompt, test_image]
                )
            else:
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )

            # Success
            elapsed = time.time() - start
            self.response_times.append(elapsed)
            self.successful_requests += 1
            self.total_requests += 1

            return {
                'success': True,
                'request_num': request_num,
                'elapsed': elapsed,
                'response': response.text[:50]  # First 50 chars
            }

        except Exception as e:
            elapsed = time.time() - start
            error_type = type(e).__name__
            error_msg = str(e)

            self.failed_requests += 1
            self.total_requests += 1
            self.errors_by_type[error_type] += 1

            # Check if it's a rate limit error
            if 'quota' in error_msg.lower() or 'rate' in error_msg.lower() or '429' in error_msg:
                self.rate_limit_errors += 1
                error_category = 'RATE_LIMIT'
            else:
                self.other_errors += 1
                error_category = 'OTHER'

            return {
                'success': False,
                'request_num': request_num,
                'elapsed': elapsed,
                'error': error_msg[:100],
                'error_type': error_type,
                'category': error_category
            }

    async def test_concurrent_burst(self, num_concurrent=30):
        """Test: Send N concurrent requests simultaneously."""
        print(f"\n{'='*80}")
        print(f"TEST 1: Concurrent Burst")
        print(f"Sending {num_concurrent} requests simultaneously...")
        print(f"{'='*80}")

        self.start_time = time.time()

        # Create all tasks at once
        tasks = [
            self.make_request(i)
            for i in range(num_concurrent)
        ]

        # Execute all concurrently
        results = await asyncio.gather(*tasks)

        # Analyze results
        self._print_results(results, "Concurrent Burst")

        return results

    async def test_sustained_load(self, requests_per_second=10, duration_seconds=60):
        """Test: Sustained load over time."""
        print(f"\n{'='*80}")
        print(f"TEST 2: Sustained Load")
        print(f"Rate: {requests_per_second} req/s for {duration_seconds}s")
        print(f"{'='*80}")

        self.start_time = time.time()
        delay_between_requests = 1.0 / requests_per_second
        total_requests = requests_per_second * duration_seconds

        results = []
        for i in range(total_requests):
            task = self.make_request(i, delay=i * delay_between_requests)
            results.append(await task)

            # Print progress every 10 requests
            if (i + 1) % 10 == 0:
                elapsed = time.time() - self.start_time
                current_rate = (i + 1) / elapsed
                print(f"  Progress: {i+1}/{total_requests} requests, "
                      f"Rate: {current_rate:.1f} req/s, "
                      f"Success: {self.successful_requests}, "
                      f"Failed: {self.failed_requests}")

        self._print_results(results, "Sustained Load")

        return results

    async def test_ramp_up(self, start_concurrent=5, max_concurrent=50, step=5):
        """Test: Gradually increase concurrency to find breaking point."""
        print(f"\n{'='*80}")
        print(f"TEST 3: Ramp-Up Test")
        print(f"Starting at {start_concurrent}, increasing by {step} until {max_concurrent}")
        print(f"{'='*80}")

        all_results = []

        for num_concurrent in range(start_concurrent, max_concurrent + 1, step):
            print(f"\n--- Testing {num_concurrent} concurrent requests ---")

            tasks = [
                self.make_request(i)
                for i in range(num_concurrent)
            ]

            batch_results = await asyncio.gather(*tasks)
            all_results.extend(batch_results)

            # Check if we hit rate limits
            batch_failures = sum(1 for r in batch_results if not r['success'])
            batch_rate_limits = sum(1 for r in batch_results if not r['success'] and r.get('category') == 'RATE_LIMIT')

            print(f"  Success: {num_concurrent - batch_failures}/{num_concurrent}")
            if batch_rate_limits > 0:
                print(f"  ⚠️  Hit {batch_rate_limits} rate limit errors!")
                print(f"  Breaking point found at ~{num_concurrent} concurrent requests")
                break

            # Small delay between batches
            await asyncio.sleep(2)

        self._print_results(all_results, "Ramp-Up Test")

        return all_results

    def _print_results(self, results, test_name):
        """Print detailed results."""
        elapsed = time.time() - self.start_time

        print(f"\n{'='*80}")
        print(f"RESULTS: {test_name}")
        print(f"{'='*80}")
        print(f"Duration: {elapsed:.1f}s")
        print(f"Total requests: {self.total_requests}")
        print(f"Successful: {self.successful_requests} ({self.successful_requests/self.total_requests*100:.1f}%)")
        print(f"Failed: {self.failed_requests} ({self.failed_requests/self.total_requests*100:.1f}%)")

        if self.rate_limit_errors > 0:
            print(f"\n⚠️  RATE LIMIT ERRORS: {self.rate_limit_errors}")

        if self.other_errors > 0:
            print(f"\n⚠️  OTHER ERRORS: {self.other_errors}")

        if self.errors_by_type:
            print(f"\nErrors by type:")
            for error_type, count in self.errors_by_type.items():
                print(f"  {error_type}: {count}")

        if self.response_times:
            avg_response = sum(self.response_times) / len(self.response_times)
            min_response = min(self.response_times)
            max_response = max(self.response_times)
            print(f"\nResponse times:")
            print(f"  Average: {avg_response:.2f}s")
            print(f"  Min: {min_response:.2f}s")
            print(f"  Max: {max_response:.2f}s")

        actual_rate = self.total_requests / elapsed
        print(f"\nActual request rate: {actual_rate:.1f} req/s")

        # Recommendations
        print(f"\n{'='*80}")
        print(f"RECOMMENDATIONS:")
        if self.rate_limit_errors > 0:
            safe_concurrent = max(1, int(self.successful_requests / self.total_requests * 30))
            print(f"  ⚠️  Hit rate limits!")
            print(f"  ✅ Safe concurrent limit: ~{safe_concurrent} requests")
        else:
            print(f"  ✅ No rate limits detected")
            print(f"  ✅ Can handle {self.total_requests} requests in {elapsed:.1f}s")


async def main():
    parser = argparse.ArgumentParser(description='Gemini API concurrency stress test')
    parser.add_argument('--test', choices=['burst', 'sustained', 'ramp', 'all'], default='burst',
                        help='Which test to run')
    parser.add_argument('--concurrent', type=int, default=30, help='Concurrent requests for burst test')
    parser.add_argument('--rate', type=int, default=10, help='Requests per second for sustained test')
    parser.add_argument('--duration', type=int, default=60, help='Duration in seconds for sustained test')
    parser.add_argument('--vision', action='store_true', help='Use vision API with real images (costs more)')

    args = parser.parse_args()

    tester = GeminiStressTester(use_vision=args.vision)

    if args.vision:
        print("⚠️  Running with VISION API - will analyze images with real captions")
        print("   This uses more quota than text-only requests\n")
    else:
        print("Running with TEXT-ONLY API (simple prompts)")
        print("   Use --vision flag to test with image analysis\n")

    try:
        if args.test == 'burst' or args.test == 'all':
            await tester.test_concurrent_burst(args.concurrent)

        if args.test == 'sustained' or args.test == 'all':
            await tester.test_sustained_load(args.rate, args.duration)

        if args.test == 'ramp' or args.test == 'all':
            await tester.test_ramp_up(start_concurrent=5, max_concurrent=50, step=5)

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
