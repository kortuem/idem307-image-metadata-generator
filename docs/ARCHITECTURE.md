# Architecture Documentation

## System Overview

The Image Metadata Generator is a Flask-based web application that uses Google's Gemini vision AI to automatically generate captions for image training datasets in the format required by Replicate.com for FLUX LoRA fine-tuning.

**Key Design Decision**: Built as a web app (not Streamlit or CLI) for accessibility and deployment flexibility.

---

## Technology Stack

### Backend
- **Flask 3.0.0**: Lightweight web framework
- **Python 3.9+**: Runtime environment
- **google-generativeai**: Gemini API client
- **Pillow**: Image processing and validation
- **Gunicorn**: Production WSGI server

### Frontend
- **Vanilla JavaScript**: No frameworks (simplicity)
- **HTML5 + CSS3**: Modern responsive UI
- **Drag-and-drop API**: File uploads

### Deployment
- **Platform**: Render.com (free tier)
- **Server**: Gunicorn with 1 worker
- **Storage**: Temporary file system (`/tmp/sessions/`)

---

## Architecture Diagrams

### High-Level Flow

```
User Browser
    ↓ (1) Upload images + trigger word
Flask Backend
    ↓ (2) Process & store in session
Session Storage (/tmp/sessions/*.json)
    ↓ (3) Request caption generation
Gemini API
    ↓ (4) Return AI-generated captions
Flask Backend
    ↓ (5) Format captions
User Browser (displays for editing)
    ↓ (6) Export request
Flask Backend (creates ZIP)
    ↓ (7) Download
User's Computer
```

### Session Storage Architecture

```
Client Request → Flask generates session_id (UUID)
                     ↓
              Create /tmp/sessions/{session_id}.json
                     ↓
              Store images as base64 in JSON
                     {
                       "images": [
                         {
                           "filename": "img1.jpg",
                           "data": "base64...",
                           "caption": "photo of ..."
                         }
                       ],
                       "trigger_word": "ide_main_hall"
                     }
                     ↓
              Return session_id to client
                     ↓
              All subsequent requests include session_id
```

**Why Base64 in JSON?**
- Originally designed for Vercel (serverless/stateless)
- Kept for Render deployment (simpler than database)
- Works well for 20-40 image batches
- Session files auto-cleaned by OS `/tmp` management

---

## API Endpoints

### 1. `GET /`
**Purpose**: Serve main application UI
**Response**: HTML page with JavaScript app

### 2. `POST /upload`
**Purpose**: Upload images and create session
**Request**:
- Content-Type: `multipart/form-data`
- Files: Multiple image files
- Body: `trigger_word` (string)

**Response**:
```json
{
  "session_id": "uuid-string",
  "images": [
    {
      "filename": "image1.jpg",
      "thumbnail": "data:image/jpeg;base64,...",
      "caption": ""
    }
  ]
}
```

**Validation**:
- Max 100 images
- Allowed formats: JPG, JPEG, PNG, WEBP
- Max file size: 10MB per image
- Trigger word: 3-50 chars, alphanumeric + underscore

### 3. `POST /generate_caption`
**Purpose**: Generate AI caption for single image
**Request**:
```json
{
  "session_id": "uuid-string",
  "index": 0,
  "api_key": "optional-gemini-key"
}
```

**Response**:
```json
{
  "caption": "photo of ide_main_hall entrance area..."
}
```

**Rate Limiting**:
- 2-second delay between requests (built-in)
- Respects Gemini free tier: 15 req/min, 1500/day

### 4. `POST /update_caption`
**Purpose**: Save user-edited caption
**Request**:
```json
{
  "session_id": "uuid-string",
  "index": 0,
  "caption": "photo of ide_main_hall modified caption"
}
```

**Response**:
```json
{
  "status": "success"
}
```

### 5. `POST /export`
**Purpose**: Create Replicate-compatible ZIP file
**Request**:
```json
{
  "session_id": "uuid-string"
}
```

**Response**:
- Content-Type: `application/zip`
- Content-Disposition: `attachment; filename="trigger_word_training.zip"`
- Body: Binary ZIP file

