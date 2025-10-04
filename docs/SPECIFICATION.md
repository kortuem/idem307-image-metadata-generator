# Technical Specification
## Image Dataset Metadata Generator for LoRA Training

**Version**: 1.0
**Last Updated**: 2025-10-04
**Status**: Approved for Development

---

## 1. Executive Summary

### 1.1 Purpose
Web application that automates metadata generation for image datasets used in LoRA model training on Replicate.com. Primary use case: university workshop (IDEM307, TU Delft) preparing 6 datasets (~180 images total).

### 1.2 Problem Statement
- **Current**: Manual captioning takes 2-3 hours per 30-image dataset
- **Target**: Reduce to 20-30 minutes using AI-assisted generation + manual refinement
- **Challenge**: Captions must follow strict format and maintain consistency across datasets

### 1.3 Solution Overview
Flask-based web application with:
- Local development environment (direct file system access)
- Vercel deployment capability (student-accessible via browser)
- Google Gemini vision API for caption generation
- Browser-based editing interface
- Export to Replicate-compatible format

---

## 2. Architecture

### 2.1 Technology Stack

**Backend**:
- Python 3.9+
- Flask 3.0+ (web framework)
- google-generativeai (Gemini API client)
- Pillow 10+ (image processing)
- python-dotenv (environment variables)

**Frontend**:
- HTML5
- CSS3 (vanilla, responsive)
- JavaScript (ES6+, vanilla - no frameworks)

**Deployment**:
- Local: Flask development server
- Production: Vercel (serverless functions + static hosting)

**Version Control**:
- Git + GitHub
- Automated Vercel deployment via GitHub integration

### 2.2 Application Modes

#### Mode 1: Local Development
```
User → Flask Server (localhost:5000) → File System
                ↓
        Gemini API (captions)
                ↓
        Download metadata.txt + zip
```

**Characteristics**:
- Direct file system access
- Folder selection via browser upload
- Runs on user's machine
- Full control over files

#### Mode 2: Vercel Production
```
Student → Vercel (your-app.vercel.app) → /tmp storage
                    ↓
            Gemini API (captions)
                    ↓
            Download metadata.txt + zip
```

**Characteristics**:
- No file system access (serverless)
- File upload via drag-and-drop
- Temporary storage in `/tmp`
- Files auto-deleted after session
- Shared with students (no local setup required)

### 2.3 File Structure

```
image-metadata-generator/
├── docs/                           # Documentation
│   ├── SPECIFICATION.md           # This file
│   ├── DEVELOPMENT_PLAN.md        # Development roadmap
│   └── API_DESIGN.md              # API endpoint specifications
├── api/                           # Vercel serverless functions
│   ├── upload.py                  # Handle image uploads
│   ├── generate.py                # Caption generation endpoint
│   └── export.py                  # Create metadata.txt + zip
├── app.py                         # Local Flask application
├── static/                        # Frontend assets
│   ├── css/
│   │   └── styles.css            # Application styles
│   ├── js/
│   │   └── app.js                # Frontend logic
│   └── uploads/                  # Temporary image storage (local only)
├── templates/                     # HTML templates
│   └── index.html                # Main application page
├── utils/                         # Shared utilities
│   ├── caption_generator.py      # Gemini API integration
│   ├── image_processor.py        # Image validation/processing
│   ├── metadata_exporter.py      # metadata.txt + zip creation
│   └── validators.py             # Input validation
├── tests/                         # Unit tests (optional Phase 4)
│   ├── test_caption_generator.py
│   ├── test_validators.py
│   └── fixtures/                 # Sample images for testing
├── .env                          # Local environment variables (gitignored)
├── .env.example                  # Template for .env
├── .gitignore
├── requirements.txt              # Python dependencies
├── vercel.json                   # Vercel configuration
├── README.md                     # Setup and usage instructions
├── PROJECT_BRIEF.md              # Original requirements
└── claude.md                     # Claude context/instructions
```

---

## 3. Functional Requirements

### 3.1 Image Upload & Selection

**FR-1.1: Image Upload**
- **Input**: Multiple image files via browser upload
- **Supported formats**: JPG, JPEG, PNG
- **Validation**:
  - File type check (MIME type + extension)
  - File size limit: 10MB per image
  - Maximum batch size: 100 images
  - Image readability check (can be opened by Pillow)
- **Error handling**:
  - Skip invalid files with warning
  - Show list of rejected files
  - Continue processing valid files

**FR-1.2: Image Display**
- Show thumbnail grid (150px × 150px thumbnails)
- Display filename below each thumbnail
- Show total image count
- Maintain aspect ratio in thumbnails

### 3.2 Trigger Word Input

**FR-2.1: Input Field**
- Text input for trigger word
- Placeholder: "e.g., ide_main_hall, ide_person"
- Required field (cannot be empty)

