# Development Plan
## Image Dataset Metadata Generator

**Project Timeline**: Estimated 12-16 hours development time
**Development Approach**: Iterative MVP → Feature Complete → Polish

---

## Overview

This document outlines the step-by-step development plan for building the Image Dataset Metadata Generator. Development follows an incremental approach with working prototypes at each phase.

---

## Phase 1: Core Infrastructure & MVP (4-5 hours)

**Goal**: Working end-to-end caption generation with basic export

### 1.1 Project Setup (30 min)

**Tasks**:
- [x] Create project directory structure
- [ ] Initialize Git repository
- [ ] Create `.gitignore` (include `.env`, `static/uploads/`, `__pycache__/`, etc.)
- [ ] Create `requirements.txt` with core dependencies
- [ ] Create `.env.example` template
- [ ] Set up local `.env` with `GEMINI_API_KEY`
- [ ] Create basic `README.md` with setup instructions

**Deliverable**: Clean project structure ready for development

**Files Created**:
```
.gitignore
requirements.txt
.env.example
README.md
```

---

### 1.2 Gemini API Integration (1 hour)

**Tasks**:
- [ ] Create `utils/caption_generator.py`
- [ ] Implement `GeminiCaptionGenerator` class
  - Initialize with API key from environment
  - Method: `generate_caption(image_path: str) -> str`
  - Handle API errors with retries (exponential backoff)
  - Add 2-second delay between calls
- [ ] Implement caption formatting: `photo of {trigger_word} {description}`
- [ ] Test with single image (manual test script)

**Deliverable**: Working caption generation for single image

**Test**:
```python
# test_gemini.py
from utils.caption_generator import GeminiCaptionGenerator

gen = GeminiCaptionGenerator(trigger_word="test_space")
caption = gen.generate_caption("test_image.jpg")
print(caption)  # Should output: "photo of test_space [description]"
```

**Success Criteria**:
- Caption generated successfully
- Correct format with trigger word
- Handles API errors gracefully

---

### 1.3 Image Processing Utilities (45 min)

**Tasks**:
- [ ] Create `utils/image_processor.py`
- [ ] Implement `validate_image(file) -> bool`
  - Check file type (MIME + extension)
  - Check file size (< 10MB)
  - Verify image can be opened by Pillow
- [ ] Implement `resize_image_for_api(image_path) -> Image`
  - Resize if > 4MB (max 2048px longest side)
  - Convert to RGB (remove alpha)
  - Maintain aspect ratio
- [ ] Implement `create_thumbnail(image_path, size=(150, 150)) -> base64`
  - Generate thumbnail for frontend display
  - Return as base64 data URL

**Deliverable**: Image validation and processing utilities

---

### 1.4 Input Validation (30 min)

**Tasks**:
- [ ] Create `utils/validators.py`
- [ ] Implement `validate_trigger_word(word: str) -> tuple[bool, str]`
  - Check pattern: `^[a-z0-9_]+$`
  - Check length: 3-50 characters
  - Return (is_valid, error_message)
- [ ] Add unit tests (optional for MVP)

**Deliverable**: Robust input validation

---

### 1.5 Metadata Export Functionality (1 hour)

**Tasks**:
- [ ] Create `utils/metadata_exporter.py`
- [ ] Implement `generate_metadata_txt(captions: dict, trigger_word: str) -> str`
  - Sort captions alphabetically by filename
  - Format: `photo of {trigger_word} {description}`
  - UTF-8 encoding, LF line endings
- [ ] Implement `create_training_zip(image_folder: str, metadata_content: str, trigger_word: str) -> bytes`
  - Create zip with images + metadata.txt
  - Filename: `{trigger_word}_training.zip`
- [ ] Test zip creation and validate contents

**Deliverable**: Working export to Replicate format

**Test**:
```python
# test_export.py
captions = {
    "IMG_001.jpg": "entrance area, glass doors",
    "IMG_002.jpg": "corridor view, seating"
}
metadata = generate_metadata_txt(captions, "test_space")
print(metadata)
# Should output:
# photo of test_space entrance area, glass doors
# photo of test_space corridor view, seating
```

---

### 1.6 Basic Flask Application (1.5 hours)

