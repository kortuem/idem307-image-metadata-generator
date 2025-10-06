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
from utils.metadata_exporter import create_training_zip_in_memory, preview_metadata_content
from utils.session_manager import SessionManager

# Load environment variables
load_dotenv()

# Load secret access code from environment
SECRET_ACCESS_CODE = os.getenv('SECRET_ACCESS_CODE', '')

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload

# Get build/deploy time from last git commit
def get_deploy_time():
    """Get deployment time from last git commit."""
    try:
        import subprocess
        from datetime import datetime
        result = subprocess.check_output(
            ['git', 'log', '-1', '--format=%cI'],
            text=True,
            stderr=subprocess.DEVNULL
        ).strip()
        commit_date = datetime.fromisoformat(result.replace('Z', '+00:00'))
        return commit_date.strftime('%B %d, %Y at %I:%M %p UTC')
    except:
        return 'October 2025'

DEPLOY_TIME = get_deploy_time()

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

# Session storage - Redis (optional) or file-based (default)
# For Render paid plans: use persistent disk at /data (configured in dashboard)
# For local dev: use /tmp/sessions
REDIS_URL = os.getenv('REDIS_URL')

# Try /data first (Render persistent disk), fallback to /tmp for local dev
try:
    SESSION_FOLDER = Path('/data/sessions')
    SESSION_FOLDER.mkdir(parents=True, exist_ok=True)
except (PermissionError, OSError):
    SESSION_FOLDER = Path('/tmp/sessions')
    SESSION_FOLDER.mkdir(parents=True, exist_ok=True)
    logger.info("Using /tmp/sessions (no persistent disk available)")

session_manager = SessionManager(redis_url=REDIS_URL, file_folder=SESSION_FOLDER)

# Rate limiting configuration
# Max concurrent sessions to prevent out-of-memory crashes
# Each session uses ~80MB (30 images × 2MB base64 avg)
# Render instances:
#   Starter (512MB): Max 6 sessions safely
#   Standard (2GB): Max 30 sessions safely (CURRENT INSTANCE)
#   Pro (4GB): Max 50 sessions safely
# Set via environment variable MAX_CONCURRENT_SESSIONS
MAX_CONCURRENT_SESSIONS = int(os.getenv('MAX_CONCURRENT_SESSIONS', 30))
SESSION_TIMEOUT_MINUTES = 30  # Not used (cleanup disabled for workshop reliability)

# Active sessions tracker (in-memory, rebuilt from filesystem on startup)
# Format: {session_id: timestamp}
active_sessions = {}

def rebuild_active_sessions():
    """
    Rebuild active_sessions tracker from filesystem on startup.
    For workshop use: Keep ALL session files, no cleanup during active use.
    Manual cleanup after workshop via shell command.
    """
    import time

    if session_manager.storage_type == 'redis':
        logger.info("Using Redis - session tracking handled by Redis TTL")
        return

    # File-based: restore ALL session files (no deletion)
    session_files = list(SESSION_FOLDER.glob('*.json'))
    current_time = time.time()

    for session_file in session_files:
        session_id = session_file.stem  # filename without .json
        mtime = session_file.stat().st_mtime

        # Restore ALL sessions regardless of age
        active_sessions[session_id] = mtime
        age_minutes = (current_time - mtime) / 60
        logger.debug(f"Restored session {session_id[:8]}... (age: {age_minutes:.1f}m)")

    logger.info(f"Rebuilt {len(active_sessions)} active sessions from filesystem")

# Rebuild active sessions on app startup
rebuild_active_sessions()

def save_session(session_id, data):
    """Save session data using SessionManager (Redis or file-based)."""
    success = session_manager.save_session(session_id, data)
    if success:
        logger.info(f"Session {session_id[:16]}... saved ({session_manager.get_storage_type()})")
    return success

def load_session(session_id):
    """Load session data using SessionManager (Redis or file-based)."""
    data = session_manager.load_session(session_id)
    if not data:
        logger.error(f"Session {session_id[:16]}... not found ({session_manager.get_storage_type()})")
    return data

def session_exists(session_id):
    """Check if session exists."""
    return session_manager.session_exists(session_id)

def cleanup_old_sessions():
    """
    NO-OP for workshop: Keep all sessions during active use.
    Sessions persist for entire workshop day, cleaned up manually after.
    This prevents race conditions and premature deletion during caption generation.
    """
    # Return 0 expired sessions (nothing cleaned up)
    return 0

def get_active_session_count():
    """Get number of currently active sessions (after cleanup)."""
    cleanup_old_sessions()
    return len(active_sessions)