**ZIP Structure**:
```
trigger_word_training.zip
├── image1.jpg          ← Original filename preserved
├── image1.txt          ← Caption in Replicate format
├── image2.jpg
├── image2.txt
└── ...
```

---

## Gemini API Integration

### Configuration

```python
# Model selection with fallback
MODEL = "gemini-2.5-pro"  # Primary: Best quality (~18s/image)
FALLBACK_MODELS = [
    "gemini-2.5-flash",   # Faster but lower quality
    "gemini-2.0-flash-exp"
]

# Generation settings
generation_config = {
    "temperature": 0.7,       # Balanced creativity
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 200  # Captions are short
}
```

### Caption Generation Prompt

```python
prompt = f"""Analyze this image and create a caption for LoRA training.

Format EXACTLY as:
photo of {trigger_word} [detailed visual description]

Rules:
- Start with literal "photo of {trigger_word} " (lowercase, with space)
- Describe visible elements: objects, materials, lighting, spatial layout
- Be specific and objective (no interpretation)
- Include: lighting conditions, colors, materials, spatial arrangement
- No trailing punctuation
- One line only

Example:
photo of {trigger_word} entrance area with glass doors, high ceiling with exposed beams, natural daylight from skylights, polished concrete floor, modern minimalist design
"""
```

### Error Handling

1. **API Key Validation**:
   - Check environment variable `GEMINI_API_KEY`
   - Accept user-provided key OR secret access code
   - Validate before first API call

2. **Rate Limiting**:
   - 2-second delay between requests (client-side)
   - Exponential backoff on 429 errors (server-side)

3. **Retry Logic**:
   - 3 attempts with exponential backoff (1s, 2s, 4s)
   - Fallback to alternative models on failure
   - Return error message if all attempts fail

4. **Content Safety**:
   - Handle SAFETY_SETTINGS blocks gracefully
   - Return placeholder caption: "photo of {trigger_word} image content"

---

## Session Management

### Session Lifecycle

```
1. Upload → Create session_id → Store in /tmp/sessions/{id}.json
2. Generate captions → Update session JSON
3. Edit captions → Update session JSON
4. Export → Read session JSON → Create ZIP → Return file
5. Cleanup → OS handles /tmp/ cleanup (typically 3-7 days)
```

### Session Data Structure

```json
{
  "session_id": "abc123-uuid",
  "trigger_word": "ide_main_hall",
  "created_at": "2025-01-15T10:30:00Z",
  "images": [
    {
      "filename": "IMG_001.jpg",
      "original_extension": ".jpg",
      "data": "base64-encoded-image-data...",
      "thumbnail": "base64-encoded-thumbnail...",
      "caption": "photo of ide_main_hall entrance area..."
    }
  ]
}
```

### Why Not Database?

- **Simplicity**: No DB setup/maintenance
- **Temporary Data**: Sessions only needed for hours, not days
- **Small Scale**: 20-40 images per session
- **Platform Compatibility**: Works on any platform with `/tmp/`
- **Auto-Cleanup**: OS handles cleanup automatically

---

## File Processing Pipeline

### Image Upload Pipeline

```
1. Receive multipart/form-data
   ↓
2. Validate image format (JPEG/PNG/WEBP)
   ↓
3. Validate file size (< 10MB)
   ↓
4. Read image with Pillow
   ↓
5. Validate image dimensions (min 100x100)
   ↓
6. Create thumbnail (300x300 max, maintain aspect ratio)
   ↓
7. Convert image to base64
   ↓
8. Convert thumbnail to base64
   ↓
9. Store in session JSON
   ↓
10. Return thumbnail to client for preview
```

### Export Pipeline

```
1. Receive session_id
   ↓
2. Load session JSON
   ↓
3. Validate all captions exist
   ↓
4. Create in-memory ZIP
   ↓
5. For each image (sorted alphabetically):
   - Decode base64 → binary
   - Add image to ZIP (original filename)
   - Create caption .txt file
   - Add caption to ZIP (same basename + .txt)
   ↓
6. Return ZIP as binary stream
```

### Caption Format Validation

