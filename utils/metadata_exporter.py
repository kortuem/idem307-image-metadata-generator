"""
Metadata Export Utilities
Generates metadata.txt and creates training zip files for Replicate.
"""

import os
import zipfile
import logging
from typing import Dict, List, Tuple
from io import BytesIO

logger = logging.getLogger(__name__)


def generate_metadata_txt(captions: Dict[str, str], trigger_word: str = "") -> str:
    """
    Generate metadata.txt content from captions dictionary.

    Args:
        captions: Dictionary mapping filename -> caption
        trigger_word: Optional trigger word (will be prepended if not already in caption)

    Returns:
        Formatted metadata.txt content (UTF-8, LF line endings)
    """
    # Sort filenames alphabetically (case-insensitive)
    sorted_filenames = sorted(captions.keys(), key=lambda x: x.lower())

    lines = []
    for filename in sorted_filenames:
        caption = captions[filename].strip()

        # Ensure caption starts with "photo of" prefix
        if not caption.startswith("photo of "):
            if trigger_word and not caption.startswith(f"photo of {trigger_word}"):
                caption = f"photo of {trigger_word} {caption}"
            else:
                caption = f"photo of {caption}"

        # Remove trailing punctuation
        if caption and caption[-1] in '.!?':
            caption = caption[:-1]

        lines.append(caption)

    # Join with LF line endings
    metadata_content = '\n'.join(lines)

    logger.info(f"Generated metadata.txt with {len(lines)} captions")
    return metadata_content


def validate_captions(captions: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Validate captions before export.

    Args:
        captions: Dictionary mapping filename -> caption

    Returns:
        Tuple of (is_valid: bool, missing_captions: List[str])
    """
    missing = []

    for filename, caption in captions.items():
        if not caption or caption.strip() == "":
            missing.append(filename)

    is_valid = len(missing) == 0

    if not is_valid:
        logger.warning(f"Validation failed: {len(missing)} images missing captions")

    return (is_valid, missing)


def create_training_zip(
    image_folder: str,
    captions: Dict[str, str],
    trigger_word: str,
    output_path: str = None
) -> Tuple[bool, str, str]:
    """
    Create a training zip file with images and metadata.txt.

    Args:
        image_folder: Path to folder containing images
        captions: Dictionary mapping filename -> caption
        trigger_word: Trigger word for zip filename
        output_path: Optional output path (defaults to same folder as images)

    Returns:
        Tuple of (success: bool, zip_path: str, message: str)
    """
    try:
        # Validate captions first
        is_valid, missing = validate_captions(captions)
        if not is_valid:
            error_msg = f"Cannot export: {len(missing)} images missing captions: {', '.join(missing[:5])}"
            if len(missing) > 5:
                error_msg += f" and {len(missing) - 5} more"
            logger.error(error_msg)
            return (False, "", error_msg)

        # Generate metadata.txt content
        metadata_content = generate_metadata_txt(captions, trigger_word)

        # Determine output path
        if output_path is None:
            output_path = os.path.join(image_folder, f"{trigger_word}_training.zip")

        # Create zip file
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all images with individual caption .txt files
            for filename in captions.keys():
                image_path = os.path.join(image_folder, filename)
                if os.path.exists(image_path):
                    # Add image
                    zipf.write(image_path, arcname=filename)
                    logger.debug(f"Added to zip: {filename}")

                    # Add matching .txt file with caption
                    # Get base filename without extension
                    base_name = os.path.splitext(filename)[0]
                    txt_filename = f"{base_name}.txt"

                    # Get caption for this image
                    caption = captions.get(filename, '')

                    # Add .txt file with caption
                    zipf.writestr(txt_filename, caption.encode('utf-8'))
                    logger.debug(f"Added caption file: {txt_filename}")
                else:
                    logger.warning(f"Image not found, skipping: {filename}")

        # Get zip file size
        zip_size = os.path.getsize(output_path)
        zip_size_mb = zip_size / (1024 * 1024)

        success_msg = f"Created {trigger_word}_training.zip ({zip_size_mb:.1f} MB) with {len(captions)} images"
        logger.info(success_msg)

        return (True, output_path, success_msg)

    except Exception as e:
        error_msg = f"Failed to create zip file: {str(e)}"
        logger.error(error_msg)
        return (False, "", error_msg)


def create_training_zip_in_memory(
    image_paths: Dict[str, str],
    captions: Dict[str, str],
    trigger_word: str
) -> Tuple[bool, BytesIO, str]:
    """
    Create a training zip file in memory (for web download).

    Args:
        image_paths: Dictionary mapping filename -> full_path
        captions: Dictionary mapping filename -> caption
        trigger_word: Trigger word for naming

    Returns:
        Tuple of (success: bool, zip_buffer: BytesIO, message: str)
    """
    try:
        # Validate captions first
        is_valid, missing = validate_captions(captions)
        if not is_valid:
            error_msg = f"Cannot export: {len(missing)} images missing captions"
            logger.error(error_msg)
            return (False, BytesIO(), error_msg)

        # Generate metadata.txt content
        metadata_content = generate_metadata_txt(captions, trigger_word)

        # Create zip in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all images with individual caption .txt files
            for filename, image_path in image_paths.items():
                if os.path.exists(image_path):
                    # Add image
                    zipf.write(image_path, arcname=filename)
                    logger.debug(f"Added to zip: {filename}")

                    # Add matching .txt file with caption
                    # Get base filename without extension
                    base_name = os.path.splitext(filename)[0]
                    txt_filename = f"{base_name}.txt"

                    # Get caption for this image
                    caption = captions.get(filename, '')

                    # Add .txt file with caption
                    zipf.writestr(txt_filename, caption.encode('utf-8'))
                    logger.debug(f"Added caption file: {txt_filename}")
                else:
                    logger.warning(f"Image not found, skipping: {filename}")

        # Get zip size
        zip_size = zip_buffer.tell()
        zip_size_mb = zip_size / (1024 * 1024)

        # Reset buffer position for reading
        zip_buffer.seek(0)

        success_msg = f"Created zip in memory ({zip_size_mb:.1f} MB) with {len(captions)} images"
        logger.info(success_msg)

        return (True, zip_buffer, success_msg)

    except Exception as e:
        error_msg = f"Failed to create zip file: {str(e)}"
        logger.error(error_msg)
        return (False, BytesIO(), error_msg)


def preview_metadata_content(captions: Dict[str, str], trigger_word: str = "", max_lines: int = 10) -> str:
    """
    Generate a preview of metadata.txt content.

    Args:
        captions: Dictionary mapping filename -> caption
        trigger_word: Trigger word
        max_lines: Maximum lines to show in preview

    Returns:
        Preview string
    """
    metadata_content = generate_metadata_txt(captions, trigger_word)
    lines = metadata_content.split('\n')

    if len(lines) <= max_lines:
        preview = metadata_content
    else:
        preview_lines = lines[:max_lines]
        preview = '\n'.join(preview_lines)
        preview += f"\n\n... and {len(lines) - max_lines} more lines"

    return preview