**Tasks**:
- [ ] Create `app.py` (Flask server)
- [ ] Set up basic routes:
  - `GET /` → serve main page
  - `POST /api/upload` → handle image uploads
  - `POST /api/generate` → batch caption generation
  - `POST /api/export` → create zip file
- [ ] Configure upload folder (`static/uploads/`)
- [ ] Implement session management (in-memory dict for MVP)
- [ ] Add error handling middleware

**Deliverable**: Working Flask API

**API Endpoints** (detailed in next section):
```
GET  /                  → Main application page
POST /api/upload        → Upload images
POST /api/generate      → Generate captions
POST /api/export        → Export metadata + zip
GET  /api/status        → Check generation progress (optional)
```

---

### 1.7 Minimal Frontend (1.5 hours)

**Tasks**:
- [ ] Create `templates/index.html`
- [ ] Create `static/css/styles.css` (basic styles)
- [ ] Create `static/js/app.js`
- [ ] Implement basic UI:
  - File upload input (multiple files)
  - Trigger word text input
  - "Generate Captions" button
  - Progress indicator (simple text)
  - "Export" button
  - Download link for zip file
- [ ] Add collapsible debug console panel
  - Color-coded log levels (INFO, SUCCESS, WARNING, ERROR)
  - Toggle show/hide button
  - Auto-scroll to latest message
  - Clear logs button
  - Copy/download logs functionality

**Deliverable**: Functional (but minimal) web interface with debug monitoring

**UI Elements**:
```html
<input type="file" multiple accept="image/*">
<input type="text" id="trigger-word" placeholder="e.g., ide_main_hall">
<button id="generate-btn">Generate Captions</button>
<div id="progress">Processing 0 of 0...</div>
<button id="export-btn">Export Zip</button>

<!-- Debug Console -->
<div id="debug-panel" class="debug-panel collapsed">
  <div class="debug-header">
    <span>Debug Console</span>
    <button id="toggle-debug">▼</button>
  </div>
  <div class="debug-content">
    <div id="debug-logs"></div>
    <div class="debug-actions">
      <button id="clear-logs">Clear</button>
      <button id="copy-logs">Copy Logs</button>
    </div>
  </div>
</div>
```

**Debug Logger (JavaScript)**:
```javascript
const DEBUG = {
  INFO: 'info',
  SUCCESS: 'success',
  WARNING: 'warning',
  ERROR: 'error'
};

function log(level, message) {
  const timestamp = new Date().toLocaleTimeString();
  const logEntry = document.createElement('div');
  logEntry.className = `log-entry log-${level}`;
  logEntry.textContent = `[${timestamp}] ${level.toUpperCase()}: ${message}`;

  document.getElementById('debug-logs').appendChild(logEntry);
  logEntry.scrollIntoView({ behavior: 'smooth' });

  // Also log to browser console
  console.log(`[${level}] ${message}`);
}

// Usage examples:
log(DEBUG.INFO, 'Uploading 30 images...');
log(DEBUG.SUCCESS, 'IMG_001.jpg: caption generated');
log(DEBUG.WARNING, 'IMG_015.jpg: retrying after timeout (attempt 2/3)');
log(DEBUG.ERROR, 'IMG_027.jpg: failed after 3 retries');
```

---

### 1.8 End-to-End Testing (30 min)

**Tasks**:
- [ ] Test complete workflow:
  1. Upload 5 sample images
  2. Enter trigger word
  3. Generate captions
  4. Export zip
  5. Verify zip contents
- [ ] Test error cases:
  - Invalid image file
  - Missing trigger word
  - API failure (simulate)
- [ ] Fix bugs found during testing

**Success Criteria**:
- Complete workflow works without crashes
- Exported zip can be extracted and contains correct files
- metadata.txt format is correct

---

## Phase 2: Editing Interface (3-4 hours)

**Goal**: Review and manually edit generated captions

### 2.1 Image Grid Display (1 hour)

**Tasks**:
- [ ] Update `index.html` with image grid layout
- [ ] Add CSS for responsive grid (4-6 columns)
- [ ] Display thumbnails after upload
- [ ] Show filename below each thumbnail
- [ ] Implement click handler to select image

**Deliverable**: Clickable thumbnail grid

**CSS Layout**:
```css
.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 1rem;
}
```

