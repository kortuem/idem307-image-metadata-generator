# API Design Documentation
## Image Dataset Metadata Generator

**Version**: 1.0
**Last Updated**: 2025-10-04

---

## Overview

This document specifies all API endpoints for the Image Dataset Metadata Generator. The application exposes a REST API for image processing, caption generation, and metadata export.

**Base URL**:
- Local: `http://localhost:5000`
- Vercel: `https://image-metadata-generator.vercel.app`

**Content Types**:
- Request: `multipart/form-data` (file uploads), `application/json` (other endpoints)
- Response: `application/json` (all endpoints except file downloads)

---

## Authentication

**None required** for MVP. API key for Gemini is stored server-side.

**Future Enhancement**: Optional API key authentication for rate limiting in production.

---

## Endpoints

### 1. Upload Images

**Endpoint**: `POST /api/upload`

**Description**: Upload multiple image files for processing.

**Request**:
```http
POST /api/upload HTTP/1.1
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW

------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="images"; filename="IMG_001.jpg"
Content-Type: image/jpeg

[binary data]
------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="images"; filename="IMG_002.jpg"
Content-Type: image/jpeg

[binary data]
------WebKitFormBoundary7MA4YWxkTrZu0gW--
```

**Parameters**:
- `images` (FormData): One or more image files

**Response** (200 OK):
```json
{
  "success": true,
  "session_id": "abc123def456",
  "images": [
    {
      "filename": "IMG_001.jpg",
      "size": 1234567,
      "thumbnail": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
      "status": "valid"
    },
    {
      "filename": "IMG_002.jpg",
      "size": 987654,
      "thumbnail": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
      "status": "valid"
    }
  ],
  "rejected": [
    {
      "filename": "invalid.txt",
      "reason": "Invalid file type (must be JPG, JPEG, or PNG)"
    }
  ],
  "total_valid": 2,
  "total_rejected": 1
}
```

**Response** (400 Bad Request):
```json
{
  "success": false,
  "error": "No images provided"
}
```

**Response** (413 Payload Too Large):
```json
{
  "success": false,
  "error": "Total upload size exceeds 100MB limit"
}
```

**Validation**:
- File type: JPG, JPEG, PNG (MIME type + extension)
- Individual file size: < 10MB
- Total upload size: < 100MB
- Maximum files: 100

**Notes**:
- Server generates thumbnails (150×150px) as base64 data URLs
- Invalid files are rejected but don't fail the entire request
- `session_id` is generated for tracking uploaded images

---

### 2. Validate Trigger Word

**Endpoint**: `POST /api/validate-trigger-word`

**Description**: Validate trigger word before caption generation.

**Request**:
```json
{
  "trigger_word": "ide_main_hall"
}
```

**Response** (200 OK - Valid):
```json
{
  "valid": true,
  "trigger_word": "ide_main_hall"
}
```

**Response** (200 OK - Invalid):
```json
{
  "valid": false,
  "error": "Trigger word must contain only lowercase letters, numbers, and underscores",
  "examples": ["ide_main_hall", "ide_person", "test_space_01"]
}
```

**Validation Rules**:
- Pattern: `^[a-z0-9_]+$`
- Length: 3-50 characters
- No spaces, hyphens, or special characters
- Lowercase only

---

### 3. Generate Captions

**Endpoint**: `POST /api/generate`

**Description**: Generate captions for all uploaded images using Gemini API. Supports streaming for real-time progress updates.

**Request**:
```json
{
  "session_id": "abc123def456",
  "trigger_word": "ide_main_hall"
}
```

**Response** (200 OK - Streaming):

Server sends Server-Sent Events (SSE) for progress updates:

```
data: {"type": "progress", "current": 1, "total": 30, "filename": "IMG_001.jpg", "status": "processing"}

data: {"type": "caption", "filename": "IMG_001.jpg", "caption": "entrance area, glass doors, high ceiling, natural daylight, open circulation space", "status": "completed"}

data: {"type": "progress", "current": 2, "total": 30, "filename": "IMG_002.jpg", "status": "processing"}

data: {"type": "caption", "filename": "IMG_002.jpg", "caption": "corridor view, seating areas, modern lighting fixtures, students visible", "status": "completed"}

...

data: {"type": "complete", "total_processed": 30, "total_failed": 0, "duration_seconds": 78}
```

**Response** (200 OK - Non-Streaming Alternative):

For simpler implementation, can return all captions at once:

```json
{
  "success": true,
  "captions": [
    {
      "filename": "IMG_001.jpg",
      "caption": "photo of ide_main_hall entrance area, glass doors, high ceiling, natural daylight, open circulation space",
      "status": "completed",
      "edited": false
    },
    {
      "filename": "IMG_002.jpg",
      "caption": "photo of ide_main_hall corridor view, seating areas, modern lighting fixtures",
      "status": "completed",
      "edited": false
    }
  ],
  "failed": [],
  "total_processed": 30,
  "total_failed": 0,
  "duration_seconds": 78
}
```

