# Image Dataset Metadata Generator for LoRA Training

## Project Context

This tool prepares image datasets for fine-tuning image generation models using LoRA (Low-Rank Adaptation) on Replicate.com. The tool is needed for a university workshop (IDEM307 at TU Delft) where students learn to create custom image generation models.

### Problem Statement

Training LoRA models requires structured metadata for each image. Manually writing 20-40 captions per dataset is time-consuming and inconsistent. This tool automates initial caption generation using vision AI, then allows manual refinement for quality control.

### Use Case

**I have 6 image datasets**:
- 5 campus space datasets (24-40 images each): ide_drawing_studio, ide_lecture_hall, ide_main_hall, ide_studio, sde_hallway
- 1 person dataset: ide_person (24-40 images)

**Each needs**:
- Structured captions following specific format
- Consistent trigger word prefix
- metadata.txt file with one caption per image
- Zip file containing images + metadata.txt for upload to Replicate

### Current Workflow (Manual - Too Slow)

1. Open each image individually
2. Write caption: "photo of [trigger_word] [description]"
3. Ensure consistency across all captions
4. Compile into metadata.txt
5. Zip images + metadata.txt

**Time per dataset**: 2-3 hours

### Desired Workflow (Automated)

1. Select image folder
2. Enter trigger word (e.g., "ide_main_hall")
3. Auto-generate captions using vision AI
4. Review and edit captions as needed
5. Export metadata.txt + zip file

**Time per dataset**: 20-30 minutes

---

## Technical Requirements

### Technology Stack

**Requirement**: Web application OR standalone Python (NOT Streamlit)

**Options**:

**Option A - Web App (Preferred for Vercel deployment)**:
- Frontend: HTML/CSS/JavaScript (vanilla or React)
- Backend: Python Flask or FastAPI
- Deployment: Can run locally during development, deploy to Vercel if needed
- File handling: Upload via web interface

**Option B - Standalone Python**:
- UI: tkinter (native desktop GUI)
- No server needed
- Runs entirely locally
- Direct file system access

**Choose the approach that makes most sense for the requirements.**

### Core Functionality

#### 1. Image Selection
- Browse filesystem to select folder containing images
- Support formats: JPG, JPEG, PNG
- Display image count and thumbnails
- Validate all files are readable images

#### 2. Trigger Word Input
- Text input field for trigger word
- Validation: lowercase, underscores for spaces (no hyphens, no spaces)
- Examples: "ide_main_hall", "ide_drawing_studio", "ide_person"
- This becomes the consistent prefix for ALL captions

#### 3. Automated Caption Generation

**Vision Model**: Use Google Gemini API (I have API key)

**Why Gemini over local models**: 
- Superior quality for structured captions
- Follows format instructions precisely
- Free tier covers entire project (~180 images)
- Better understanding of spatial/architectural concepts
- Can emphasize specific details (lighting, materials, layout)

**Caption Format Required**:
```
photo of [trigger_word] [room_type], [key_objects], [lighting], [contextual_details]
```

**Examples**:
```
photo of ide_main_hall entrance area, glass doors, high ceiling, natural daylight streaming in, open circulation space
photo of ide_drawing_studio workspace, large tables, task lighting, drawing materials scattered, students working, afternoon light
photo of ide_lecture_hall tiered seating, rows of desks, projection screen at front, overhead fluorescent lighting, teaching space
photo of ide_person standing, casual clothing, neutral expression, soft natural lighting, plain background
```

**Vision AI Prompt Template**:
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