def register_session(session_id):
    """Register a new active session."""
    import time
    active_sessions[session_id] = time.time()
    logger.info(f"Session {session_id} registered. Active sessions: {len(active_sessions)}/{MAX_CONCURRENT_SESSIONS}")

def update_session_activity(session_id):
    """
    Update session activity timestamp.
    For workshop: No file touching needed since we don't cleanup during active use.
    """
    import time
    if session_id in active_sessions:
        active_sessions[session_id] = time.time()
        logger.debug(f"Session {session_id[:8]}... activity updated")

def is_capacity_available():
    """Check if server has capacity for new session."""
    active_count = get_active_session_count()
    return active_count < MAX_CONCURRENT_SESSIONS


@app.route('/')
def index():
    """Serve the main application page."""
    return render_template('index.html', deploy_time=DEPLOY_TIME)


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

    # Check if access code is configured (for debugging)
    access_code_configured = bool(SECRET_ACCESS_CODE and SECRET_ACCESS_CODE.strip())

    return jsonify({
        'status': 'healthy',
        'api_key_configured': True,
        'access_code_configured': access_code_configured,
        'session_storage': session_manager.get_storage_type(),
        'version': '2.0.0',
        'capacity': {
            'active_sessions': active_count,
            'max_sessions': MAX_CONCURRENT_SESSIONS,
            'available': capacity_available,
            'utilization_percent': round((active_count / MAX_CONCURRENT_SESSIONS) * 100, 1)
        }
    })


@app.route('/api/validate-semantic-context', methods=['POST'])
def validate_semantic_context_endpoint():
    """Validate semantic context format."""
    data = request.get_json()
    semantic_context = data.get('semantic_context', '').strip()

    # Simple validation - just check it's not empty
    if not semantic_context:
        return jsonify({
            'valid': False,
            'error': 'Semantic context is required',
            'examples': ['TU Delft drawing studio', 'modern office workspace', 'industrial design lab']
        })

    # Check length (max 50 characters for context alone)
    if len(semantic_context) > 50:
        return jsonify({
            'valid': False,
            'error': 'Semantic context too long (max 50 characters)',
            'examples': ['TU Delft drawing studio', 'modern office workspace', 'industrial design lab']
        })

    return jsonify({
        'valid': True,
        'semantic_context': semantic_context,
        'message': 'Valid semantic context'
    })


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
            'semantic_context': ''  # User-provided context (e.g., "TU Delft drawing studio")
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
    """Generate captions for all images in a session (v2.0 - batch mode not recommended)."""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        semantic_context = data.get('semantic_context', '').strip()

        # Update session activity to keep it alive during long processing
        update_session_activity(session_id)

        # Validate inputs
        session_data = load_session(session_id)
        if not session_data:
            return jsonify({
                'success': False,
                'error': 'Invalid session ID'
            }), 400

        if not semantic_context:
            return jsonify({
                'success': False,
                'error': 'Semantic context is required'
            }), 400

        # Update session with semantic context
        session_data['semantic_context'] = semantic_context
        save_session(session_id, session_data)

        # Get API key or access code from request (REQUIRED)
        user_input = data.get('api_key', '').strip()

        if not user_input:
            return jsonify({
                'success': False,
                'error': 'API key or access code required'
            }), 400

        # Check if user provided the secret access code
        if SECRET_ACCESS_CODE and user_input.lower() == SECRET_ACCESS_CODE.lower():
            api_key_to_use = None  # Use shared API key from .env
            logger.info("Using shared API key (access code provided)")
        else:
            api_key_to_use = user_input  # User-provided API key
            logger.info("Using user-provided API key")

        # Initialize caption generator (no trigger_word parameter)
        generator = GeminiCaptionGenerator(api_key=api_key_to_use)

        # Get images from session
        images = session_data['images']
        captions_result = []
        failed_images = []

        # Log which model we're using
        logger.info(f"Using Gemini model for caption generation")

        # Process each image
        for i, (filename, img_data) in enumerate(images.items(), 1):
            logger.info(f"Processing {filename} ({i}/{len(images)})")

            # Decode base64 image and save temporarily
            image_bytes = base64.b64decode(img_data['data'])
            temp_image_path = UPLOAD_FOLDER / session_id / filename
            temp_image_path.parent.mkdir(parents=True, exist_ok=True)
            with open(temp_image_path, 'wb') as f:
                f.write(image_bytes)

            # Generate caption with semantic context
            success, caption, error = generator.generate_caption(
                str(temp_image_path),
                semantic_context
            )

            # Clean up temporary file
            if temp_image_path.exists():
                temp_image_path.unlink()

            if success:
                # Update session with caption (no trigger word prefix needed)
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
    """Generate caption for a single image (v2.0 - recommended approach)."""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        filename = data.get('filename')
        semantic_context = data.get('semantic_context', '').strip()

        # Update session activity to keep it alive during long processing
        update_session_activity(session_id)

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

        # Update semantic context in session if provided
        if semantic_context and not session_data['semantic_context']:
            session_data['semantic_context'] = semantic_context
            save_session(session_id, session_data)
        elif not semantic_context:
            # Fall back to session semantic context if not provided
            semantic_context = session_data.get('semantic_context', '')

        if not semantic_context:
            return jsonify({
                'success': False,
                'error': 'Semantic context is required'
            }), 400

        img_data = session_data['images'][filename]

        # Get API key or access code from request (REQUIRED)
        user_input = data.get('api_key', '').strip()

        if not user_input:
            return jsonify({
                'success': False,
                'error': 'API key or access code required. Please enter your Gemini API key or use the provided access code.'
            }), 400

        logger.info(f"Generating caption for {filename} with context: {semantic_context}")

        # Check if user provided the secret access code from .env
        if SECRET_ACCESS_CODE and user_input.lower() == SECRET_ACCESS_CODE.lower():
            api_key_to_use = None  # Use shared API key from .env
            logger.info("Using shared API key (access code matched)")
        else:
            api_key_to_use = user_input  # User-provided API key
            logger.info(f"Using user-provided API key (access code did not match, expected: {SECRET_ACCESS_CODE[:4] if SECRET_ACCESS_CODE else 'NOT_SET'}...)")

        # Decode base64 image and save temporarily
        image_bytes = base64.b64decode(img_data['data'])
        temp_image_path = UPLOAD_FOLDER / session_id / filename
        temp_image_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_image_path, 'wb') as f:
            f.write(image_bytes)

        # Initialize caption generator (no trigger_word parameter)
        generator = GeminiCaptionGenerator(api_key=api_key_to_use)

        # Generate caption with semantic context
        success, caption, error = generator.generate_caption(
            str(temp_image_path),
            semantic_context
        )

        # Clean up temporary file
        if temp_image_path.exists():
            temp_image_path.unlink()

        if success:
            # Store caption (already formatted by generator)
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
    """Update a single caption (manual edit) - v2.0 format."""
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

        # v2.0: No automatic formatting - user edits are stored as-is
        # Caption should already follow format: "{SEMANTIC_CONTEXT} {description}"
        # No "photo of" prefix, no trigger word

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
        'semantic_context': session_data.get('semantic_context', ''),
        'captions': captions,
        'total_images': len(captions),
        'edited_count': edited_count
    })


