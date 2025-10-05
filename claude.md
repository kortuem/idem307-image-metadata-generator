# Claude Project Instructions

> **Note for students/users**: This file contains development instructions for Claude Code (AI coding assistant).
> If you're looking for how to USE the app, see [README.md](README.md) or [TUTORIAL.md](TUTORIAL.md) instead.
> This file is for developers who want to understand or modify the code.

---

**STATUS**: ✅ **PRODUCTION** - Deployed and in active use for TU Delft IDEM307 Workshop

**Live App**: https://idem307-image-metadata-generator.onrender.com/
**Repository**: https://github.com/kortuem/idem307-image-metadata-generator
**Version**: 1.0 (January 2025)

---

## Project Overview

Flask web application for generating AI-powered image captions for LoRA fine-tuning datasets. Built for TU Delft IDEM307 workshop students preparing datasets for Replicate.com FLUX LoRA training.

### Architecture

**Stack**:
- **Backend**: Flask (Python 3.9+)
- **AI**: Google Gemini 2.5 Pro vision API
- **Frontend**: Vanilla JavaScript (no frameworks)
- **Deployment**: Render.com (free tier)
- **Session Storage**: Base64-encoded images in JSON files (`/tmp/sessions/`)

**Why Render over Vercel**:
- ✅ Supports long-running processes (18s per image generation)
- ✅ Persistent sessions (stateful, no "Invalid session ID" errors)
- ✅ No timeout limits on free tier
- ✅ Works perfectly with Flask

### Key Features

- **Batch Upload**: 20-100 images with drag-and-drop
- **AI Caption Generation**: Gemini 2.5 Pro with expert-level prompts
- **Real-time Progress**: Upload and generation progress tracking
- **Caption Editing**: Per-image review and manual editing
- **Replicate Export**: Individual .txt files per image (not metadata.txt)
- **Secret Access Code**: `SECRET_ACCESS_CODE` env var for shared API key

---

## Technical Details

### Caption Format (CRITICAL - DO NOT CHANGE)

**Required Replicate.com format**:
```
photo of [trigger_word] [description]
```

**Rules**:
- Literal "photo of " (lowercase, with space)
- Trigger word (e.g., `ide_main_hall`)
- Space before description
- No trailing punctuation
- Detailed, specific descriptions

**Correct**:
```
photo of ide_main_hall entrance area with glass doors, high ceiling,
natural daylight, open space, modern architecture
```

**Wrong**:
```
A photo of ide_main_hall...        ← "A" before "photo"
photo of ide_main_hall: entrance   ← colon separator
Photo of ide_main_hall...          ← capital P
ide_main_hall entrance...          ← missing "photo of"
```

---

### Gemini API Configuration

**Model Priority** (with fallbacks):
1. `gemini-2.5-pro` (primary - best quality)
2. `gemini-2.5-flash` (fallback)
3. `gemini-2.0-flash-exp` (fallback)
4. `gemini-1.5-pro` (fallback)
5. `gemini-1.5-flash` (last resort)

**Performance**:
- ~18 seconds per image with 2.5 Pro (acceptable for quality)
- ~10 minutes for 30 images
- 2-second delay between requests (rate limiting)

**Free Tier Limits**:
- 15 requests/minute
- 1,500 requests/day
- Sufficient for ~750 images/day