**Batch Processing**:
- Process all images in folder sequentially
- Show progress (X of Y images processed)
- Handle API rate limits gracefully (wait/retry with exponential backoff)
- Log any failures with error messages
- Continue processing if one image fails (don't crash entire batch)

#### 4. Manual Editing Interface

**Requirements**:
- Display all images with their captions
- Allow editing any caption
- Visual distinction between auto-generated and manually-edited captions
- Navigation: previous/next, or click any image
- Save edits immediately (no "save" button needed)
- Preview of final metadata.txt format

**UI Layout Suggestion**:
```
┌─────────────────────────────────────────┐
│ Folder: /path/to/images     [Select]   │
│ Trigger Word: [ide_main_hall____]      │
│                [Generate Captions]      │
├─────────────────────────────────────────┤
│ ┌────┐ ┌────┐ ┌────┐ ┌────┐           │
│ │img1│ │img2│ │img3│ │img4│  (thumbs) │
│ └────┘ └────┘ └────┘ └────┘           │
├─────────────────────────────────────────┤
│ [Full Size Image Preview]              │
│                                         │
│ Caption:                                │
│ ┌─────────────────────────────────────┐│
│ │photo of ide_main_hall entrance...   ││
│ │                                     ││
│ └─────────────────────────────────────┘│
│ [< Previous]  [Next >]                 │
├─────────────────────────────────────────┤
│        [Export metadata.txt + Zip]     │
└─────────────────────────────────────────┘
```

#### 5. Export Functionality

**Generate metadata.txt**:
- One line per image
- Order matches alphabetical image filename order
- Format: `photo of [trigger_word] [caption]`
- UTF-8 encoding
- Unix line endings (LF)

**Create zip file**:
- Name: `[trigger_word]_training.zip`
- Contains: all original images + metadata.txt
- Preserve original image filenames
- Save to user-selected location or same directory as images

**Example metadata.txt**:
```
photo of ide_main_hall entrance area, glass doors, high ceiling, natural daylight, open circulation space
photo of ide_main_hall corridor view, seating areas, modern lighting fixtures, students visible, collaborative atmosphere
photo of ide_main_hall staircase detail, metal railings, concrete steps, industrial aesthetic, architectural feature
```

**Example zip structure**:
```
ide_main_hall_training.zip
├── IMG_001.jpg
├── IMG_002.jpg
├── IMG_003.jpg
├── ...
└── metadata.txt
```

---

## Technical Specifications

### Required Python Libraries

```
google-generativeai  # Gemini API
pillow              # Image handling
flask               # Web framework (if web app)
# OR
tkinter             # GUI (if standalone Python - comes with Python)
```

### API Configuration

**Gemini API**:
- API key provided via environment variable: `GEMINI_API_KEY`
- Model: `gemini-2.0-flash-exp` or `gemini-1.5-flash` (try newest available)
- Rate limits: ~15 requests/minute on free tier
- Implement retry logic with exponential backoff
- Recommended: 2-second delay between requests to avoid rate limits

**API Call Example**:
```python
import google.generativeai as genai
from PIL import Image
import os

genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-2.0-flash-exp')

image = Image.open('photo.jpg')
prompt = "Analyze this interior space..."
response = model.generate_content([prompt, image])
caption = response.text
```

### Deployment Options

**Local Development**:
- Run Python script/server locally
- Access via localhost
- Direct file system access

**Vercel Deployment** (optional, if web app):
- Flask/FastAPI backend as serverless functions
- Frontend served as static files
- Environment variable for GEMINI_API_KEY
- Note: File uploads on Vercel are temporary (stored in /tmp)

### Image Handling

**Considerations**:
- Resize large images before API call (max 4MB recommended)
- Maintain aspect ratio
- Convert to RGB if necessary (some PNGs have alpha channel)
- Don't modify original files

### Error Handling

**Must handle**:
- Invalid image files (corrupted, wrong format)
- API failures (rate limits, network errors, invalid key)
- Empty folders
- Invalid trigger words (spaces, special characters)
- Duplicate filenames
- Missing GEMINI_API_KEY environment variable

**User feedback required**:
- Clear error messages
- Progress indication during batch processing
- Success confirmation with file location
- Warning if metadata.txt already exists (overwrite prompt)

---

## Development Approach

### Phase 1: Core Functionality (MVP)
1. Choose architecture (web app or standalone)
2. Folder selection / file upload
3. Trigger word input with validation
4. Gemini API integration
5. Single image caption generation (test)
6. Batch caption generation with progress
7. Export metadata.txt

**Target**: Working end-to-end for metadata.txt generation

### Phase 2: Editing Interface
8. Display images as thumbnail grid
9. Click image to view full size
10. Display caption below image
11. Edit caption functionality
12. Save edits to data structure
13. Navigate previous/next

**Target**: Can review and edit all captions

### Phase 3: Export Enhancement
14. Create zip file with images + metadata
15. File saving/download
16. Export validation
17. Success message with file location

**Target**: Complete workflow from folder to zip file

### Phase 4: Polish
18. Progress indicators with percentages
19. Better error messages
20. UI improvements (styling, layout)
21. Keyboard shortcuts (optional)

---

## Success Criteria

**The tool is successful if**:
1. I can process a 30-image dataset in < 30 minutes (vs. 2-3 hours manual)
2. Auto-generated captions are 80%+ accurate (minimal editing needed)
3. Output metadata.txt works perfectly with Replicate (correct format)
4. Tool handles all 6 datasets without crashes
5. UI is intuitive (no documentation needed for basic use)
6. Captions follow consistent format across all images
7. Export zip file uploads successfully to Replicate
8. Can run locally without complex setup

---

## Example Usage Session

```
1. Launch application
   - Web app: python app.py → open http://localhost:5000
   - OR standalone: python metadata_generator.py
2. Select folder: /datasets/ide_main_hall/ (or upload files if web)
3. Enter trigger word: "ide_main_hall"
4. Click "Generate Captions"
   → Progress: Processing image 1 of 32...
   → Progress: Processing image 2 of 32...
   [... 2-3 minutes with rate limiting ...]
   → Complete! 32 captions generated.
5. Review captions:
   → Click through images
   → Edit ~20% that need refinement
6. Click "Export"
   → metadata.txt created ✓
   → ide_main_hall_training.zip created ✓
   → Downloaded/saved to specified location ✓
7. Success! Ready to upload to Replicate.
```

---

## Caption Quality Guidelines

**Good captions** are:
- Specific (not "a room" but "lecture hall")
- Objective (describe what's visible, not interpretation)
- Consistent in structure across dataset
- Include lighting information
- Mention key spatial features
- Appropriate detail level (not too brief, not exhaustive)

**Examples of good vs. poor captions**:

❌ Poor: "nice room with furniture"
✅ Good: "lecture hall, tiered seating, projection screen, overhead lighting, teaching space"

❌ Poor: "someone standing around"
✅ Good: "standing, casual clothing, neutral expression, soft natural lighting, plain background"

❌ Poor: "ide_drawing_studio with lots of stuff everywhere"
✅ Good: "workspace, large tables, task lighting, drawing materials scattered, students working, afternoon light"

---

## Getting Started

**Your first steps**:
1. Decide on architecture: web app (Flask) or standalone Python (tkinter)
2. Ask me which approach I prefer if unclear
3. Create simple prototype: folder selection + single image caption generation
4. Show me the output to verify caption quality
5. Iterate based on feedback

**I will provide**:
- Gemini API key as environment variable
- Sample images for testing (3-5 images)
- Feedback on caption quality and format
- UI/UX preferences as you develop

**Development philosophy**: Start simple, show working code early, iterate based on feedback.

Let's build this tool step by step!