```python
def validate_caption_format(caption: str, trigger_word: str) -> bool:
    """Ensure caption matches Replicate.com requirements"""
    # Must start with "photo of {trigger_word} "
    expected_start = f"photo of {trigger_word} "
    if not caption.startswith(expected_start):
        return False

    # Must have description after trigger word
    description = caption[len(expected_start):].strip()
    if not description:
        return False

    # No trailing punctuation
    if description[-1] in '.!?':
        return False

    return True
```

---

## Security Considerations

### API Key Protection

1. **Environment Variables**:
   - `GEMINI_API_KEY` stored in `.env` (gitignored)
   - `SECRET_ACCESS_CODE` stored in `.env` (gitignored)
   - Never exposed to client-side code

2. **Access Control**:
   - Users provide either:
     - Their own Gemini API key (client-side, not stored)
     - Secret access code (validated server-side against env var)
   - No authentication/user accounts (by design)

3. **Session Security**:
   - Session IDs are UUIDs (unguessable)
   - Sessions stored in `/tmp/` (not publicly accessible)
   - No permanent storage of user data

### Input Validation

1. **Trigger Word**:
   - Length: 3-50 characters
   - Allowed chars: alphanumeric + underscore
   - Prevents path traversal and injection

2. **File Uploads**:
   - Extension whitelist: `.jpg`, `.jpeg`, `.png`, `.webp`
   - MIME type validation
   - File size limit: 10MB
   - Image format validation with Pillow

3. **Session IDs**:
   - UUID v4 format validation
   - File path sanitization
   - Prevents directory traversal

---

## Performance Characteristics

### Processing Times

- **Image upload**: ~100ms for 30 images (5MB total)
- **Caption generation**: ~18 seconds per image (Gemini 2.5 Pro)
- **Export ZIP**: ~2 seconds for 30 images
- **Total workflow**: ~10-12 minutes for 30 images

### Bottlenecks

1. **Gemini API**: Longest step (~18s per image)
   - Mitigated by: Sequential processing with progress updates
   - Free tier limits: 15 req/min (not an issue with 18s per request)

2. **Base64 Encoding**: Minimal impact
   - 30 images × 2MB = ~80MB base64 in session JSON
   - Acceptable for temporary storage

3. **Network**: Upload time depends on user connection
   - Progress tracking added for user feedback

### Scalability Limits

**Current Design**:
- Single user sessions (no concurrent processing)
- 100 images max per session
- Free tier Gemini API: ~750 images/day

**Not Designed For**:
- Multi-user concurrent access (would need DB + queue)
- Large batches (>100 images)
- Real-time collaboration

**Target Use Case**: ✅ Perfect for
- Individual workshop students (20-40 images)
- Instructor preparing datasets (6 × 30 images)
- One-time or occasional use

---

## Frontend Architecture

### Application State

```javascript
const appState = {
  sessionId: null,           // UUID from server
  images: [],                // Array of {filename, thumbnail, caption}
  triggerWord: '',           // User input
  currentIndex: 0,           // For navigation
  isGenerating: false,       // Prevent double-clicks
  apiKey: ''                 // Optional user API key
};
```

### Key Functions

1. **Upload Handler**:
   - Collects files from drag-drop or file input
   - Shows progress bar during upload
   - Receives session_id and stores in state

2. **Caption Generator**:
   - Loops through images sequentially
   - Calls `/generate_caption` for each
   - Updates UI with progress (X/Y complete)
   - 2-second delay between requests

3. **Editor UI**:
   - Displays current image with caption
   - Previous/Next navigation
   - Live caption editing
   - Auto-saves on blur or navigation

4. **Export Handler**:
   - Calls `/export` endpoint
   - Creates download link from blob
   - Triggers browser download

### Error Handling

- Network errors: Show retry button
- Invalid session: Prompt to re-upload
- API errors: Display error message in caption field
- Validation errors: Red border + error text

---

## Deployment Architecture (Render.com)

### Why Render over Vercel?

| Feature | Render | Vercel |
|---------|--------|--------|
| Long processes | ✅ No timeout | ❌ 10s limit (free tier) |
| Stateful storage | ✅ `/tmp/` persists | ⚠️ Ephemeral |
| Flask support | ✅ Native | ⚠️ Requires serverless wrapper |
| Session handling | ✅ Works perfectly | ❌ "Invalid session" errors |
| Cost | ✅ Free tier sufficient | ✅ Free tier sufficient |

