"""
Image Dataset Metadata Generator
Flask web application for generating training metadata for LoRA models.
"""

import os
import uuid
import logging
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from utils.caption_generator import GeminiCaptionGenerator
from utils.image_processor import validate_image, create_thumbnail, sanitize_filename
from utils.validators import validate_trigger_word, normalize_trigger_word, get_trigger_word_examples
from utils.metadata_exporter import create_training_zip_in_memory, preview_metadata_content

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload

# Configure upload folder
UPLOAD_FOLDER = Path(__file__).parent / 'static' / 'uploads'
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# In-memory session storage
sessions = {}


@app.route('/')
def index():
    """Serve the main application page."""
    return render_template('index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Check API health and Gemini API configuration."""
    api_key = os.getenv('GEMINI_API_KEY')

    if not api_key:
        return jsonify({
            'status': 'unhealthy',
            'api_key_configured': False,
            'error': 'GEMINI_API_KEY environment variable not set'
        }), 503

    return jsonify({
        'status': 'healthy',
        'api_key_configured': True,
        'version': '1.0.0'
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
        # Generate session ID
        session_id = uuid.uuid4().hex

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

        for file in files:
            if file.filename == '':
                continue

            # Sanitize filename
            filename = sanitize_filename(file.filename)

            # Save file temporarily
            file_path = session_folder / filename
            file.save(file_path)

            # Validate image
            is_valid, error = validate_image(str(file_path))

            if is_valid:
                # Create thumbnail
                thumbnail = create_thumbnail(str(file_path))

                valid_images.append({
                    'filename': filename,
                    'size': file_path.stat().st_size,
                    'thumbnail': thumbnail,
                    'status': 'valid'
                })
            else:
                # Remove invalid file
                file_path.unlink()
                rejected.append({
                    'filename': filename,
                    'reason': error
                })

        # Store session data
        sessions[session_id] = {
            'folder': str(session_folder),
            'images': {img['filename']: {
                'path': str(session_folder / img['filename']),
                'caption': '',
                'edited': False,
                'status': 'pending'
            } for img in valid_images},
            'trigger_word': ''
        }

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
        if not session_id or session_id not in sessions:
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
        sessions[session_id]['trigger_word'] = trigger_word

        # Initialize caption generator
        generator = GeminiCaptionGenerator(trigger_word=trigger_word)

        # Get images from session
        images = sessions[session_id]['images']
        captions_result = []
        failed_images = []

        # Process each image
        for i, (filename, img_data) in enumerate(images.items(), 1):
            logger.info(f"Processing {filename} ({i}/{len(images)})")

            # Generate caption
            success, caption, error = generator.generate_caption(img_data['path'])

            if success:
                # Update session with caption
                sessions[session_id]['images'][filename]['caption'] = caption
                sessions[session_id]['images'][filename]['status'] = 'completed'

                captions_result.append({
                    'filename': filename,
                    'caption': caption,
                    'status': 'completed',
                    'edited': False
                })
            else:
                # Mark as failed
                sessions[session_id]['images'][filename]['status'] = 'failed'
                sessions[session_id]['images'][filename]['error'] = error

                failed_images.append({
                    'filename': filename,
                    'error': error
                })

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


@app.route('/api/caption', methods=['PUT'])
def update_caption():
    """Update a single caption (manual edit)."""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        filename = data.get('filename')
        caption = data.get('caption', '').strip()

        if not session_id or session_id not in sessions:
            return jsonify({
                'success': False,
                'error': 'Invalid session ID'
            }), 404

        if filename not in sessions[session_id]['images']:
            return jsonify({
                'success': False,
                'error': 'Image not found in session'
            }), 404

        trigger_word = sessions[session_id]['trigger_word']

        # Format caption with trigger word if needed
        if not caption.startswith('photo of '):
            if trigger_word:
                caption = f"photo of {trigger_word} {caption}"
            else:
                caption = f"photo of {caption}"

        # Update caption
        sessions[session_id]['images'][filename]['caption'] = caption
        sessions[session_id]['images'][filename]['edited'] = True

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
    if session_id not in sessions:
        return jsonify({
            'success': False,
            'error': 'Session not found'
        }), 404

    session_data = sessions[session_id]
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
    if session_id not in sessions:
        return jsonify({
            'success': False,
            'error': 'Session not found'
        }), 404

    session_data = sessions[session_id]
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

        if not session_id or session_id not in sessions:
            return jsonify({
                'success': False,
                'error': 'Invalid session ID'
            }), 400

        session_data = sessions[session_id]
        trigger_word = session_data['trigger_word']

        # Prepare image paths and captions
        image_paths = {}
        captions = {}

        for filename, img_data in session_data['images'].items():
            image_paths[filename] = img_data['path']
            captions[filename] = img_data['caption']

        # Create zip in memory
        success, zip_buffer, message = create_training_zip_in_memory(
            image_paths,
            captions,
            trigger_word
        )

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
    app.run(debug=True, host='0.0.0.0', port=5000)
