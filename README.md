# Image Metadata Generator for LoRA Training

Automated caption generation tool for preparing image datasets for LoRA fine-tuning on Replicate.com.

## Overview

This web application automates the time-consuming task of writing captions for image training datasets. It uses Google's Gemini vision AI to generate structured, consistent captions, then allows manual editing for quality control.

**Time savings**: Process 30 images in 20-30 minutes (vs. 2-3 hours manually)

## Features

- 📁 **Batch Upload**: Upload 20-100 images via drag-and-drop or file selection
- 🤖 **AI Caption Generation**: Automated captions using Google Gemini vision API
- ✏️ **Manual Editing**: Review and refine captions with intuitive image editor
- 📊 **Progress Tracking**: Real-time progress indicators and debug console
- 📦 **Replicate Export**: One-click export to Replicate-compatible zip format
- 🎨 **Clean UI**: Modern, responsive interface with keyboard shortcuts

## Quick Start

### Prerequisites

- Python 3.9+
- Google Gemini API key ([Get one here](https://ai.google.dev/))

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd image-metadata-generator
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Get a Gemini API Key**
   - Go to [Google AI Studio](https://aistudio.google.com/)
   - Sign in with your Google account
   - Click "Get API Key" → "Create API Key"
   - Copy your API key

4. **Configure environment** (optional - for shared deployments only)
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
# Optionally add SECRET_ACCESS_CODE if you want to share access with others
```

5. **Run the application**
```bash
python app.py
```

6. **Open in browser**
```
http://localhost:5000
```

## Usage

### Step-by-Step Workflow

1. **Upload Images**
   - Click upload area or drag-and-drop 20-40 JPG/PNG images
   - Images are validated and thumbnails generated

2. **Enter Trigger Word**
   - Type your trigger word (e.g., `ide_main_hall`, `ide_person`)
   - Must be lowercase, underscores only, no spaces

3. **Enter API Key**
   - Enter your Gemini API key (from [Google AI Studio](https://aistudio.google.com/))
   - Or use provided access code (if deployer shared one with you)

4. **Generate Captions**
   - Click "Generate Captions"
   - Wait 2-3 minutes for batch processing (~2s per image)

5. **Review & Edit**
   - Click thumbnails to navigate images
   - Edit captions in the textarea
   - Changes auto-save
   - Use arrow keys for quick navigation

6. **Export**
   - Click "Preview metadata.txt" to review final output
   - Click "Export Training Zip" to download
   - Upload zip file to Replicate

### Output Format

The exported zip file contains:
```
trigger_word_training.zip
├── IMG_001.jpg
├── IMG_002.jpg
├── ...
└── metadata.txt
```

**metadata.txt** format (one line per image):
```
photo of ide_main_hall entrance area, glass doors, high ceiling, natural daylight
photo of ide_main_hall corridor view, seating areas, modern lighting fixtures
photo of ide_main_hall staircase detail, metal railings, concrete steps
```

## Configuration

### Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Secret access code (for shared deployments)
# If set, users can enter this code instead of their own API key
# Choose your own unique code (e.g., "myclass2024")
SECRET_ACCESS_CODE=your_chosen_secret_code

# Optional: Flask settings
FLASK_ENV=development
FLASK_DEBUG=True
MAX_FILE_SIZE_MB=10
MAX_TOTAL_UPLOAD_MB=100
```

**Getting a Gemini API Key:**
1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Sign in with Google account
3. Click "Get API Key" → "Create API Key"
4. Copy and paste into `.env` file

### Gemini API

- **Model used**: `gemini-2.5-pro` (with fallbacks to 2.5-flash → 2.0-flash-exp → 1.5-pro → 1.5-flash)
- **Free tier limits**: 15 requests/minute, 1500/day
- **Rate limiting**: 2-second delay between requests (built-in)
- **Cost**: Free tier covers ~180 images easily

## Development

### Project Structure

```
image-metadata-generator/
├── app.py                 # Flask application
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (gitignored)
├── docs/                  # Documentation
│   ├── SPECIFICATION.md
│   ├── DEVELOPMENT_PLAN.md
│   └── API_DESIGN.md
├── utils/                 # Backend utilities
│   ├── caption_generator.py
│   ├── image_processor.py
│   ├── validators.py
│   └── metadata_exporter.py
├── templates/             # HTML templates
│   └── index.html
├── static/                # Frontend assets
│   ├── css/styles.css
│   ├── js/app.js
│   └── uploads/           # Temporary image storage
└── PROJECT_BRIEF.md       # Original requirements
```

### Running Tests

Manual testing checklist:

1. Upload 5 test images
2. Enter trigger word "test_space"
3. Generate captions (wait ~10 seconds)
4. Edit 2 captions manually
5. Preview metadata.txt
6. Export zip and verify contents

### Debug Console

The built-in debug console shows:
- 🔵 **INFO**: Normal operations (uploads, processing)
- 🟢 **SUCCESS**: Completed operations (captions generated)
- 🟡 **WARNING**: Non-critical issues (retries, rejections)
- 🔴 **ERROR**: Failures (API errors, validation failures)

Toggle with the "Debug Console" button at the bottom.

## Deployment (Vercel)

### Prerequisites

- GitHub repository
- Vercel account (free tier works)

### Steps

1. **Push to GitHub**
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

2. **Connect to Vercel**
   - Go to [Vercel Dashboard](https://vercel.com)
   - Import GitHub repository
   - Framework preset: "Other"

3. **Configure Environment Variables**
   - In Vercel project settings → Environment Variables
   - Add: `GEMINI_API_KEY` = your_gemini_api_key (from [Google AI Studio](https://aistudio.google.com/))
   - Add: `SECRET_ACCESS_CODE` = your_chosen_secret_code (optional - for sharing with students/users)

4. **Deploy**
   - Vercel auto-deploys on every push to main
   - Share URL with students: `https://your-project.vercel.app`

### Vercel Notes

- Files uploaded to `/tmp` (temporary storage, auto-deleted)
- 10-second function timeout (handled with proper response streaming)
- No persistent database needed (session-based)

## Troubleshooting

### Common Issues

**"GEMINI_API_KEY not found"**
- Check `.env` file exists and contains `GEMINI_API_KEY=your_key`
- Restart Flask server after adding key

**"Rate limit exceeded"**
- Gemini free tier: 15 req/min
- App adds 2s delay automatically
- Wait 60 seconds and retry

**"Image validation failed"**
- Only JPG, JPEG, PNG supported
- Max file size: 10MB per image
- Check image isn't corrupted (try opening in image viewer)

**Captions not generating**
- Check debug console for API errors
- Verify API key is valid
- Check internet connection

**Upload fails on large batches**
- Max total upload: 100MB
- Max 100 images per session
- Split into smaller batches if needed

### Getting Help

- Check [docs/SPECIFICATION.md](docs/SPECIFICATION.md) for technical details
- Check [docs/API_DESIGN.md](docs/API_DESIGN.md) for endpoint documentation
- Review debug console logs for error messages

## Roadmap

### Completed ✅
- ✅ Image upload and validation
- ✅ Gemini API integration
- ✅ Automated caption generation
- ✅ Caption editing interface
- ✅ Metadata export to Replicate format
- ✅ Debug console

### Future Enhancements 🚀
- 🔜 Keyboard shortcuts (arrow keys implemented)
- 🔜 Batch caption editing
- 🔜 Caption templates/presets
- 🔜 Save/load projects
- 🔜 Multi-language support
- 🔜 Local vision models (offline mode)

## License

MIT License - Use freely for educational and personal projects.

## Credits

Developed by **Prof. Gerd Kortuem** with **Claude Code**
TU Delft, Faculty of Industrial Design Engineering
Contact: [g.w.kortuem@tudelft.nl](mailto:g.w.kortuem@tudelft.nl)

**Built for**: IDEM307 Generative AI and Design - TU Delft
**Powered by**: Google Gemini 2.5 Pro API
**Designed for**: Replicate.com FLUX LoRA fine-tuning

---

**Version**: 2.0.0
**Last Updated**: October 2025