**Response** (400 Bad Request):
```json
{
  "success": false,
  "error": "Invalid session_id or trigger_word"
}
```

**Response** (500 Internal Server Error):
```json
{
  "success": false,
  "error": "Gemini API error: Rate limit exceeded. Please try again in 60 seconds."
}
```

**Processing Flow**:
1. Validate `session_id` and `trigger_word`
2. Retrieve uploaded images from session
3. For each image:
   - Resize if needed (> 4MB)
   - Send to Gemini API with prompt
   - Format response: `photo of {trigger_word} {description}`
   - Add 2-second delay before next image
4. Return all captions (or stream progress)

**Error Handling**:
- Retry failed API calls (exponential backoff: 1s, 2s, 4s, 8s)
- Max 3 retries per image
- Skip image after max retries (mark as failed)
- Continue processing remaining images

**Rate Limiting**:
- 2-second delay between API calls
- Tracks last request time per session
- Returns 429 if rate limit exceeded

---

### 4. Update Caption

**Endpoint**: `PUT /api/caption`

**Description**: Update a single caption (manual edit).

**Request**:
```json
{
  "session_id": "abc123def456",
  "filename": "IMG_001.jpg",
  "caption": "entrance area with large glass doors, double-height ceiling, abundant natural daylight"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "filename": "IMG_001.jpg",
  "caption": "photo of ide_main_hall entrance area with large glass doors, double-height ceiling, abundant natural daylight",
  "edited": true
}
```

**Response** (404 Not Found):
```json
{
  "success": false,
  "error": "Image not found in session"
}
```

**Notes**:
- Caption is automatically prefixed with `photo of {trigger_word}` if not already present
- Sets `edited: true` flag for visual distinction in UI
- Caption stored in server session (in-memory)

---

### 5. Get All Captions

**Endpoint**: `GET /api/captions/:session_id`

**Description**: Retrieve all captions for a session (useful for preview).

**Request**:
```http
GET /api/captions/abc123def456 HTTP/1.1
```

**Response** (200 OK):
```json
{
  "success": true,
  "session_id": "abc123def456",
  "trigger_word": "ide_main_hall",
  "captions": [
    {
      "filename": "IMG_001.jpg",
      "caption": "photo of ide_main_hall entrance area, glass doors",
      "edited": true
    },
    {
      "filename": "IMG_002.jpg",
      "caption": "photo of ide_main_hall corridor view, seating areas",
      "edited": false
    }
  ],
  "total_images": 2,
  "edited_count": 1
}
```

**Response** (404 Not Found):
```json
{
  "success": false,
  "error": "Session not found"
}
```

---

### 6. Preview Metadata

**Endpoint**: `GET /api/preview/:session_id`

**Description**: Preview final metadata.txt content before export.

**Request**:
```http
GET /api/preview/abc123def456 HTTP/1.1
```

**Response** (200 OK):
```json
{
  "success": true,
  "metadata_content": "photo of ide_main_hall entrance area, glass doors, high ceiling\nphoto of ide_main_hall corridor view, seating areas, modern lighting",
  "line_count": 2,
  "ready_for_export": true,
  "warnings": []
}
```

**Response** (200 OK - With Warnings):
```json
{
  "success": true,
  "metadata_content": "...",
  "line_count": 30,
  "ready_for_export": false,
  "warnings": [
    "IMG_015.jpg has no caption",
    "IMG_027.jpg has no caption"
  ]
}
```

**Notes**:
- Captions sorted alphabetically by filename
- UTF-8 encoding, LF line endings
- `ready_for_export: false` if any captions missing

---

### 7. Export Zip

**Endpoint**: `POST /api/export`

**Description**: Create and download zip file with images + metadata.txt.

**Request**:
```json
{
  "session_id": "abc123def456"
}
```

**Response** (200 OK):
```http
HTTP/1.1 200 OK
Content-Type: application/zip
Content-Disposition: attachment; filename="ide_main_hall_training.zip"
Content-Length: 12345678

[binary zip data]
```

**Response** (400 Bad Request):
```json
{
  "success": false,
  "error": "Cannot export: 2 images missing captions",
  "missing_captions": ["IMG_015.jpg", "IMG_027.jpg"]
}
```

**Zip Contents**:
```
ide_main_hall_training.zip
├── IMG_001.jpg
├── IMG_002.jpg
├── IMG_003.jpg
├── ...
└── metadata.txt
```