**Authentication**:
- `GEMINI_API_KEY` environment variable (deployer's key)
- `SECRET_ACCESS_CODE` environment variable (e.g., `idem307_2025`)
- Users can enter secret code OR their own API key

---

### Export Format (CRITICAL)

**Replicate.com FLUX LoRA requires**:
```
trigger_word_training.zip
├── image1.jpg
├── image1.txt          ← Contains: "photo of trigger_word description"
├── image2.jpg
├── image2.txt
└── ...
```

**NOT** a single `metadata.txt` file - each image needs its own .txt file.

**Implementation**: See `utils/metadata_exporter.py` - `create_training_zip_in_memory()`

---

### Session Storage Strategy

**Problem**: Vercel/serverless platforms are stateless - sessions don't persist between function invocations.

**Solution**: Store everything in `/tmp/sessions/{session_id}.json`:
- Images encoded as base64 strings
- Captions stored alongside
- Single JSON file per session
- Works on Render (persistent for ~15 min warm container)

**Structure**:
```json
{
  "trigger_word": "ide_main_hall",
  "images": {
    "image1.jpg": {
      "data": "base64_encoded_image_data...",
      "caption": "photo of ide_main_hall...",
      "edited": false,
      "status": "completed"
    }
  }
}
```

**Helper functions** (in `app.py`):
- `save_session(session_id, data)` → writes JSON to `/tmp/sessions/`
- `load_session(session_id)` → reads JSON from `/tmp/sessions/`
- `session_exists(session_id)` → checks if session file exists

---

## Development Principles

### 1. User-Centered Design
- Students are primary users (not developers)
- Clear error messages in plain language
- Progressive disclosure (advanced features hidden)
- Works on first try (no complex setup)

### 2. Reliability Over Features
- Better to do one thing well than many things poorly
- Graceful degradation (fallback models if primary fails)
- Clear feedback (progress bars, status messages)
- User can manually fix edge cases

### 3. Code Quality
- Clear variable names (`trigger_word`, not `tw`)
- Comments for non-obvious logic
- Modular functions (single responsibility)
- Error handling with try/except and logging
- Use `pathlib` for cross-platform file paths

---

## Key Constraints & Decisions

### Environment

**Local Development**:
- Python 3.9+
- Flask development server (port 5001)
- `.env` file for API keys (gitignored)

**Production (Render.com)**:
- Environment variables set in Render dashboard
- Gunicorn WSGI server
- `/tmp` for temporary storage
- Auto-deploy on git push

### Authentication Strategy

**Two-tier system**:
1. **Instructor's API key** (in `GEMINI_API_KEY` env var)
2. **Secret access code** (in `SECRET_ACCESS_CODE` env var)

**Flow**:
- User enters code in UI
- If matches `SECRET_ACCESS_CODE` → use instructor's API key
- Otherwise → treat as user's own API key
- Prevents API key sharing while controlling costs

### File Size Limits

- Max 10MB per image
- Max 100MB total upload
- Max 100 images per session
- Enforced in Flask config and frontend

---

## Current Architecture

### Backend (`app.py`)

**Key endpoints**:
- `/` → serve main HTML
- `/api/upload` → handle image upload, create session
- `/api/validate-trigger-word` → validate trigger word format
- `/api/generate-single` → generate caption for one image
- `/api/caption` (PUT) → update caption (manual edit)
- `/api/export` → create and download ZIP file
- `/api/preview/{session_id}` → preview all captions

**Session flow**:
1. Upload → creates session JSON in `/tmp/sessions/`
2. Generate → loads session, decodes base64, generates caption, saves session
3. Export → loads session, decodes all images, creates ZIP, sends download

### Frontend (`static/js/app.js`)

**State management**:
```javascript
const state = {
    sessionId: null,
    images: [],
    captions: {},
    triggerWord: '',
    currentImageIndex: 0
};
```

**Key functions**:
- `handleFileUpload()` → upload images with progress bar
- `validateTriggerWord()` → real-time trigger word validation
- `generateCaptions()` → sequential per-image generation
- `updateCaption()` → save edited caption to server
- `exportTrainingZip()` → download ZIP file

### Utils

**`utils/caption_generator.py`**:
- `GeminiCaptionGenerator` class
- Expert-level prompt engineering
- Model fallback chain
- Rate limiting and retry logic

**`utils/image_processor.py`**:
- Image validation (format, size, corruption)
- Thumbnail generation
- MPO to JPEG conversion (iPhone photos)

**`utils/validators.py`**:
- Trigger word format validation
- Normalization suggestions

**`utils/metadata_exporter.py`**:
- `create_training_zip_in_memory()` → creates Replicate-format ZIP
- Individual .txt files per image
- Alphabetical sorting

---

## Deployment

### Render.com Configuration

**Build Command**:
```bash
pip install -r requirements.txt
```

**Start Command**:
```bash
gunicorn app:app
```

**Environment Variables**:
- `GEMINI_API_KEY` → Your Gemini API key
- `SECRET_ACCESS_CODE` → Your chosen access code (e.g., `idem307_2025`)

**Instance Type**: Free
- 512 MB RAM (sufficient)
- Spins down after 15 min inactivity (cold start ~30s)
- Auto-deploys on GitHub push

### Auto-Deployment

**Workflow**:
1. Commit changes locally
2. `git push origin main`
3. Render detects push
4. Runs build command
5. Restarts app with new code
6. Live in ~2-3 minutes

---

## Known Limitations & Trade-offs

### Performance
- **18 seconds per image**: Acceptable trade-off for Gemini 2.5 Pro quality
- **Cold start (30s)**: Only on first request after 15 min idle
- **Serial processing**: Could parallelize, but rate limits make it unnecessary

### Storage
- **Sessions in /tmp**: Lost if container restarts (acceptable - user downloads ZIP)
- **Base64 encoding**: Increases memory ~33%, but simplifies stateless architecture
- **No persistence**: No database - session-based only

### UI/UX
- **No keyboard shortcuts in editor**: Could add arrow keys for navigation
- **No batch editing**: Edit one caption at a time
- **No save/load projects**: Export ZIP and start fresh each time

### Scalability
- **Free tier limit**: ~750 images/day (Gemini API)
- **Single user at a time**: OK for workshop, not for production at scale
- **No queue system**: Concurrent users might hit rate limits

---

## Future Enhancement Ideas

### High Priority (If Requested)
- ✨ Keyboard shortcuts (arrow keys for image navigation)
- ✨ Batch caption editing (apply template to multiple)
- ✨ Caption quality presets (detailed vs concise)
- ✨ Progress persistence (resume if browser closes)

### Medium Priority
- 🔧 Save/load projects (JSON download/upload)
- 🔧 Caption templates (e.g., "photo of {trigger} {subject}, {lighting}, {mood}")
- 🔧 Multi-language support
- 🔧 Export to other platforms (not just Replicate)

### Low Priority
- 💡 Local vision models (offline mode)
- 💡 Bulk dataset management
- 💡 Caption quality scoring
- 💡 A/B testing different prompts

---

## Development Workflow

### Making Changes

1. **Test locally first**:
   ```bash
   python app.py
   # Test at http://localhost:5001
   ```

2. **Commit with descriptive messages**:
   ```bash
   git add .
   git commit -m "feat: Add keyboard shortcuts for caption navigation"
   git push
   ```

3. **Monitor Render deployment**:
   - Watch build logs in Render dashboard
   - Test live app after deployment completes

### Debugging

**Local**:
- Check terminal for Flask logs
- Browser console (F12) for JavaScript errors
- Add `logger.info()` statements in Python

**Production (Render)**:
- Click "Logs" tab in Render dashboard
- Real-time logs show all `logger` output
- Check for Python exceptions or API errors

---

## Important Files

### Must Never Commit
- `.env` → Contains real API keys (gitignored)
- `static/uploads/*` → Temporary uploads (gitignored)

### Safe to Commit
- `claude.md` → This file (development context)
- `README.md` → Public documentation
- `TUTORIAL.md` → Student instructions
- `RENDER_DEPLOYMENT.md` → Deployment guide
- `.env.example` → Template (no real keys)

### Archive (Not Used)
- `archive/VERCEL_DEPLOYMENT.md` → Old Vercel attempt (didn't work)
- `archive/vercel.json` → Vercel config (not needed on Render)

---

## User Profile

**Prof. Gerd Kortuem**:
- Technical but not Python expert
- Values reliability > features
- Teaching IDEM307 workshop (6 datasets, ~180 images)
- Tool saves 12-18 hours of manual captioning work
- Quality matters (used in student teaching materials)

**Students** (indirect users via shared access code):
- Non-technical
- Need simple, working tool
- Process 20-40 images each
- Upload to Replicate.com after export

---

## Communication Guidelines (For Claude)

### When Making Changes

✅ **Do**:
- Test changes locally before suggesting
- Provide complete, working code (not pseudocode)
- Explain trade-offs when multiple approaches exist
- Show examples of expected output
- Update this file if architecture changes

❌ **Don't**:
- Break existing functionality
- Add dependencies without discussing
- Change caption format (breaks Replicate compatibility)
- Remove error handling
- Make assumptions about user's environment

### When User Reports Issues

1. **Reproduce locally** if possible
2. **Check logs** (local terminal or Render dashboard)
3. **Identify root cause** before suggesting fixes
4. **Provide complete fix** (don't leave it half-done)
5. **Test the fix** before pushing to production

---

## Success Metrics

**Primary Goal**: ✅ **ACHIEVED**
- Tool successfully deployed and working
- Students can generate captions without technical knowledge
- Saves significant time vs manual captioning

**Quality Metrics**:
- ✅ Captions match Replicate format (individual .txt files)
- ✅ No "Invalid session ID" errors in production
- ✅ Upload progress visible to users
- ✅ ~80% of captions acceptable without editing

**Reliability Metrics**:
- ✅ Works on Render free tier
- ✅ Cold start acceptable (~30s)
- ✅ No data loss during session
- ✅ ZIP export works correctly

---

## Contact & Support

**Developer**: Prof. Gerd Kortuem
**Email**: g.w.kortuem@tudelft.nl
**Institution**: TU Delft - Faculty of Industrial Design Engineering
**Course**: IDEM307 Generative AI and Design

**For Issues**:
- GitHub: https://github.com/kortuem/idem307-image-metadata-generator/issues
- Email instructor for course-specific questions

---

**Last Updated**: January 2025 (v1.0 Production Release)
