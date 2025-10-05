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

    # Interior category prompt template for LoRA training
    INTERIOR_PROMPT = """You are annotating images for LoRA fine-tuning of a Flux image model.
Output exactly ONE sentence, maximum 50 words, grounded only in visible evidence.

Your sentence MUST begin with: "{SEMANTIC_CONTEXT}"

After "{SEMANTIC_CONTEXT}", add a natural connector word (with, featuring, showing) and describe in order:
1. Key architectural elements and spatial layout
2. Furniture, objects, and their arrangement
3. Materials, finishes, and colors
4. Lighting conditions and quality
5. Overall atmosphere or character

Aim for 40-50 words to provide rich, specific detail.

Example:
"{SEMANTIC_CONTEXT} with high vaulted ceilings and exposed beams, rows of modern workstations with ergonomic chairs arranged in open layout, polished concrete floors, floor-to-ceiling windows providing abundant natural light, creating bright collaborative atmosphere"

Critical rules:
- Start EXACTLY with: {SEMANTIC_CONTEXT}
- No "photo of" or "image of"
- Maximum 50 words, aim for 40-50
- Single sentence only
- Output only the sentence"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the caption generator.

        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
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

    def _validate_caption(self, caption: str, semantic_context: str) -> Tuple[bool, str, list]:
        """
        Validate and clean generated caption.

        Args:
            caption: Generated caption from AI
            semantic_context: Required context that must be in caption

        Returns:
            Tuple of (is_valid: bool, cleaned_caption: str, issues: list)
        """
        issues = []

        # 1. Strip whitespace
        caption = caption.strip()

        # 2. Remove banned prefixes
        banned_prefixes = ['photo of', 'image of', 'picture of', 'a photo', 'an image']
        for prefix in banned_prefixes:
            if caption.lower().startswith(prefix):
                caption = caption[len(prefix):].strip()
                issues.append(f"Removed '{prefix}' prefix")

        # 3. Check starts with context (CRITICAL)
        if not caption.startswith(semantic_context):
            issues.append(f"CRITICAL: Doesn't start with '{semantic_context}'")
            return (False, caption, issues)

        # 4. Check word count (CRITICAL)
        word_count = len(caption.split())
        if word_count > 50:
            issues.append(f"CRITICAL: {word_count} words (max 50)")
            return (False, caption, issues)

        # 5. Check for multiple sentences
        if '. ' in caption or '! ' in caption or '? ' in caption:
            caption = caption.split('. ')[0]
            issues.append("Multiple sentences - kept first")

        # 6. Remove trailing punctuation
        original = caption
        caption = caption.rstrip('.!?,;:')
        if caption != original:
            issues.append("Removed trailing punctuation")

        # Success - no critical issues
        return (True, caption, issues)

    def generate_caption(self, image_path: str, semantic_context: str) -> Tuple[bool, str, Optional[str]]:
        """
        Generate a caption for an image.

        Args:
            image_path: Path to the image file
            semantic_context: User-provided context (e.g., "TU Delft drawing studio")

        Returns:
            Tuple of (success: bool, caption: str, error: Optional[str])
            - success: True if caption generated successfully
            - caption: The formatted caption starting with semantic context
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

            # Inject semantic context into prompt
            prompt = self.INTERIOR_PROMPT.replace("{SEMANTIC_CONTEXT}", semantic_context)

            # Generate caption with retry logic
            def api_call():
                response = self.model.generate_content([prompt, image])
                return response.text

            caption = self._retry_with_backoff(api_call)

            # Validate and clean caption
            is_valid, cleaned_caption, issues = self._validate_caption(caption, semantic_context)

            if not is_valid:
                # Critical issue - try to regenerate once
                logger.warning(f"Caption validation failed: {issues}. Attempting regeneration...")

                # Determine regeneration prompt based on issue
                if "Doesn't start with" in str(issues):
                    regen_prompt = f"""Your previous caption didn't start with "{semantic_context}" as required.

Previous caption: {caption}

Generate a NEW caption that begins EXACTLY with: "{semantic_context}"
Then add connector word and description. Maximum 50 words, aim for 40-50. Output only the sentence."""

                elif "words (max 50)" in str(issues):
                    word_count = len(caption.split())
                    regen_prompt = f"""Your previous caption was {word_count} words, but maximum is 50.

Previous caption: {caption}

Condense to maximum 50 words. Keep key facts. Start with "{semantic_context}". Aim for 40-50 words. Output only the sentence."""

                else:
                    regen_prompt = f"""Your previous caption had issues: {', '.join(issues)}

Previous caption: {caption}

Generate a NEW caption starting with "{semantic_context}", maximum 50 words. Output only the sentence."""

                # Try regeneration
                try:
                    def regen_call():
                        response = self.model.generate_content([regen_prompt, image])
                        return response.text

                    regenerated_caption = self._retry_with_backoff(regen_call)

                    # Validate regenerated caption
                    is_valid_regen, cleaned_regen, issues_regen = self._validate_caption(regenerated_caption, semantic_context)

                    if is_valid_regen:
                        logger.info(f"Regeneration successful: {cleaned_regen[:60]}...")
                        return (True, cleaned_regen, None)
                    else:
                        logger.error(f"Regeneration still failed: {issues_regen}")
                        return (False, cleaned_regen, f"Regeneration failed: {', '.join(issues_regen)}")

                except Exception as e:
                    logger.error(f"Regeneration error: {e}")
                    return (False, cleaned_caption, f"Validation failed and regeneration error: {str(e)}")

            logger.info(f"Generated caption for {os.path.basename(image_path)}: {cleaned_caption[:60]}...")
            if issues:
                logger.info(f"Auto-fixes applied: {', '.join(issues)}")

            return (True, cleaned_caption, None)

        except FileNotFoundError:
            error = f"Image file not found: {image_path}"
            logger.error(error)
            return (False, "", error)

        except Exception as e:
            error = f"Failed to generate caption: {str(e)}"
            logger.error(error)
            return (False, "", error)


# Convenience function for single-caption generation
def generate_single_caption(image_path: str, semantic_context: str, api_key: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
    """
    Generate a single caption (convenience function).

    Args:
        image_path: Path to image file
        semantic_context: Context description (e.g., "TU Delft drawing studio")
        api_key: Optional API key (defaults to env var)

    Returns:
        Tuple of (success, caption, error)
    """
    generator = GeminiCaptionGenerator(api_key=api_key)
    return generator.generate_caption(image_path, semantic_context)