**metadata.txt Format**:
```
photo of ide_main_hall entrance area, glass doors, high ceiling, natural daylight
photo of ide_main_hall corridor view, seating areas, modern lighting fixtures
photo of ide_main_hall staircase detail, metal railings, concrete steps
```

**Validation Before Export**:
- All images must have captions
- Trigger word must be set
- Session must exist

---

### 8. Health Check

**Endpoint**: `GET /api/health`

**Description**: Check API health and Gemini API connectivity.

**Request**:
```http
GET /api/health HTTP/1.1
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "api_key_configured": true,
  "gemini_api_status": "available",
  "version": "1.0.0"
}
```

**Response** (503 Service Unavailable):
```json
{
  "status": "unhealthy",
  "api_key_configured": false,
  "gemini_api_status": "unavailable",
  "error": "GEMINI_API_KEY environment variable not set"
}
```

---

## Error Codes

| HTTP Code | Meaning | Example |
|-----------|---------|---------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid trigger word, missing session_id |
| 404 | Not Found | Session not found, image not found |
| 413 | Payload Too Large | Upload exceeds size limit |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Gemini API failure, unexpected error |
| 503 | Service Unavailable | API key not configured |

---

## Rate Limiting

**Gemini API Limits** (Free Tier):
- 15 requests per minute
- 1500 requests per day

**Application Strategy**:
- 2-second delay between requests (max 30 req/min)
- Retry with exponential backoff on rate limit errors
- Return 429 to client if persistent rate limiting

**Future Enhancement**: Implement Redis-based rate limiting for multi-user scenarios.

---

## Session Management

**Session Storage**: In-memory dictionary (no persistence)

**Session Data Structure**:
```python
sessions = {
    "abc123def456": {
        "created_at": "2025-10-04T10:30:00Z",
        "trigger_word": "ide_main_hall",
        "images": [
            {
                "filename": "IMG_001.jpg",
                "path": "/tmp/uploads/abc123/IMG_001.jpg",
                "caption": "photo of ide_main_hall entrance area...",
                "edited": False,
                "thumbnail": "data:image/jpeg;base64,...",
                "status": "completed"
            }
        ]
    }
}
```

**Session Lifecycle**:
1. Created on `/api/upload`
2. Updated during `/api/generate` and `/api/caption`
3. Read during `/api/preview` and `/api/export`
4. Expired after 1 hour of inactivity (cleanup job)

**Session ID**: Generated using `uuid.uuid4().hex` (32-character hex string)

---

## CORS Configuration

**Local Development**:
```python
CORS(app, origins=["http://localhost:5000"])
```

**Vercel Production**:
```python
CORS(app, origins=["https://image-metadata-generator.vercel.app"])
```

**Headers**:
- `Access-Control-Allow-Origin`: Specified origin
- `Access-Control-Allow-Methods`: GET, POST, PUT, DELETE
- `Access-Control-Allow-Headers`: Content-Type

---

## Gemini API Integration

### Vision Prompt Template

**Sent to Gemini API**:
```
Analyze this interior space/person image and provide a structured description following this format:

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

Do NOT include the "photo of [trigger_word]" prefix - that will be added automatically.
```

**Model Used**: `gemini-2.5-flash-latest` (fallback chain: 2.5-flash → 2.0-flash-exp → 1.5-flash)

**API Call Example**:
```python
import google.generativeai as genai
from PIL import Image

genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-2.5-flash-latest')

image = Image.open('photo.jpg')
response = model.generate_content([VISION_PROMPT, image])
caption = response.text.strip()
```

**Error Handling**:
- `ResourceExhausted`: Rate limit exceeded → retry after delay
- `InvalidArgument`: Invalid image → skip image, log error
- `Unauthenticated`: Invalid API key → return 503
- `DeadlineExceeded`: Timeout → retry with backoff

---

## Frontend Integration

### JavaScript Fetch Examples

**Upload Images**:
```javascript
const formData = new FormData();
for (let file of files) {
  formData.append('images', file);
}

const response = await fetch('/api/upload', {
  method: 'POST',
  body: formData
});

const data = await response.json();
console.log(data.images); // Array of uploaded images
```

**Generate Captions (Non-Streaming)**:
```javascript
const response = await fetch('/api/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: sessionId,
    trigger_word: triggerWord
  })
});

const data = await response.json();
console.log(data.captions); // Array of captions
```

**Generate Captions (Streaming with SSE)**:
```javascript
const eventSource = new EventSource(`/api/generate?session_id=${sessionId}&trigger_word=${triggerWord}`);

eventSource.addEventListener('progress', (event) => {
  const data = JSON.parse(event.data);
  updateProgressBar(data.current, data.total);
});

eventSource.addEventListener('caption', (event) => {
  const data = JSON.parse(event.data);
  displayCaption(data.filename, data.caption);
});

eventSource.addEventListener('complete', (event) => {
  const data = JSON.parse(event.data);
  eventSource.close();
  showSuccessMessage(`Generated ${data.total_processed} captions`);
});
```

