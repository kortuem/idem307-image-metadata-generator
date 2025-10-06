#!/usr/bin/env python3
"""
Quick test script to verify Gemini API key validity
"""

import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    print("❌ No API key found in .env file")
    sys.exit(1)

print(f"API Key found: {api_key[:20]}...{api_key[-4:]}")
print("Testing API key validity...")

try:
    # Configure API
    genai.configure(api_key=api_key)

    # Try to load a model
    model = genai.GenerativeModel('gemini-2.5-pro')

    # Test with simple text prompt (no image required)
    response = model.generate_content("Say 'test successful' if you can read this.")

    print(f"✅ API Key test passed!")
    print(f"Response: {response.text}")

except Exception as e:
    error_msg = str(e)
    print(f"❌ API Key test failed: {error_msg}")

    if "API key expired" in error_msg or "API_KEY_INVALID" in error_msg:
        print("\n⚠️  Your API key has expired or is invalid.")
        print("To fix this:")
        print("1. Go to https://aistudio.google.com/")
        print("2. Delete the old API key")
        print("3. Create a new API key")
        print("4. Update your .env file with the new key")
        print("5. Also update GEMINI_API_KEY in Render dashboard")
    elif "quota" in error_msg.lower():
        print("\n⚠️  You've hit your API quota limit.")
        print("Google Gemini free tier: 15 requests/minute, 1500 requests/day")

    sys.exit(1)
