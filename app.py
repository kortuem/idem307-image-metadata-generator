"""
Image Dataset Metadata Generator
Flask web application for generating training metadata for LoRA models.
"""

import os
import uuid
import json
import logging
import base64
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, Response
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from utils.caption_generator import GeminiCaptionGenerator
from utils.image_processor import validate_image, create_thumbnail, sanitize_filename
from utils.validators import validate_trigger_word, normalize_trigger_word, get_trigger_word_examples
from utils.metadata_exporter import create_training_zip_in_memory, preview_metadata_content

# Load environment variables
load_dotenv()

# Load secret access code from environment
SECRET_ACCESS_CODE = os.getenv('SECRET_ACCESS_CODE', '')

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload

# Configure upload folder
# Use /tmp for Vercel serverless compatibility (read-only filesystem)
UPLOAD_FOLDER = Path('/tmp') / 'uploads'
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Session storage for Vercel compatibility
# Store everything in /tmp/sessions as JSON files (including base64 images)
# This works on Vercel because warm containers keep /tmp for 5-15 minutes
SESSION_FOLDER = Path('/tmp') / 'sessions'
SESSION_FOLDER.mkdir(parents=True, exist_ok=True)

# Rate limiting configuration
# Max concurrent sessions to prevent out-of-memory crashes
# Each session uses ~80MB (30 images × 2MB base64 avg)
# Render Starter (1GB): Max 12 sessions safely
# Render Standard (2GB): Max 25 sessions safely
MAX_CONCURRENT_SESSIONS = int(os.getenv('MAX_CONCURRENT_SESSIONS', 12))
SESSION_TIMEOUT_MINUTES = 30  # Auto-cleanup old sessions

# Active sessions tracker (in-memory)
# Format: {session_id: timestamp}
active_sessions = {}

def save_session(session_id, data):
    """Save session data to /tmp as JSON file."""
    session_file = SESSION_FOLDER / f"{session_id}.json"
    with open(session_file, 'w') as f:
        json.dump(data, f)
    logger.info(f"Session {session_id} saved to {session_file}")

def load_session(session_id):
    """Load session data from /tmp JSON file."""
    session_file = SESSION_FOLDER / f"{session_id}.json"
    if not session_file.exists():
        logger.error(f"Session {session_id} not found at {session_file}")
        return None
    with open(session_file, 'r') as f:
        return json.load(f)

def session_exists(session_id):
    """Check if session exists."""
    return (SESSION_FOLDER / f"{session_id}.json").exists()

def cleanup_old_sessions():
    """Remove sessions older than SESSION_TIMEOUT_MINUTES from active tracker."""
    import time
    current_time = time.time()
    timeout_seconds = SESSION_TIMEOUT_MINUTES * 60

    expired_sessions = [
        sid for sid, timestamp in active_sessions.items()
        if current_time - timestamp > timeout_seconds
    ]

    for sid in expired_sessions:
        del active_sessions[sid]
        logger.info(f"Removed expired session {sid} from active tracker")

    return len(expired_sessions)

def get_active_session_count():
    """Get number of currently active sessions (after cleanup)."""
    cleanup_old_sessions()
    return len(active_sessions)

def register_session(session_id):
    """Register a new active session."""
    import time
    active_sessions[session_id] = time.time()
    logger.info(f"Session {session_id} registered. Active sessions: {len(active_sessions)}/{MAX_CONCURRENT_SESSIONS}")

def is_capacity_available():
    """Check if server has capacity for new session."""
    active_count = get_active_session_count()
    return active_count < MAX_CONCURRENT_SESSIONS