**FR-2.2: Validation Rules**
- Lowercase only (auto-convert or reject uppercase)
- Underscores allowed
- No spaces (reject or auto-convert to underscores)
- No hyphens (reject or auto-convert to underscores)
- Alphanumeric + underscore only: `^[a-z0-9_]+$`
- Length: 3-50 characters

**FR-2.3: Validation Feedback**
- Real-time validation on input
- Red border + error message if invalid
- Green checkmark if valid
- Example valid inputs shown

### 3.3 Caption Generation

**FR-3.1: Gemini API Integration**

**Model**: `gemini-2.0-flash-exp` (fallback: `gemini-1.5-flash`)

**Prompt Template**:
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

**FR-3.2: Batch Processing**
- Process images sequentially (not parallel)
- Rate limiting: 2-second delay between API calls
- Progress indicator: "Processing image X of Y..."
- Error handling:
  - Retry failed requests (exponential backoff: 1s, 2s, 4s, 8s, 16s)
  - Max 3 retries per image
  - Skip image after max retries (log error)
  - Continue processing remaining images
- Timeout: 30 seconds per API call

**FR-3.3: Caption Format**
- Prepend trigger word: `photo of {trigger_word} {ai_description}`
- Clean AI response: trim whitespace, remove trailing punctuation
- No line breaks within caption
- UTF-8 encoding

**FR-3.4: Image Preprocessing (before API call)**
- Resize if > 4MB: reduce to max 2048px on longest side
- Convert to RGB (remove alpha channel if present)
- Maintain aspect ratio
- Don't modify original files

### 3.4 Manual Editing Interface

**FR-4.1: Image Grid Display**
- Thumbnail grid layout (responsive: 4-6 columns depending on screen width)
- Click thumbnail to select image
- Highlight selected image (border + background color)
- Show filename below thumbnail

**FR-4.2: Full Image Preview**
- Display selected image at larger size (max 800px width)
- Maintain aspect ratio
- Filename displayed above image

**FR-4.3: Caption Editing**
- Textarea for caption (auto-expanding or fixed height with scroll)
- Pre-filled with auto-generated caption
- Real-time editing (no save button)
- Auto-save on blur or after 1 second of inactivity
- Character count (optional, helpful for very long captions)

**FR-4.4: Edit Status Indicator**
- Visual distinction:
  - Auto-generated: default text color
  - Manually edited: different color or icon (e.g., pencil icon)
- Persist edit status in memory

**FR-4.5: Navigation**
- Previous/Next buttons
- Keyboard shortcuts (optional Phase 4):
  - Arrow Left: Previous image
  - Arrow Right: Next image
  - Tab: Jump to caption textarea
- Click any thumbnail to jump to that image

**FR-4.6: Preview Mode**
- Button: "Preview metadata.txt"
- Modal/panel showing final formatted output
- Allows review before export

**FR-4.7: Debug Console Panel**
- Collapsible panel at bottom of interface
- Color-coded log messages:
  - INFO (blue): Normal operations (e.g., "Uploading 30 images...")
  - SUCCESS (green): Successful operations (e.g., "IMG_001.jpg: caption generated")
  - WARNING (yellow): Non-critical issues (e.g., "Retrying after timeout")
  - ERROR (red): Failures (e.g., "IMG_027.jpg: failed after 3 retries")
- Toggle show/hide button (default: expanded during operations, collapsed when idle)
- Auto-scroll to latest message
- Action buttons:
  - Clear logs
  - Copy logs to clipboard
  - Download logs as .txt file (optional)
- Timestamps for all messages ([HH:MM:SS] format)
- Logs persist within session (cleared on page refresh)

**Purpose**: Helps users troubleshoot issues and monitor processing progress in detail.

### 3.5 Export Functionality

**FR-5.1: Generate metadata.txt**
- Format: One line per image
- Order: Alphabetical by filename (case-insensitive)
- Encoding: UTF-8, no BOM
- Line endings: LF (Unix style) - `\n`
- Content: `photo of {trigger_word} {description}`

**Example**:
```
photo of ide_main_hall entrance area, glass doors, high ceiling, natural daylight, open circulation space
photo of ide_main_hall corridor view, seating areas, modern lighting fixtures, students visible
photo of ide_main_hall staircase detail, metal railings, concrete steps, industrial aesthetic
```

**FR-5.2: Create Zip File**
- Filename: `{trigger_word}_training.zip`
- Contents:
  - All uploaded images (original filenames, unmodified)
  - metadata.txt (in root of zip)
- Compression: standard ZIP format

**FR-5.3: Download/Export**
- Browser download (local & Vercel)
- Clear success message with filename
- Option to download metadata.txt separately (optional)

**FR-5.4: Validation Before Export**
- Check all images have captions
- Warn if any captions missing
- Confirm overwrite if file exists (local mode only)