**Update Caption**:
```javascript
const response = await fetch('/api/caption', {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: sessionId,
    filename: 'IMG_001.jpg',
    caption: 'updated caption text'
  })
});

const data = await response.json();
console.log(data.edited); // true
```

**Export Zip**:
```javascript
const response = await fetch('/api/export', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ session_id: sessionId })
});

if (response.ok) {
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${triggerWord}_training.zip`;
  a.click();
}
```

---

## Vercel-Specific Considerations

### Function Timeout (10 seconds)

**Problem**: Batch caption generation for 30 images takes ~2-3 minutes.

**Solution**: Use streaming responses (Server-Sent Events) to keep connection alive.

**Implementation**:
```python
from flask import Response, stream_with_context
import time

@app.route('/api/generate', methods=['POST'])
def generate_captions():
    def generate():
        for i, image in enumerate(images):
            caption = generate_caption(image)
            yield f"data: {json.dumps({'current': i+1, 'caption': caption})}\n\n"
            time.sleep(2)  # Rate limiting
        yield "data: {\"type\": \"complete\"}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')
```

### Temporary Storage (/tmp)

**Vercel `/tmp` characteristics**:
- Max 512MB storage
- Cleared between function invocations (unpredictable)
- Not shared across functions

**Strategy**:
- Store uploaded images in `/tmp/{session_id}/`
- Clean up after export
- Warn user if storage limit exceeded

---

## Security Considerations

### Input Validation

**All endpoints validate**:
- File types (whitelist: JPG, JPEG, PNG)
- File sizes (max 10MB per file)
- Trigger word format (regex pattern)
- Session ID format (UUID hex)

### API Key Security

**Best Practices**:
- Store in environment variable
- Never log API key
- Never expose in frontend
- Rotate periodically (manual process)

### File Upload Security

**Mitigations**:
- MIME type validation
- Extension validation
- File size limits
- Pillow verification (can image be opened?)
- Temporary storage (not web-accessible)

### XSS Prevention

**User-controlled data**:
- Trigger word: validated with regex
- Captions: escaped in HTML output
- Filenames: sanitized (remove special characters)

---

## Testing

### Unit Tests (Optional - Phase 4)

**Test cases**:
- Validate trigger word (valid/invalid inputs)
- Caption formatting (prepend trigger word)
- Image validation (valid/invalid file types)
- Metadata generation (correct format, sorting)

### Integration Tests

**Test scenarios**:
1. Upload → Generate → Export (happy path)
2. Upload invalid files → Verify rejection
3. Generate with invalid trigger word → Verify error
4. Export with missing captions → Verify warning
5. Rate limit exceeded → Verify retry logic

### Manual Testing

**Checklist**:
- [ ] Upload 30 images → All appear in grid
- [ ] Generate captions → All successful
- [ ] Edit 5 captions → Changes persist
- [ ] Preview metadata → Correct format
- [ ] Export zip → Contains all files
- [ ] Unzip → metadata.txt readable
- [ ] Upload to Replicate → Accepted

---

## Monitoring & Logging

### Logging Strategy

**Log Levels**:
- `INFO`: Request received, processing started/completed
- `WARNING`: Invalid input, skipped image, rate limit warning
- `ERROR`: API failure, unexpected error

**Log Format**:
```
[2025-10-04 10:30:15] INFO: Upload request received: 30 images, session abc123
[2025-10-04 10:30:20] INFO: Caption generation started: session abc123, trigger_word ide_main_hall
[2025-10-04 10:32:45] WARNING: Image IMG_015.jpg skipped: Gemini API timeout after 3 retries
[2025-10-04 10:33:10] INFO: Caption generation completed: 29/30 successful
[2025-10-04 10:33:15] INFO: Export requested: session abc123
[2025-10-04 10:33:18] INFO: Export completed: ide_main_hall_training.zip (12.3 MB)
```

**Vercel Logs**:
- View in Vercel dashboard (Deployments → Function Logs)
- Real-time streaming during development

---

## Changelog

### Version 1.0 (2025-10-04)
- Initial API design
- Core endpoints: upload, generate, export
- Streaming support for caption generation
- Session-based state management

### Future Versions
- v1.1: Add authentication (API keys for rate limiting)
- v1.2: Add batch editing endpoints
- v1.3: Add project save/load (JSON export/import)

---

**Document Status**: Complete
**Implementation Status**: Ready for Development
**Next Step**: Begin Phase 1 coding (MVP)