@app.route('/api/preview/<session_id>', methods=['GET'])
def preview_metadata(session_id):
    """Preview metadata.txt content (v2.0 - no trigger word in preview)."""
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

    # v2.0: No trigger_word parameter needed
    preview = preview_metadata_content(captions)

    return jsonify({
        'success': True,
        'metadata_content': preview,
        'line_count': len(captions),
        'ready_for_export': len(missing) == 0,
        'warnings': [f"{f} has no caption" for f in missing] if missing else []
    })


@app.route('/api/export', methods=['POST'])
def export_zip():
    """Export zip file with images and caption .txt files (v2.0)."""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        dataset_name = data.get('dataset_name', 'dataset').strip()  # Optional custom name

        session_data = load_session(session_id)
        if not session_data:
            return jsonify({
                'success': False,
                'error': 'Invalid session ID'
            }), 400

        # Use semantic_context as default dataset name if not provided
        if not dataset_name or dataset_name == 'dataset':
            semantic_context = session_data.get('semantic_context', '')
            if semantic_context:
                # Convert "TU Delft drawing studio" -> "tudelft_drawing_studio"
                dataset_name = semantic_context.lower().replace(' ', '_')
            else:
                dataset_name = 'dataset'

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

        # Create zip in memory (v2.0: dataset_name instead of trigger_word)
        success, zip_buffer, message = create_training_zip_in_memory(
            image_paths,
            captions,
            dataset_name
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

        # Delete session after successful export to free up disk space
        # This is critical for workshop with 30 concurrent students
        try:
            # Delete session file
            if session_manager.storage_type == 'file':
                session_file = SESSION_FOLDER / f"{session_id}.json"
                if session_file.exists():
                    session_file.unlink()
                    logger.info(f"Deleted session {session_id[:8]}... after export (freed ~80MB)")

            # Remove from active sessions tracker
            if session_id in active_sessions:
                del active_sessions[session_id]
        except Exception as cleanup_error:
            # Don't fail export if cleanup fails
            logger.warning(f"Failed to cleanup session {session_id[:8]}...: {cleanup_error}")

        # Send zip file
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"{dataset_name}_training.zip"
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