@app.route('/')
def index():
    """Serve the main application page."""
    return render_template('index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Check API health and Gemini API configuration."""
    api_key = os.getenv('GEMINI_API_KEY')
    active_count = get_active_session_count()
    capacity_available = is_capacity_available()

    if not api_key:
        return jsonify({
            'status': 'unhealthy',
            'api_key_configured': False,
            'error': 'GEMINI_API_KEY environment variable not set'
        }), 503

    return jsonify({
        'status': 'healthy',
        'api_key_configured': True,
        'version': '1.0.0',
        'capacity': {
            'active_sessions': active_count,
            'max_sessions': MAX_CONCURRENT_SESSIONS,
            'available': capacity_available,
            'utilization_percent': round((active_count / MAX_CONCURRENT_SESSIONS) * 100, 1)
        }
    })


@app.route('/api/validate-trigger-word', methods=['POST'])
def validate_trigger_word_endpoint():
    """Validate trigger word format."""
    data = request.get_json()
    trigger_word = data.get('trigger_word', '').strip()

    is_valid, message = validate_trigger_word(trigger_word)

    if is_valid:
        return jsonify({
            'valid': True,
            'trigger_word': trigger_word,
            'message': message
        })
    else:
        # Try to suggest normalized version
        normalized = normalize_trigger_word(trigger_word)
        is_normalized_valid, _ = validate_trigger_word(normalized)

        response = {
            'valid': False,
            'error': message,
            'examples': get_trigger_word_examples()
        }

        if is_normalized_valid and normalized != trigger_word:
            response['suggestion'] = normalized

        return jsonify(response)


@app.route('/api/upload', methods=['POST'])
def upload_images():
    """Handle image uploads."""
    try:
        # Check capacity BEFORE processing upload
        if not is_capacity_available():
            active_count = get_active_session_count()
            logger.warning(f"Server at capacity: {active_count}/{MAX_CONCURRENT_SESSIONS} active sessions")
            return jsonify({
                'success': False,
                'error': 'server_busy',
                'message': f'Server is currently at capacity ({active_count}/{MAX_CONCURRENT_SESSIONS} users). Please wait 2-3 minutes and try again.',
                'active_sessions': active_count,
                'max_sessions': MAX_CONCURRENT_SESSIONS,
                'retry_after': 120  # Suggest retry after 2 minutes
            }), 503

        # Generate session ID
        session_id = uuid.uuid4().hex

        # Register session immediately
        register_session(session_id)

        # Create session folder
        session_folder = UPLOAD_FOLDER / session_id
        session_folder.mkdir(parents=True, exist_ok=True)

        # Get uploaded files
        files = request.files.getlist('images')

        if not files or len(files) == 0:
            return jsonify({
                'success': False,
                'error': 'No images provided'
            }), 400

        valid_images = []
        rejected = []
        images_dict = {}

        for file in files:
            if file.filename == '':
                continue

            # Sanitize filename
            filename = sanitize_filename(file.filename)

            # Read file content into memory
            file_content = file.read()

            # Save file temporarily for validation
            file_path = session_folder / filename
            with open(file_path, 'wb') as f:
                f.write(file_content)

            # Validate image
            is_valid, error = validate_image(str(file_path))

            if is_valid:
                # Create thumbnail
                thumbnail = create_thumbnail(str(file_path))

                # Encode image as base64 for session storage
                image_base64 = base64.b64encode(file_content).decode('utf-8')

                valid_images.append({
                    'filename': filename,
                    'size': len(file_content),
                    'thumbnail': thumbnail,
                    'status': 'valid'
                })

                # Store image data in session (as base64)
                images_dict[filename] = {
                    'data': image_base64,  # Base64 encoded image
                    'caption': '',
                    'edited': False,
                    'status': 'pending'
                }

                # Delete temporary file after encoding
                file_path.unlink()
            else:
                # Remove invalid file
                if file_path.exists():
                    file_path.unlink()
                rejected.append({
                    'filename': filename,
                    'reason': error
                })

        # Store session data with base64 images
        session_data = {
            'images': images_dict,
            'trigger_word': ''
        }
        save_session(session_id, session_data)

        logger.info(f"Session {session_id}: Uploaded {len(valid_images)} images, rejected {len(rejected)}")

        return jsonify({
            'success': True,
            'session_id': session_id,
            'images': valid_images,
            'rejected': rejected,
            'total_valid': len(valid_images),
            'total_rejected': len(rejected)
        })

    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/generate', methods=['POST'])
def generate_captions():
    """Generate captions for all images in a session."""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        trigger_word = data.get('trigger_word', '').strip()

        # Validate inputs
        session_data = load_session(session_id)
        if not session_data:
            return jsonify({
                'success': False,
                'error': 'Invalid session ID'
            }), 400

        is_valid, message = validate_trigger_word(trigger_word)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': f'Invalid trigger word: {message}'
            }), 400

        # Update session with trigger word
        session_data['trigger_word'] = trigger_word
        save_session(session_id, session_data)

        # Initialize caption generator
        generator = GeminiCaptionGenerator(trigger_word=trigger_word)

        # Get images from session
        images = session_data['images']
        captions_result = []
        failed_images = []

        # Log which model we're using
        logger.info(f"Using Gemini model for caption generation")

        # Process each image
        for i, (filename, img_data) in enumerate(images.items(), 1):
            logger.info(f"Processing {filename} ({i}/{len(images)})")

            # Generate caption
            success, caption, error = generator.generate_caption(img_data['path'])

            if success:
                # Update session with caption
                session_data['images'][filename]['caption'] = caption
                session_data['images'][filename]['status'] = 'completed'
                save_session(session_id, session_data)

                captions_result.append({
                    'filename': filename,
                    'caption': caption,
                    'status': 'completed',
                    'edited': False
                })
                logger.info(f"✓ Generated caption for {filename}: {caption[:80]}...")
            else:
                # Mark as failed
                session_data['images'][filename]['status'] = 'failed'
                session_data['images'][filename]['error'] = error
                save_session(session_id, session_data)

                failed_images.append({
                    'filename': filename,
                    'error': error
                })
                logger.error(f"✗ Failed to generate caption for {filename}: {error}")

        logger.info(f"Session {session_id}: Generated {len(captions_result)} captions, {len(failed_images)} failed")

        return jsonify({
            'success': True,
            'captions': captions_result,
            'failed': failed_images,
            'total_processed': len(captions_result),
            'total_failed': len(failed_images)
        })

    except Exception as e:
        logger.error(f"Caption generation error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/generate-single', methods=['POST'])
def generate_single_caption():
    """Generate caption for a single image."""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        filename = data.get('filename')
        trigger_word = data.get('trigger_word', '').strip()

        session_data = load_session(session_id)
        if not session_data:
            return jsonify({
                'success': False,
                'error': 'Invalid session ID'
            }), 404

        if filename not in session_data['images']:
            return jsonify({
                'success': False,
                'error': 'Image not found in session'
            }), 404

        # Update trigger word in session if provided
        if trigger_word and not session_data['trigger_word']:
            session_data['trigger_word'] = trigger_word
            save_session(session_id, session_data)
        elif not trigger_word:
            # Fall back to session trigger word if not provided
            trigger_word = session_data['trigger_word']

        img_data = session_data['images'][filename]

        # Get API key or access code from request (REQUIRED)
        user_input = data.get('api_key', '').strip()

        # Users must provide either:
        # 1. The secret access code "kind_gemini_key" to use the shared key
        # 2. Their own Gemini API key
        if not user_input:
            return jsonify({
                'success': False,
                'error': 'API key or access code required. Please enter your Gemini API key or use the provided access code.'
            }), 400

        logger.info(f"Generating caption for {filename}")

        # Check if user provided the secret access code from .env
        # If so, use the default API key from .env (your key)
        # Otherwise, treat the input as their own Gemini API key
        if SECRET_ACCESS_CODE and user_input.lower() == SECRET_ACCESS_CODE.lower():
            # Use shared API key from .env
            api_key_to_use = None
            logger.info("Using shared API key (access code provided)")
        else:
            # User provided their own API key
            api_key_to_use = user_input
            logger.info("Using user-provided API key")

        # Decode base64 image and save temporarily
        image_bytes = base64.b64decode(img_data['data'])
        temp_image_path = UPLOAD_FOLDER / session_id / filename
        temp_image_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_image_path, 'wb') as f:
            f.write(image_bytes)

        # Initialize caption generator
        generator = GeminiCaptionGenerator(
            trigger_word=trigger_word,
            api_key=api_key_to_use
        )

        # Generate caption
        success, caption, error = generator.generate_caption(str(temp_image_path))

        # Clean up temporary file
        if temp_image_path.exists():
            temp_image_path.unlink()

        if success:
            # Format with trigger word
            if trigger_word and not caption.startswith('photo of '):
                caption = f"photo of {trigger_word} {caption}"
            elif not caption.startswith('photo of '):
                caption = f"photo of {caption}"

            # Store caption
            session_data['images'][filename]['caption'] = caption
            session_data['images'][filename]['edited'] = False
            save_session(session_id, session_data)

            logger.info(f"✓ Generated caption for {filename}: {caption[:80]}...")

            return jsonify({
                'success': True,
                'filename': filename,
                'caption': caption
            })
        else:
            logger.error(f"✗ Failed to generate caption for {filename}: {error}")
            return jsonify({
                'success': False,
                'filename': filename,
                'error': error
            }), 500

    except Exception as e:
        logger.error(f"Error generating caption: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/caption', methods=['PUT'])
def update_caption():
    """Update a single caption (manual edit)."""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        filename = data.get('filename')
        caption = data.get('caption', '').strip()

        session_data = load_session(session_id)
        if not session_data:
            return jsonify({
                'success': False,
                'error': 'Invalid session ID'
            }), 404

        if filename not in session_data['images']:
            return jsonify({
                'success': False,
                'error': 'Image not found in session'
            }), 404

        trigger_word = session_data['trigger_word']

        # Format caption with trigger word if needed
        if not caption.startswith('photo of '):
            if trigger_word:
                caption = f"photo of {trigger_word} {caption}"
            else:
                caption = f"photo of {caption}"

        # Update caption
        session_data['images'][filename]['caption'] = caption
        session_data['images'][filename]['edited'] = True
        save_session(session_id, session_data)

        logger.info(f"Session {session_id}: Caption updated for {filename}")

        return jsonify({
            'success': True,
            'filename': filename,
            'caption': caption,
            'edited': True
        })

    except Exception as e:
        logger.error(f"Caption update error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/captions/<session_id>', methods=['GET'])
def get_captions(session_id):
    """Get all captions for a session."""
    session_data = load_session(session_id)
    if not session_data:
        return jsonify({
            'success': False,
            'error': 'Session not found'
        }), 404
    captions = []
    edited_count = 0

    for filename, img_data in session_data['images'].items():
        captions.append({
            'filename': filename,
            'caption': img_data.get('caption', ''),
            'edited': img_data.get('edited', False)
        })
        if img_data.get('edited'):
            edited_count += 1

    return jsonify({
        'success': True,
        'session_id': session_id,
        'trigger_word': session_data['trigger_word'],
        'captions': captions,
        'total_images': len(captions),
        'edited_count': edited_count
    })


@app.route('/api/preview/<session_id>', methods=['GET'])
def preview_metadata(session_id):
    """Preview metadata.txt content."""
    session_data = load_session(session_id)
    if not session_data:
        return jsonify({
            'success': False,
            'error': 'Session not found'
        }), 404
    captions = {filename: img_data['caption']
                for filename, img_data in session_data['images'].items()}

    # Check for missing captions
    missing = [f for f, c in captions.items() if not c or c.strip() == '']

    preview = preview_metadata_content(captions, session_data['trigger_word'])

    return jsonify({
        'success': True,
        'metadata_content': preview,
        'line_count': len(captions),
        'ready_for_export': len(missing) == 0,
        'warnings': [f"{f} has no caption" for f in missing] if missing else []
    })


@app.route('/api/export', methods=['POST'])
def export_zip():
    """Export zip file with images and metadata.txt."""
    try:
        data = request.get_json()
        session_id = data.get('session_id')

        session_data = load_session(session_id)
        if not session_data:
            return jsonify({
                'success': False,
                'error': 'Invalid session ID'
            }), 400
        trigger_word = session_data['trigger_word']

        # Decode base64 images to temporary files for ZIP creation
        temp_folder = UPLOAD_FOLDER / session_id
        temp_folder.mkdir(parents=True, exist_ok=True)

        image_paths = {}
        captions = {}

        for filename, img_data in session_data['images'].items():
            # Decode base64 to temporary file
            image_bytes = base64.b64decode(img_data['data'])
            temp_path = temp_folder / filename
            with open(temp_path, 'wb') as f:
                f.write(image_bytes)

            image_paths[filename] = str(temp_path)
            captions[filename] = img_data['caption']

        # Create zip in memory
        success, zip_buffer, message = create_training_zip_in_memory(
            image_paths,
            captions,
            trigger_word
        )

        # Clean up temporary files
        for temp_path in temp_folder.glob('*'):
            if temp_path.is_file():
                temp_path.unlink()
        if temp_folder.exists():
            temp_folder.rmdir()

        if not success:
            return jsonify({
                'success': False,
                'error': message
            }), 400

        logger.info(f"Session {session_id}: {message}")

        # Send zip file
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"{trigger_word}_training.zip"
        )

    except Exception as e:
        logger.error(f"Export error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # Check for API key
    if not os.getenv('GEMINI_API_KEY'):
        logger.warning("GEMINI_API_KEY not found in environment!")
        logger.warning("Please create a .env file with your API key")

    # Run development server
    port = int(os.getenv('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)
