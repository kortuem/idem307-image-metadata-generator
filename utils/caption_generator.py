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

    # Vision prompt template optimized for LoRA training dataset generation
    # Based on best practices for text-to-image model fine-tuning metadata
    VISION_PROMPT = """You are an expert image annotator for a leading text-to-image AI model. Your task is to analyze the provided image and generate a single, highly descriptive prompt that can be used to faithfully reproduce this image.

The prompt must be a single, continuous sentence and should be structured using the following mandatory elements:

**Subject**: The main object(s), space, or person(s) in the image.

**Environment/Location**: The setting (e.g., in a modern office, a minimalist lecture hall, an industrial workspace).

**Style & Composition**: Specify photographic style (e.g., photorealistic, architectural photography, wide-angle shot, 50mm lens, natural light, golden hour, high-key lighting).

**Key Details**: Materials, colors, textures, and critical elements (e.g., polished concrete floor, exposed brick walls, ergonomic mesh chairs, floor-to-ceiling windows, soft diffused lighting from skylights).

**Spatial Relationships**: How elements relate to each other (e.g., rows of desks facing a projection screen, spiral staircase connecting two floors, open-plan layout with glass partitions).

**Mood/Atmosphere**: The overall feeling (e.g., minimalist and serene, busy and collaborative, moody and intimate, bright and energetic).

**For Person Images, Focus On**:
- Pose/action, clothing style, expression
- Lighting quality and direction
- Background environment and depth
- Physical appearance and context

**Example outputs**:

Space: "A spacious industrial-style design studio with exposed concrete ceiling beams and polished concrete floors, featuring rows of black drafting tables with adjustable LED task lamps, floor-to-ceiling windows providing soft natural daylight, surrounded by white acoustic wall panels and cork pinboards displaying sketches, creating a minimalist yet creative atmosphere with high ceilings and open-plan layout"

Person: "A confident professional standing in relaxed pose wearing casual dark jeans and charcoal crew-neck sweater, calm and approachable expression, illuminated by soft window light from camera left creating subtle shadow definition, against a neutral medium-grey seamless backdrop with shallow depth of field"

**Critical Instructions**:
- Output ONLY the complete, single-sentence descriptive prompt
- Do NOT include any introductory text, explanations, or the word "photo" or "image"
- Do NOT include the trigger word prefix - that will be added automatically
- Be extremely specific about materials, lighting, spatial layout, and atmosphere
- Use professional photographic and architectural terminology where appropriate"""

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

        # Model names for google-generativeai 0.8.x (latest API)
        # Prioritize Gemini 2.5 Pro for superior interior design analysis:
        # - Style classification (architectural details, design aesthetics)
        # - Contextual reasoning (spatial relationships, lighting interactions)
        # - Material and texture identification
        # - Atmospheric/mood descriptions
        model_preference = [
            'gemini-2.5-pro',            # Best: Deep reasoning, nuanced analysis, style classification
            'gemini-2.5-flash',          # Good: Fast, accurate, less detailed than Pro
            'gemini-2.0-flash-exp',      # Fallback: Experimental 2.0
            'gemini-1.5-pro',            # Fallback: Stable 1.5 Pro
            'gemini-1.5-flash',          # Fallback: Stable 1.5 Flash
            'gemini-pro-vision'          # Last resort: older vision model
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

            # Load image and convert MPO to JPEG for Gemini API compatibility
            image = Image.open(image_path)

            # If image is MPO format, convert to JPEG
            if image.format == 'MPO':
                # Convert to RGB (in case it's in a different mode)
                if image.mode != 'RGB':
                    image = image.convert('RGB')

                # Save as JPEG to a temporary path
                temp_path = image_path.rsplit('.', 1)[0] + '_temp.jpg'
                image.save(temp_path, 'JPEG', quality=95)

                # Update image_path to the temporary JPEG
                image_path = temp_path
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
