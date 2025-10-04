"""
Image Processing Utilities
Handles image validation, resizing, and thumbnail generation.
"""

import os
import io
import base64
import logging
from typing import Tuple, Optional
from PIL import Image

logger = logging.getLogger(__name__)

# Supported image formats
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png'}

# Size limits (in bytes)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_API_SIZE = 4 * 1024 * 1024    # 4 MB (resize if larger)


def get_file_extension(filename: str) -> str:
    """Get file extension in lowercase."""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''


def validate_image(file_path: str, file_size: Optional[int] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate an image file.

    Args:
        file_path: Path to the image file
        file_size: Optional file size in bytes (if known)

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    filename = os.path.basename(file_path)

    # Check file extension
    ext = get_file_extension(filename)
    if ext not in ALLOWED_EXTENSIONS:
        return (False, f"Invalid file type: .{ext}. Must be JPG, JPEG, or PNG.")

    # Check file exists
    if not os.path.exists(file_path):
        return (False, f"File not found: {filename}")

    # Check file size
    if file_size is None:
        file_size = os.path.getsize(file_path)

    if file_size > MAX_FILE_SIZE:
        size_mb = file_size / (1024 * 1024)
        return (False, f"File too large: {size_mb:.1f}MB (max {MAX_FILE_SIZE / (1024 * 1024):.0f}MB)")

    # Try to open as image
    try:
        with Image.open(file_path) as img:
            img.verify()  # Verify it's a valid image

        # Re-open for format check (verify() closes the file)
        with Image.open(file_path) as img:
            if img.format.lower() not in ['jpeg', 'png']:
                return (False, f"Invalid image format: {img.format}")

        logger.debug(f"Image validated: {filename}")
        return (True, None)

    except Exception as e:
        return (False, f"Invalid or corrupted image: {str(e)}")


def resize_image_for_api(image_path: str, max_dimension: int = 2048) -> Image.Image:
    """
    Resize image if needed for API processing.

    Args:
        image_path: Path to the image
        max_dimension: Maximum dimension (width or height) in pixels

    Returns:
        PIL Image object (resized if needed, converted to RGB)
    """
    img = Image.open(image_path)

    # Convert to RGB (remove alpha channel if present)
    if img.mode not in ('RGB', 'L'):
        img = img.convert('RGB')
        logger.debug(f"Converted image to RGB: {os.path.basename(image_path)}")

    # Check if resizing needed
    file_size = os.path.getsize(image_path)
    width, height = img.size

    # Resize if file is too large OR dimensions are too large
    if file_size > MAX_API_SIZE or max(width, height) > max_dimension:
        # Calculate new dimensions maintaining aspect ratio
        if width > height:
            new_width = min(width, max_dimension)
            new_height = int(height * (new_width / width))
        else:
            new_height = min(height, max_dimension)
            new_width = int(width * (new_height / height))

        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        logger.info(f"Resized image: {os.path.basename(image_path)} ({width}x{height} → {new_width}x{new_height})")

    return img


def create_thumbnail(image_path: str, size: Tuple[int, int] = (150, 150)) -> str:
    """
    Create a thumbnail and return as base64 data URL.

    Args:
        image_path: Path to the image
        size: Thumbnail size (width, height)

    Returns:
        Base64 data URL string (e.g., "data:image/jpeg;base64,...")
    """
    try:
        img = Image.open(image_path)

        # Convert to RGB if needed
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')

        # Create thumbnail (maintains aspect ratio)
        img.thumbnail(size, Image.Resampling.LANCZOS)

        # Save to bytes buffer
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)

        # Encode as base64
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        data_url = f"data:image/jpeg;base64,{img_base64}"

        logger.debug(f"Created thumbnail: {os.path.basename(image_path)}")
        return data_url

    except Exception as e:
        logger.error(f"Failed to create thumbnail for {image_path}: {e}")
        # Return a placeholder data URL or empty string
        return ""


def get_image_info(image_path: str) -> dict:
    """
    Get image metadata.

    Args:
        image_path: Path to the image

    Returns:
        Dictionary with image info (width, height, format, size)
    """
    try:
        img = Image.open(image_path)
        file_size = os.path.getsize(image_path)

        return {
            'filename': os.path.basename(image_path),
            'width': img.width,
            'height': img.height,
            'format': img.format,
            'mode': img.mode,
            'size_bytes': file_size,
            'size_mb': round(file_size / (1024 * 1024), 2)
        }
    except Exception as e:
        logger.error(f"Failed to get image info for {image_path}: {e}")
        return {
            'filename': os.path.basename(image_path),
            'error': str(e)
        }


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and other issues.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove path separators
    filename = os.path.basename(filename)

    # Remove or replace problematic characters
    # Keep alphanumeric, dots, hyphens, underscores
    safe_chars = []
    for char in filename:
        if char.isalnum() or char in '._- ':
            safe_chars.append(char)
        else:
            safe_chars.append('_')

    sanitized = ''.join(safe_chars)

    # Ensure it has an extension
    if '.' not in sanitized:
        sanitized += '.jpg'

    # Limit length
    if len(sanitized) > 255:
        name, ext = sanitized.rsplit('.', 1)
        sanitized = name[:250] + '.' + ext

    return sanitized