### Render Configuration

```yaml
# render.yaml (inferred from dashboard settings)
services:
  - type: web
    name: idem307-image-metadata-generator
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    envVars:
      - key: GEMINI_API_KEY
        sync: false  # Set in dashboard
      - key: SECRET_ACCESS_CODE
        sync: false  # Set in dashboard
```

### Environment Setup (Render Dashboard)

1. **Build Command**: `pip install -r requirements.txt`
2. **Start Command**: `gunicorn app:app`
3. **Environment Variables**:
   - `GEMINI_API_KEY`: Your Gemini API key
   - `SECRET_ACCESS_CODE`: `idem307_2025`
4. **Auto-Deploy**: Enabled (on git push to main)

### Production Monitoring

- **Logs**: Available in Render dashboard
- **Health Check**: Built-in (monitors `/` endpoint)
- **Cold Starts**: First request after inactivity takes ~30s
- **Uptime**: Free tier spins down after 15 min inactivity

---

## Project Structure

```
image-metadata-generator/
├── app.py                    # Main Flask application
│   ├── Route handlers (/upload, /generate_caption, etc.)
│   ├── Session management
│   └── Error handling
│
├── utils/                    # Backend modules
│   ├── caption_generator.py  # Gemini API integration
│   │   ├── generate_caption()
│   │   ├── validate_api_key()
│   │   └── retry_with_fallback()
│   │
│   ├── image_processor.py    # Image validation & thumbnails
│   │   ├── validate_image()
│   │   ├── create_thumbnail()
│   │   └── image_to_base64()
│   │
│   ├── validators.py         # Input validation
│   │   ├── validate_trigger_word()
│   │   └── validate_session_id()
│   │
│   └── metadata_exporter.py  # ZIP file creation
│       ├── create_training_zip()
│       └── validate_export_data()
│
├── templates/
│   └── index.html            # Main UI (includes inline JS)
│
├── static/
│   ├── css/styles.css        # Application styles
│   └── js/app.js             # Frontend JavaScript
│
├── docs/                     # Documentation
│   ├── ARCHITECTURE.md       # This file
│   ├── DEPLOYMENT-RENDER.md  # Deployment guide
│   └── DEVELOPMENT.md        # Developer workflow
│
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (gitignored)
├── .env.example              # Template for .env
├── .gitignore                # Git ignore rules
├── README.md                 # Project overview
├── TUTORIAL.md               # Student tutorial
└── claude.md                 # Claude Code instructions
```

---

## Design Decisions Log

### 1. Base64 Session Storage
**Decision**: Store images as base64 in JSON files
**Why**: Originally for Vercel serverless; kept for simplicity
**Trade-offs**: Higher memory usage, but acceptable for 20-40 images
**Alternatives Considered**: PostgreSQL, Redis (rejected: overkill for use case)

### 2. Sequential Caption Generation
**Decision**: Process images one-by-one on frontend
**Why**: User wants to see progress; respects rate limits
**Trade-offs**: Slower than parallel, but more reliable
**Alternatives Considered**: Background queue (rejected: added complexity)

### 3. No User Authentication
**Decision**: Share access code instead of user accounts
**Why**: Simpler for students; temporary use case
**Trade-offs**: No usage tracking, shared API quota
**Alternatives Considered**: OAuth (rejected: unnecessary friction)

### 4. Vanilla JavaScript
**Decision**: No frontend framework (React/Vue)
**Why**: Simple app, avoid build complexity
**Trade-offs**: More verbose code, but easier for instructor to modify
**Alternatives Considered**: React (rejected: overkill for project scope)

### 5. Gemini 2.5 Pro over Flash
**Decision**: Use slower but higher-quality model
**Why**: Quality matters for teaching materials; 18s acceptable
**Trade-offs**: 3-4x slower than Flash
**Alternatives Considered**: GPT-4 Vision (rejected: cost), Claude (rejected: API limits)

---

**Last Updated**: January 2025 (v1.0)