---

### 2.2 Full Image Preview (45 min)

**Tasks**:
- [ ] Add preview area in HTML
- [ ] Display selected image at larger size (max 800px)
- [ ] Show filename above image
- [ ] Maintain aspect ratio
- [ ] Add loading state for large images

**Deliverable**: Selected image displays in preview area

---

### 2.3 Caption Editing (1.5 hours)

**Tasks**:
- [ ] Add textarea for caption editing
- [ ] Pre-fill with auto-generated caption
- [ ] Implement auto-save on blur (debounced)
- [ ] Update backend to track edited captions
- [ ] Add visual indicator for edited vs. auto-generated
  - Option 1: Color change (e.g., edited = blue, auto = black)
  - Option 2: Icon (pencil icon for edited)
- [ ] Store edit status in session data

**Deliverable**: Editable captions with save functionality

**Backend Update**:
```python
# Add to session data structure
{
    "filename": "IMG_001.jpg",
    "caption": "entrance area...",
    "edited": False  # Set to True when user edits
}
```

---

### 2.4 Navigation (45 min)

**Tasks**:
- [ ] Add "Previous" and "Next" buttons
- [ ] Implement navigation logic in JavaScript
- [ ] Update preview and caption when navigating
- [ ] Disable "Previous" on first image
- [ ] Disable "Next" on last image
- [ ] Optional: Keyboard shortcuts (arrow keys)

**Deliverable**: Easy navigation between images

---

### 2.5 Testing & Refinement (30 min)

**Tasks**:
- [ ] Test editing workflow with 20+ images
- [ ] Verify edits persist across navigation
- [ ] Test edge cases (empty caption, very long caption)
- [ ] Improve UI/UX based on testing

---

## Phase 3: Export Enhancement & Polish (2-3 hours)

**Goal**: Professional export experience with validation

### 3.1 Export Validation (45 min)

**Tasks**:
- [ ] Check all images have captions before export
- [ ] Warn if any captions are empty
- [ ] Show confirmation dialog before export
- [ ] Add preview mode: show final metadata.txt before export

**Deliverable**: Validated export process

**UI Flow**:
```
[Export] → Check captions → [Preview Modal] → [Confirm] → Download
```

---

### 3.2 Download Experience (1 hour)

**Tasks**:
- [ ] Generate zip file server-side
- [ ] Return download link to frontend
- [ ] Trigger automatic download in browser
- [ ] Show success message with filename
- [ ] Option to download metadata.txt separately
- [ ] Clean up temporary files after download

**Deliverable**: Smooth download experience

---

### 3.3 Progress Indicators (1 hour)

**Tasks**:
- [ ] Replace text progress with progress bar
- [ ] Show percentage (X%)
- [ ] Display current image filename
- [ ] Estimate time remaining (optional)
- [ ] Add loading spinners for uploads
- [ ] Disable buttons during processing

**Deliverable**: Clear visual feedback for all operations

**UI Components**:
```html
<div class="progress-bar">
  <div class="progress-fill" style="width: 45%"></div>
</div>
<p>Processing IMG_012.jpg (12 of 30) - 45%</p>
```

---

### 3.4 Error Handling & Messages (45 min)

**Tasks**:
- [ ] Implement toast notifications or alert system
- [ ] Show clear error messages for:
  - Upload failures
  - Invalid trigger word
  - API failures
  - Export errors
- [ ] Add success messages for:
  - Successful upload
  - Captions generated
  - Export completed
- [ ] Style error/success messages distinctly

**Deliverable**: User-friendly error handling

---

## Phase 4: Vercel Deployment (2-3 hours)

**Goal**: Deploy to Vercel for student access

### 4.1 Vercel Configuration (1 hour)

**Tasks**:
- [ ] Create `vercel.json` configuration
- [ ] Refactor Flask routes for serverless functions
- [ ] Create `api/upload.py` (serverless function)
- [ ] Create `api/generate.py` (serverless function)
- [ ] Create `api/export.py` (serverless function)
- [ ] Test locally with Vercel CLI (`vercel dev`)

**Deliverable**: Vercel-compatible structure

**File Structure**:
```
api/
├── upload.py      # POST /api/upload
├── generate.py    # POST /api/generate
└── export.py      # POST /api/export
```

