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

    # Category-specific prompt templates for LoRA training

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

    PERSON_PROMPT = """You are annotating images for LoRA fine-tuning of a Flux image model.
Output exactly ONE sentence, maximum 50 words, grounded only in visible evidence.

Your sentence MUST begin with: "{SEMANTIC_CONTEXT}"

After "{SEMANTIC_CONTEXT}", add a natural connector word (wearing, with, in, showing) and describe in order:
1. Physical appearance and distinguishing features
2. Clothing, accessories, and style
3. Pose, gesture, or activity
4. Facial expression or mood
5. Background or setting context

Aim for 40-50 words to provide rich, specific detail.

Example:
"{SEMANTIC_CONTEXT} wearing black turtleneck and blue jeans, standing with arms crossed in confident pose, slight smile and direct gaze, against minimalist white background with soft studio lighting creating professional portrait atmosphere"

Critical rules:
- Start EXACTLY with: {SEMANTIC_CONTEXT}
- No "photo of" or "image of"
- Maximum 50 words, aim for 40-50
- Single sentence only
- Output only the sentence"""

    OBJECT_PROMPT = """You are annotating images for LoRA fine-tuning of a Flux image model.
Output exactly ONE sentence, maximum 50 words, grounded only in visible evidence.

Your sentence MUST begin with: "{SEMANTIC_CONTEXT}"

After "{SEMANTIC_CONTEXT}", add a natural connector word (with, featuring, made of, showing) and describe in order:
1. Overall shape and form
2. Materials, texture, and finish
3. Colors and visual details
4. Function or design purpose
5. Context or background setting

Aim for 40-50 words to provide rich, specific detail.

Example:
"{SEMANTIC_CONTEXT} with sleek minimalist design and rounded edges, brushed aluminum body with matte black accents, compact rectangular form, precision-engineered controls, photographed on white seamless background with soft diffused lighting highlighting premium build quality"

Critical rules:
- Start EXACTLY with: {SEMANTIC_CONTEXT}
- No "photo of" or "image of"
- Maximum 50 words, aim for 40-50
- Single sentence only
- Output only the sentence"""

    SCENE_PROMPT = """You are annotating images for LoRA fine-tuning of a Flux image model.
Output exactly ONE sentence, maximum 50 words, grounded only in visible evidence.

Your sentence MUST begin with: "{SEMANTIC_CONTEXT}"

After "{SEMANTIC_CONTEXT}", add a natural connector word (with, featuring, showing, under) and describe in order:
1. Main environmental elements and composition
2. Weather conditions or time of day
3. Natural or artificial lighting quality
4. Colors, atmosphere, and mood
5. Notable visual details or focal points

Aim for 40-50 words to provide rich, specific detail.

Example:
"{SEMANTIC_CONTEXT} with rolling green hills extending to distant mountains under partly cloudy sky, golden hour sunlight casting long shadows across pastoral landscape, scattered trees and winding dirt path, warm saturated colors creating serene peaceful atmosphere"

Critical rules:
- Start EXACTLY with: {SEMANTIC_CONTEXT}
- No "photo of" or "image of"
- Maximum 50 words, aim for 40-50
- Single sentence only
- Output only the sentence"""

    PEOPLE_PROMPT = """You are annotating images for LoRA fine-tuning of a Flux image model.
Output exactly ONE sentence, maximum 50 words, grounded only in visible evidence.

Your sentence MUST begin with: "{SEMANTIC_CONTEXT}"

After "{SEMANTIC_CONTEXT}", add a natural connector word (with, engaged in, showing, working in) and describe in order:
1. Number and type of people (students, coworkers, group)
2. Their activity or interaction
3. Spatial arrangement and body language
4. Environment and visible objects
5. Lighting and overall atmosphere

Aim for 40-50 words to provide rich, specific detail.

Example:
"{SEMANTIC_CONTEXT} with five students engaged in collaborative discussion around large table, leaning forward with focused expressions, gesturing at shared design materials, bright modern classroom with whiteboards and task lighting creating productive energetic atmosphere"

Critical rules:
- Start EXACTLY with: {SEMANTIC_CONTEXT}
- No "photo of" or "image of"
- Maximum 50 words, aim for 40-50
- Single sentence only
- Output only the sentence"""

    VEHICLE_PROMPT = """You are annotating images for LoRA fine-tuning of a Flux image model.
Output exactly ONE sentence, maximum 50 words, grounded only in visible evidence.

Your sentence MUST begin with: "{SEMANTIC_CONTEXT}"

After "{SEMANTIC_CONTEXT}", add a natural connector word (with, featuring, showing, captured from) and describe in order:
1. Vehicle type and model characteristics
2. Viewing angle or perspective (front, side, three-quarter)
3. Surface materials, colors, and finish
4. Setting or environment context
5. Lighting conditions and visual impact

Aim for 40-50 words to provide rich, specific detail.

Example:
"{SEMANTIC_CONTEXT} with sleek aerodynamic body and distinctive LED headlights, captured from three-quarter front angle, glossy metallic silver paint with chrome accents, positioned in modern minimalist studio, dramatic side lighting highlighting sculptural surfacing and premium build quality"

Critical rules:
- Start EXACTLY with: {SEMANTIC_CONTEXT}
- No "photo of" or "image of"
- Maximum 50 words, aim for 40-50
- Single sentence only
- Output only the sentence"""

    EXTERIOR_PROMPT = """You are annotating images for LoRA fine-tuning of a Flux image model.
Output exactly ONE sentence, maximum 50 words, grounded only in visible evidence.

Your sentence MUST begin with: "{SEMANTIC_CONTEXT}"

After "{SEMANTIC_CONTEXT}", add a natural connector word (with, featuring, showing, captured at) and describe in order:
1. Building type and architectural features
2. Main materials and facade treatment
3. Surrounding context (street, landscape, sky)
4. Time of day and lighting conditions
5. Overall character or urban relationship

Aim for 40-50 words to provide rich, specific detail.

Example:
"{SEMANTIC_CONTEXT} with modern glass and steel facade featuring floor-to-ceiling windows and angular geometric form, surrounded by landscaped plaza with mature trees, captured at golden hour with warm sunlight illuminating translucent surfaces creating dynamic interplay of light and shadow"

Critical rules:
- Start EXACTLY with: {SEMANTIC_CONTEXT}
- No "photo of" or "image of"
- Maximum 50 words, aim for 40-50
- Single sentence only
- Output only the sentence"""

    ABSTRACT_PROMPT = """You are annotating images for LoRA fine-tuning of a Flux image model.
Output exactly ONE sentence, maximum 50 words, grounded only in visible evidence.

Your sentence MUST begin with: "{SEMANTIC_CONTEXT}"

After "{SEMANTIC_CONTEXT}", add a natural connector word (with, featuring, showing, composed of) and describe in order:
1. Medium or technique (digital, watercolor, sketch, diagram)
2. Compositional structure (geometric, organic, grid-based)
3. Dominant colors and shapes
4. Texture, layering, or surface quality
5. Overall style or aesthetic mood

Aim for 40-50 words to provide rich, specific detail.

Example:
"{SEMANTIC_CONTEXT} with layered digital composition featuring intersecting geometric forms and organic flowing lines, bold primary colors contrasted with subtle gradients, smooth vector surfaces mixed with textured brush elements creating dynamic minimalist aesthetic with balanced tension between order and spontaneity"

Critical rules:
- Start EXACTLY with: {SEMANTIC_CONTEXT}
- No "photo of" or "image of"
- Maximum 50 words, aim for 40-50
- Single sentence only
- Output only the sentence"""

    def __init__(self, api_key: Optional[str] = None, slow_mode: bool = False):
        """
        Initialize the caption generator.

        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            slow_mode: Enable slow mode (3s delay, useful for rate limiting or high load)
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.last_request_time = 0
        self.slow_mode = slow_mode
        # Slow mode: 3s delay (reduces API load, helps with rate limits)
        # Normal mode: 0.1s delay (paid tier supports 1,000 RPM = 0.06s min)
        self.rate_limit_delay = 3.0 if slow_mode else 0.1

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        # Configure Gemini API
        genai.configure(api_key=self.api_key)

        if slow_mode:
            logger.info("🐢 Slow mode enabled: 3s delay between API calls")

        # Model names for google-generativeai 0.8.x (latest API)
        # Prioritize Gemini 2.5 Flash for cost-effective image analysis:
        # - 4x cheaper than Pro ($0.30 vs $1.25 per 1M input tokens)
        # - Fast and accurate for architectural/interior descriptions
        # - Good quality for LoRA training captions
        model_preference = [
            'gemini-2.5-flash',          # Primary: Fast, cost-effective, good quality
            'gemini-2.5-pro',            # Fallback: Superior reasoning if Flash unavailable
            'gemini-2.0-flash-exp',      # Fallback: Experimental 2.0
            'gemini-1.5-flash',          # Fallback: Stable 1.5 Flash
            'gemini-1.5-pro',            # Fallback: Stable 1.5 Pro
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
                error_type = type(e).__name__
                error_msg = str(e)

                # Categorize error for better monitoring
                if 'quota' in error_msg.lower() or 'rate' in error_msg.lower() or '429' in error_msg:
                    error_category = "RATE_LIMIT"
                    logger.error(f"⚠️ RATE LIMIT ERROR (attempt {attempt + 1}/{max_retries}): {error_msg}")
                elif '503' in error_msg or 'unavailable' in error_msg.lower():
                    error_category = "SERVICE_UNAVAILABLE"
                    logger.error(f"⚠️ SERVICE UNAVAILABLE (attempt {attempt + 1}/{max_retries}): {error_msg}")
                elif '500' in error_msg or 'internal' in error_msg.lower():
                    error_category = "SERVER_ERROR"
                    logger.error(f"⚠️ SERVER ERROR (attempt {attempt + 1}/{max_retries}): {error_msg}")
                else:
                    error_category = "OTHER"
                    logger.error(f"⚠️ API ERROR ({error_type}, attempt {attempt + 1}/{max_retries}): {error_msg}")

                if attempt == max_retries - 1:
                    logger.error(f"💥 FAILED after {max_retries} attempts - Error: {error_category}")
                    raise

                # Exponential backoff: 1s, 2s, 4s, 8s...
                backoff_time = 2 ** attempt
                logger.warning(f"Retrying in {backoff_time}s...")
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

    def generate_caption(self, image_path: str, semantic_context: str, category: str = 'interior') -> Tuple[bool, str, Optional[str]]:
        """
        Generate a caption for an image.

        Args:
            image_path: Path to the image file
            semantic_context: User-provided context (e.g., "TU Delft drawing studio")
            category: Image category ('interior', 'person', 'object', 'scene')

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

            # Select prompt based on category
            prompt_map = {
                'interior': self.INTERIOR_PROMPT,
                'person': self.PERSON_PROMPT,
                'object': self.OBJECT_PROMPT,
                'scene': self.SCENE_PROMPT,
                'people': self.PEOPLE_PROMPT,
                'vehicle': self.VEHICLE_PROMPT,
                'exterior': self.EXTERIOR_PROMPT,
                'abstract': self.ABSTRACT_PROMPT
            }

            prompt_template = prompt_map.get(category.lower(), self.INTERIOR_PROMPT)
            prompt = prompt_template.replace("{SEMANTIC_CONTEXT}", semantic_context)

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
