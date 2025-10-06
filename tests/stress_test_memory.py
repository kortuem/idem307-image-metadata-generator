#!/usr/bin/env python3
"""
Memory Exhaustion Stress Test

Simulates 30 concurrent students uploading images to find RAM limits.
Monitors memory usage and finds crash point.

Usage:
    python3 tests/stress_test_memory.py --sessions 30 --images 30
"""

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path
from io import BytesIO
from PIL import Image

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def create_fake_image(width=1920, height=1080, format='JPEG'):
    """Create a fake image in memory and return base64 encoded data."""
    # Create a solid color image
    img = Image.new('RGB', (width, height), color=(73, 109, 137))

    # Convert to bytes
    buffer = BytesIO()
    img.save(buffer, format=format, quality=85)
    buffer.seek(0)

    # Encode to base64
    image_bytes = buffer.getvalue()
    base64_data = base64.b64encode(image_bytes).decode('utf-8')

    return base64_data, len(image_bytes)


def simulate_session(session_id, num_images=30):
    """
    Simulate a student session with N images.
    Returns session data structure similar to production.
    """
    session_data = {
        'session_id': session_id,
        'semantic_context': f'Test session {session_id}',
        'category': 'interior',
        'images': {}
    }

    print(f"Creating session {session_id} with {num_images} images...")

    for i in range(num_images):
        filename = f'image_{i}.jpg'

        # Create fake image
        base64_data, size_bytes = create_fake_image()

        session_data['images'][filename] = {
            'data': base64_data,
            'caption': None,
            'edited': False,
            'size': size_bytes
        }

    # Calculate session size
    session_json = json.dumps(session_data)
    session_size_mb = len(session_json) / (1024 * 1024)

    return session_data, session_size_mb


def stress_test_memory(num_sessions=30, images_per_session=30):
    """
    Stress test: Create N concurrent sessions and monitor memory.

    Args:
        num_sessions: Number of concurrent student sessions
        images_per_session: Number of images per session
    """
    print("=" * 80)
    print(f"MEMORY STRESS TEST")
    print(f"Sessions: {num_sessions}, Images per session: {images_per_session}")
    print("=" * 80)

    sessions = {}
    total_session_size_mb = 0
    max_memory_limit_mb = 2048  # 2GB Render Standard instance

    print(f"\nSimulating {num_sessions} concurrent sessions...")
    print(f"Target system: 2GB RAM ({max_memory_limit_mb} MB)")

    try:
        for session_num in range(num_sessions):
            session_id = f"stress_test_{session_num:03d}"

            # Create session
            session_data, session_size = simulate_session(session_id, images_per_session)
            sessions[session_id] = session_data
            total_session_size_mb += session_size

            # Calculate percentage of 2GB limit
            memory_percent = (total_session_size_mb / max_memory_limit_mb) * 100

            print(f"\nSession {session_num + 1}/{num_sessions}:")
            print(f"  This session: {session_size:.1f} MB")
            print(f"  Total data: {total_session_size_mb:.1f} MB")
            print(f"  Memory usage: {memory_percent:.1f}% of {max_memory_limit_mb} MB")

            # Check if approaching danger zone (90% of 2GB)
            if total_session_size_mb > (max_memory_limit_mb * 0.9):
                print(f"\n⚠️  WARNING: Approaching memory limit!")
                print(f"  Reached {total_session_size_mb:.1f} MB / {max_memory_limit_mb} MB ({memory_percent:.1f}%)")
                print(f"  Stopped at {session_num + 1} sessions")
                break

            # Small delay to simulate real upload timing
            time.sleep(0.05)

    except MemoryError as e:
        print(f"\n💥 MEMORY ERROR at session {session_num + 1}")
        print(f"  Error: {e}")
    except Exception as e:
        print(f"\n💥 ERROR at session {session_num + 1}")
        print(f"  Error: {type(e).__name__}: {e}")
    finally:
        print(f"\n" + "=" * 80)
        print(f"FINAL RESULTS:")
        print(f"  Sessions created: {len(sessions)}")
        print(f"  Total session data: {total_session_size_mb:.1f} MB")
        print(f"  Memory limit: {max_memory_limit_mb} MB")
        print(f"  Memory used: {(total_session_size_mb/max_memory_limit_mb)*100:.1f}%")
        print("=" * 80)

        # Recommendations
        print(f"\nRECOMMENDATIONS:")
        if len(sessions) < num_sessions:
            safe_limit = int(len(sessions) * 0.8)  # 80% of max
            print(f"  ⚠️  Could not create all {num_sessions} sessions")
            print(f"  ⚠️  System hit limit at {len(sessions)} sessions ({total_session_size_mb:.1f} MB)")
            print(f"  ✅ Safe limit: ~{safe_limit} concurrent sessions")
            print(f"  💡 Consider: Lower MAX_CONCURRENT_SESSIONS to {safe_limit}")
        else:
            print(f"  ✅ Successfully created {num_sessions} sessions")
            print(f"  ✅ Memory usage: {total_session_size_mb:.1f} MB / {max_memory_limit_mb} MB")
            if total_session_size_mb > (max_memory_limit_mb * 0.8):
                print(f"  ⚠️  Warning: Using >{(total_session_size_mb/max_memory_limit_mb)*100:.0f}% of available RAM")
                print(f"  💡 Consider: Enable automatic session cleanup or reduce MAX_CONCURRENT_SESSIONS")
            else:
                print(f"  ✅ Healthy memory headroom: {max_memory_limit_mb - total_session_size_mb:.1f} MB remaining")


def cleanup_test_files():
    """Clean up any test session files."""
    session_folder = Path(__file__).parent.parent / 'tmp' / 'sessions'
    if session_folder.exists():
        for file in session_folder.glob('stress_test_*.json'):
            file.unlink()
            print(f"Deleted {file.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Memory stress test for concurrent sessions')
    parser.add_argument('--sessions', type=int, default=30, help='Number of concurrent sessions')
    parser.add_argument('--images', type=int, default=30, help='Images per session')
    parser.add_argument('--cleanup', action='store_true', help='Clean up test files')

    args = parser.parse_args()

    if args.cleanup:
        cleanup_test_files()
    else:
        stress_test_memory(args.sessions, args.images)
