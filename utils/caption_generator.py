"""
Gemini API Integration for Image Caption Generation
Handles vision model API calls with retry logic and rate limiting.
"""

import os
import time
import logging
from typing import Optional, Tuple
from PIL import Image
import google.generativeai as genai

logger = logging.getLogger(__name__)


class GeminiCaptionGenerator:
    """Generates image captions using Google Gemini vision API."""

    # Vision prompt template for structured caption generation
    VISION_PROMPT = """Analyze this interior space/person image and provide a structured description following this format:

For spaces: [room_type], [key_objects_visible], [lighting_description], [contextual_details]
For person: [pose/action], [clothing], [expression], [lighting], [background]

Be specific and objective. Focus on:
- Architectural/spatial elements (for spaces)
- Physical appearance and pose (for person)
- Lighting conditions (natural vs artificial, quality, direction)
- Atmosphere and context
- Visible objects and furniture
- Materials and textures where relevant

Example output for space: "lecture hall, tiered seating, projection screen, overhead fluorescent lighting, teaching space with rows of desks"

Example output for person: "standing, casual jeans and sweater, relaxed expression, soft window light from left, neutral grey background"

Do NOT include the "photo of [trigger_word]" prefix - that will be added automatically."""

    def __init__(self, api_key: Optional[str] = None, trigger_word: str = ""):
        """
        Initialize the caption generator.

        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            trigger_word: Trigger word to prepend to captions
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.trigger_word = trigger_word
        self.last_request_time = 0
        self.rate_limit_delay = 2.0  # Seconds between requests

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        # Configure Gemini API
        genai.configure(api_key=self.api_key)

        # Try newest model first, fallback chain to older stable versions
        model_preference = [
            'gemini-2.5-flash-latest',  # Latest Gemini 2.5 Flash
            'gemini-2.5-flash',          # Gemini 2.5 Flash (stable)
            'gemini-2.0-flash-exp',      # Gemini 2.0 Flash (experimental)
            'gemini-1.5-flash'           # Gemini 1.5 Flash (fallback)
        ]

        for model_name in model_preference:
            try:
                self.model = genai.GenerativeModel(model_name)
                logger.info(f"Using Gemini model: {model_name}")
                break
            except Exception as e:
                logger.warning(f"Failed to load {model_name}: {e}")
                if model_name == model_preference[-1]:
                    # Last fallback failed, raise error
                    raise ValueError(f"Could not initialize any Gemini model. Last error: {e}")

    def _rate_limit(self):
        """Enforce rate limiting between API requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _retry_with_backoff(self, func, max_retries: int = 3):
        """
        Retry a function with exponential backoff.

        Args:
            func: Function to retry
            max_retries: Maximum number of retry attempts

        Returns:
            Function result or raises last exception
        """
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed after {max_retries} attempts: {e}")
                    raise

                # Exponential backoff: 1s, 2s, 4s, 8s...
                backoff_time = 2 ** attempt
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {backoff_time}s...")
                time.sleep(backoff_time)

    def generate_caption(self, image_path: str) -> Tuple[bool, str, Optional[str]]:
        """
        Generate a caption for an image.

        Args:
            image_path: Path to the image file

        Returns:
            Tuple of (success: bool, caption: str, error: Optional[str])
            - success: True if caption generated successfully
            - caption: The formatted caption (with trigger word prefix)
            - error: Error message if failed, None if successful
        """
        try:
            # Rate limiting
            self._rate_limit()

            # Load image
            image = Image.open(image_path)

            # Generate caption with retry logic
            def api_call():
                response = self.model.generate_content([self.VISION_PROMPT, image])
                return response.text

            description = self._retry_with_backoff(api_call)

            # Clean and format caption
            description = description.strip()

            # Remove trailing punctuation
            if description and description[-1] in '.!?':
                description = description[:-1]

            # Format final caption
            if self.trigger_word:
                caption = f"photo of {self.trigger_word} {description}"
            else:
                caption = f"photo of {description}"

            logger.info(f"Generated caption for {os.path.basename(image_path)}")
            return (True, caption, None)

        except FileNotFoundError:
            error = f"Image file not found: {image_path}"
            logger.error(error)
            return (False, "", error)

        except Exception as e:
            error = f"Failed to generate caption: {str(e)}"
            logger.error(error)
            return (False, "", error)

    def set_trigger_word(self, trigger_word: str):
        """Update the trigger word for caption formatting."""
        self.trigger_word = trigger_word
        logger.info(f"Trigger word updated to: {trigger_word}")


# Convenience function for single-caption generation
def generate_single_caption(image_path: str, trigger_word: str, api_key: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
    """
    Generate a single caption (convenience function).

    Args:
        image_path: Path to image file
        trigger_word: Trigger word to prepend
        api_key: Optional API key (defaults to env var)

    Returns:
        Tuple of (success, caption, error)
    """
    generator = GeminiCaptionGenerator(api_key=api_key, trigger_word=trigger_word)
    return generator.generate_caption(image_path)