---

### 4.2 Handle Vercel Constraints (1 hour)

**Tasks**:
- [ ] Implement streaming for long-running caption generation
  - Vercel has 10-second timeout for serverless functions
  - Use Server-Sent Events (SSE) or chunked responses
- [ ] Handle `/tmp` storage properly
  - Store uploaded images in `/tmp`
  - Clean up after processing
- [ ] Test with 30+ images (ensure timeout doesn't occur)

**Deliverable**: Works within Vercel limitations

---

### 4.3 Deployment & Testing (1 hour)

**Tasks**:
- [ ] Push code to GitHub repository
- [ ] Connect GitHub repo to Vercel
- [ ] Configure environment variables in Vercel:
  - `GEMINI_API_KEY`
- [ ] Deploy to production
- [ ] Test deployed version:
  - Upload images
  - Generate captions
  - Edit captions
  - Export zip
- [ ] Fix any deployment-specific bugs
- [ ] Share URL with students (test access)

**Deliverable**: Live production deployment

**Vercel URL**: `https://image-metadata-generator.vercel.app` (or custom domain)

---

## Phase 5: Documentation & Final Polish (1-2 hours)

**Goal**: Professional, maintainable project

### 5.1 Documentation (1 hour)

**Tasks**:
- [ ] Complete `README.md` with:
  - Project description
  - Setup instructions (local)
  - Deployment instructions (Vercel)
  - Usage guide with screenshots
  - Troubleshooting section
- [ ] Add code comments for complex logic
- [ ] Create `docs/API_DESIGN.md` (API endpoint documentation)
- [ ] Add inline help text in UI (tooltips, placeholders)

**Deliverable**: Complete documentation

---

### 5.2 UI Polish (Optional - 30 min)

**Tasks**:
- [ ] Improve visual design (colors, spacing, typography)
- [ ] Add hover effects on buttons
- [ ] Smooth transitions and animations
- [ ] Responsive design improvements
- [ ] Add favicon

**Deliverable**: Polished user interface

---

### 5.3 Final Testing (30 min)

**Tasks**:
- [ ] Test all 6 datasets (ide_main_hall, ide_drawing_studio, etc.)
- [ ] Verify metadata.txt uploads successfully to Replicate
- [ ] Test on different browsers (Chrome, Firefox, Safari)
- [ ] Test on Vercel deployment
- [ ] Fix any final bugs

**Success Criteria**:
- All 6 datasets processed successfully
- Replicate accepts uploaded zip files
- No crashes or errors

---

## Optional Enhancements (Future Phases)

### Phase 6: Advanced Features (If Time Permits)

**Potential Features**:
- [ ] Keyboard shortcuts (arrow keys, Enter to save)
- [ ] Batch editing (apply same change to multiple captions)
- [ ] Search/filter images by caption text
- [ ] Caption templates/presets
- [ ] Dark mode toggle
- [ ] Export to CSV format
- [ ] Save/load projects (JSON export/import)
- [ ] Multi-language caption generation

**Estimated Time**: 4-6 hours for all features

---

## Development Workflow

### Daily Workflow

1. **Start of day**:
   - Review current phase tasks
   - Set goal (e.g., "Complete Phase 2.3 today")

2. **Development cycle** (per feature):
   - Write code
   - Manual test
   - Fix bugs
   - Commit to Git with clear message

3. **End of phase**:
   - Full end-to-end test
   - Demo to user (get feedback)
   - Adjust plan based on feedback

### Git Commit Strategy

**Commit messages**:
- `feat: Add Gemini API integration`
- `fix: Handle empty trigger word validation`
- `refactor: Extract image processing utilities`
- `docs: Update README with deployment steps`

**Branching** (optional for solo dev):
- `main` → production-ready code
- `dev` → active development
- Feature branches for major features

---

## Testing Strategy

### Manual Testing Checklist

**Phase 1 (MVP)**:
- [ ] Upload 5 images → Verify thumbnails appear
- [ ] Enter trigger word "test_space" → Verify validation
- [ ] Click "Generate Captions" → Wait for completion
- [ ] Check console for errors
- [ ] Export zip → Unzip and verify contents
- [ ] Open metadata.txt → Verify format

**Phase 2 (Editing)**:
- [ ] Click each thumbnail → Preview appears
- [ ] Edit caption → Verify auto-save
- [ ] Navigate with Previous/Next → Captions persist
- [ ] Edit indicator appears for edited captions

**Phase 3 (Export)**:
- [ ] Preview metadata.txt → Verify all captions included
- [ ] Export → Download successful
- [ ] Success message appears

**Phase 4 (Vercel)**:
- [ ] Upload on Vercel deployment → Works
- [ ] Generate captions → No timeout
- [ ] Export → Download works in browser

### Browser Testing

**Browsers to test**:
- Chrome (primary)
- Firefox
- Safari
- Edge (optional)

**Test cases per browser**:
- File upload
- Caption generation
- Zip download

---

## Risk Management

### Potential Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Gemini API rate limits exceeded | High | Medium | Add 2s delay, retry logic, test with small batches |
| Vercel timeout (10s limit) | High | High | Implement streaming responses, test early |
| Large images cause memory issues | Medium | Low | Resize before processing, set file size limits |
| Invalid image files crash app | Medium | Medium | Robust validation, error handling |
| API key exposed in code | High | Low | Use .env, add to .gitignore, verify before commit |
| Zip file too large for browser download | Low | Low | Warn if > 100MB, compress images (future) |

---

## Timeline Estimate

### Conservative Estimate (16 hours)

| Phase | Time | Cumulative |
|-------|------|------------|
| Phase 1: MVP | 5 hours | 5 hours |
| Phase 2: Editing | 4 hours | 9 hours |
| Phase 3: Export Polish | 3 hours | 12 hours |
| Phase 4: Vercel Deployment | 3 hours | 15 hours |
| Phase 5: Documentation | 1 hour | 16 hours |

### Optimistic Estimate (12 hours)

| Phase | Time | Cumulative |
|-------|------|------------|
| Phase 1: MVP | 4 hours | 4 hours |
| Phase 2: Editing | 3 hours | 7 hours |
| Phase 3: Export Polish | 2 hours | 9 hours |
| Phase 4: Vercel Deployment | 2 hours | 11 hours |
| Phase 5: Documentation | 1 hour | 12 hours |

**Recommended**: Plan for 14 hours, buffer for unexpected issues

---

## Success Criteria (Final Checklist)

### Functional Requirements
- [ ] Can upload 30+ images via browser
- [ ] Trigger word validation works correctly
- [ ] Captions generated for all images (< 5% failure rate)
- [ ] Can edit any caption and edits persist
- [ ] Export creates valid metadata.txt (UTF-8, LF line endings)
- [ ] Zip file contains all images + metadata.txt
- [ ] Zip uploads successfully to Replicate

### Non-Functional Requirements
- [ ] 30-image dataset processed in < 30 minutes
- [ ] UI is intuitive (no documentation needed for basic use)
- [ ] Works on Chrome, Firefox, Safari
- [ ] Deployed to Vercel and accessible via URL
- [ ] No crashes or unhandled errors during normal use
- [ ] API key secure (not in Git, not exposed to frontend)

### User Acceptance
- [ ] User successfully processes all 6 datasets
- [ ] Students can use Vercel deployment independently
- [ ] Trained LoRA models work as expected

---

## Next Steps

1. **Review this plan** with user
2. **Get approval** on approach and timeline
3. **Start Phase 1.1**: Project setup
4. **Iterate**: Build, test, demo, refine

**Development starts when approved by user.**

---

## Appendix: Technology Decisions

### Why Flask over FastAPI?
- Simpler for small project
- Better Vercel support (mature ecosystem)
- Fewer dependencies
- Easier to learn if user wants to modify later

### Why Vanilla JavaScript over React?
- No build step required
- Simpler deployment (just static files)
- Easier to understand for non-React users
- Sufficient for this UI complexity

### Why Gemini over Local Models?
- Superior caption quality (per user's testing)
- Free tier covers project needs
- No local GPU required
- Faster than running local inference

### Why No Database?
- Session-based workflow (single use per dataset)
- No need to persist data between sessions
- Simplifies deployment
- Reduces complexity

---

**Document Version**: 1.0
**Last Updated**: 2025-10-04
**Status**: Ready for Review