---

## 4. Non-Functional Requirements

### 4.1 Performance

**NFR-1.1: Response Times**
- Page load: < 2 seconds
- Image upload: < 5 seconds for 30 images
- Caption generation: ~2-3 seconds per image (Gemini API latency)
- Total batch processing (30 images): ~2-3 minutes
- Export zip: < 5 seconds

**NFR-1.2: Scalability**
- Support up to 100 images per session
- Vercel function timeout: 10 seconds (requires streaming for batch processing)

### 4.2 Reliability

**NFR-2.1: Error Handling**
- Graceful degradation (one failed caption doesn't break entire batch)
- Clear error messages (user-friendly, actionable)
- Retry logic for API failures
- Validation at every input point

**NFR-2.2: Data Integrity**
- Original images never modified
- Captions stored in memory (session-based)
- No database required

### 4.3 Security

**NFR-3.1: API Key Management**
- Never expose API key in frontend code
- Environment variable: `GEMINI_API_KEY`
- Local: `.env` file (gitignored)
- Vercel: Environment variable in dashboard
- No user-provided API keys (uses your key server-side)

**NFR-3.2: Input Validation**
- Sanitize all user inputs
- File type validation (prevent upload of non-images)
- Trigger word validation (prevent injection)

**NFR-3.3: File Upload Security**
- File size limits
- MIME type validation
- Virus scanning (optional, Vercel handles some of this)

### 4.4 Usability

**NFR-4.1: User Experience**
- Intuitive workflow (no documentation needed for basic use)
- Clear progress indicators
- Responsive design (works on laptop/desktop)
- Accessible (keyboard navigation, screen reader friendly - Phase 4)

**NFR-4.2: Browser Compatibility**
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**NFR-4.3: Setup Simplicity**
- Local: `pip install -r requirements.txt` → `python app.py`
- Vercel: GitHub push → auto-deploy
- No database setup required
- No complex configuration

### 4.5 Maintainability

**NFR-5.1: Code Quality**
- PEP 8 compliance (Python)
- Clear variable/function names
- Comments for non-obvious logic
- Modular design (separation of concerns)

**NFR-5.2: Documentation**
- README with setup instructions
- Inline code comments
- API documentation (endpoints, parameters, responses)

---

## 5. Data Models

### 5.1 Session Data Structure (In-Memory)

```python
{
    "trigger_word": str,
    "images": [
        {
            "filename": str,           # Original filename
            "path": str,              # Temporary storage path
            "caption": str,           # Generated/edited caption
            "edited": bool,           # True if manually edited
            "status": str,            # "pending" | "processing" | "completed" | "failed"
            "error": str | None       # Error message if failed
        }
    ]
}
```

### 5.2 API Request/Response Models

**POST /api/upload**
```json
Request: multipart/form-data with image files

Response:
{
    "success": true,
    "images": [
        {"filename": "IMG_001.jpg", "size": 1234567, "status": "valid"},
        {"filename": "IMG_002.jpg", "size": 234567, "status": "valid"}
    ],
    "rejected": [
        {"filename": "invalid.txt", "reason": "Invalid file type"}
    ]
}
```

**POST /api/generate**
```json
Request:
{
    "trigger_word": "ide_main_hall",
    "images": ["IMG_001.jpg", "IMG_002.jpg"]
}

Response (streaming):
{
    "progress": {
        "current": 1,
        "total": 2,
        "filename": "IMG_001.jpg",
        "caption": "entrance area, glass doors, high ceiling...",
        "status": "completed"
    }
}
```

**POST /api/export**
```json
Request:
{
    "trigger_word": "ide_main_hall",
    "captions": {
        "IMG_001.jpg": "entrance area, glass doors...",
        "IMG_002.jpg": "corridor view, seating areas..."
    }
}

Response:
{
    "success": true,
    "zip_filename": "ide_main_hall_training.zip",
    "download_url": "/downloads/ide_main_hall_training.zip"
}
```

---

## 6. Security & Privacy

### 6.1 Data Handling

**Local Mode**:
- Images stored temporarily in `static/uploads/` (session-specific subdirectory)
- Cleared on server restart or manual cleanup

**Vercel Mode**:
- Images stored in `/tmp` (Vercel serverless)
- Automatically deleted after function execution
- No persistent storage

### 6.2 Privacy Considerations

- No images uploaded to third parties (except Gemini API for processing)
- No analytics or tracking
- No user accounts or authentication required
- Gemini API: Images sent for analysis (Google's privacy policy applies)

### 6.3 API Key Protection

- `.env` in `.gitignore`
- Never log API key
- Server-side only (never in frontend)
- Vercel environment variables encrypted at rest

---

## 7. External Dependencies

### 7.1 Python Packages

```
Flask==3.0.0
google-generativeai==0.3.2
Pillow==10.1.0
python-dotenv==1.0.0
```

### 7.2 External APIs

**Google Gemini API**:
- Endpoint: `generativelanguage.googleapis.com`
- Authentication: API key
- Rate limits (free tier):
  - 15 requests per minute
  - 1500 requests per day
- Pricing: Free tier sufficient for project (~180 images)

### 7.3 Browser APIs (Frontend)

- File API (file uploads)
- Fetch API (AJAX requests)
- FormData API (multipart uploads)

---

## 8. Deployment Strategy

### 8.1 Local Development

```bash
# Setup
git clone <repo>
cd image-metadata-generator
cp .env.example .env
# Add GEMINI_API_KEY to .env
pip install -r requirements.txt

# Run
python app.py
# Open http://localhost:5000
```

### 8.2 Vercel Deployment

**Initial Setup**:
1. Push code to GitHub
2. Connect GitHub repo to Vercel
3. Configure environment variables in Vercel dashboard:
   - `GEMINI_API_KEY`: <your_key>
4. Deploy

**Automatic Deployment**:
- Every push to `main` branch triggers deployment
- Preview deployments for pull requests

**vercel.json Configuration**:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/**/*.py",
      "use": "@vercel/python"
    },
    {
      "src": "static/**",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "api/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/static/$1"
    }
  ]
}
```

---

## 9. Testing Strategy

### 9.1 Manual Testing (MVP - Phase 1-3)

**Test Cases**:
1. Upload 5 sample images
2. Enter trigger word "test_space"
3. Generate captions
4. Edit 2 captions manually
5. Export metadata.txt + zip
6. Verify zip contents and format

### 9.2 Automated Testing (Optional - Phase 4)

**Unit Tests**:
- `test_validators.py`: trigger word validation
- `test_caption_generator.py`: caption formatting
- `test_metadata_exporter.py`: metadata.txt generation

**Integration Tests**:
- End-to-end workflow with fixture images
- Gemini API mocking (avoid API calls in tests)

---

## 10. Future Enhancements (Out of Scope for MVP)

### 10.1 Phase 4+ Features

- **Keyboard shortcuts**: Arrow keys for navigation
- **Batch edit**: Apply same edit to multiple images
- **Caption templates**: Pre-defined formats for common scenarios
- **Multi-language support**: Generate captions in different languages
- **Advanced export options**: CSV format, custom filename patterns
- **Image filtering**: Show only edited/unedited captions
- **Search**: Find images by caption keywords
- **User accounts**: Save projects, reuse trigger words
- **Local model option**: Use local vision models (e.g., LLaVA) for offline use

### 10.2 Performance Optimizations

- Parallel API calls (with rate limiting)
- Caching of generated captions
- Progressive image loading (lazy load thumbnails)
- Server-side thumbnail generation

---

## 11. Constraints & Assumptions

### 11.1 Constraints

- **Gemini API rate limits**: Free tier only (15 req/min)
- **Vercel limitations**: 10-second function timeout (requires streaming)
- **Browser file upload**: Limited by browser memory (~100MB total)
- **No database**: Session-based only (data lost on refresh)

### 11.2 Assumptions

- User has stable internet connection (for Gemini API)
- Images are of reasonable quality (not corrupted)
- User understands basic web application usage
- Desktop/laptop use (not optimized for mobile in MVP)
- Single user at a time (no concurrent session handling needed)

---

## 12. Success Metrics

### 12.1 Quantitative Metrics

- **Time savings**: 30-image dataset processed in < 30 minutes (vs. 2-3 hours manual)
- **Caption quality**: 80%+ captions require no editing (user assessment)
- **Reliability**: 95%+ success rate for caption generation (API failures < 5%)
- **Usability**: Tool usable without documentation

### 12.2 Qualitative Metrics

- User can process all 6 datasets without issues
- Generated metadata.txt uploads successfully to Replicate
- Trained LoRA models produce expected results
- Students can use Vercel-deployed version independently

---

## 13. Glossary

- **LoRA**: Low-Rank Adaptation - technique for fine-tuning image models
- **Trigger word**: Unique identifier prefixed to all captions (e.g., "ide_main_hall")
- **Replicate.com**: Platform for running/training AI models
- **metadata.txt**: Text file with one caption per line, required by Replicate
- **Gemini API**: Google's vision AI for image analysis
- **Vercel**: Serverless hosting platform for web applications

---

## 14. References

- [Replicate LoRA Training Documentation](https://replicate.com/docs/guides/train-a-lora)
- [Google Gemini API Documentation](https://ai.google.dev/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Vercel Python Documentation](https://vercel.com/docs/functions/serverless-functions/runtimes/python)

---

**Document Status**: Ready for Development
**Next Step**: Review DEVELOPMENT_PLAN.md for implementation phases
