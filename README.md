# Image Metadata Generator for LoRA Training

Automated caption generation tool for preparing image datasets for FLUX LoRA fine-tuning on Replicate.com.

**🌐 Live App**: https://idem307-image-metadata-generator.onrender.com/

**📖 Student Tutorial**: See [TUTORIAL.md](TUTORIAL.md) for step-by-step instructions

---

## Overview

This web application automates the time-consuming task of writing captions for image training datasets. It uses Google's Gemini vision AI to generate structured, consistent captions in the format required by Replicate.com for FLUX LoRA fine-tuning.

**Time savings**: Process 30 images in ~10 minutes (vs. 2-3 hours manually)

**Built for**: IDEM307 Generative AI and Design - TU Delft
**Developed by**: Prof. Gerd Kortuem with Claude Code
**Contact**: g.w.kortuem@tudelft.nl

---

## Quick Start (For Students)

### Using the Hosted Version (Easiest)

1. Go to: https://idem307-image-metadata-generator.onrender.com/
2. Upload 20-40 images from your dataset
3. Enter your trigger word (e.g., `ide_main_hall`)
4. Enter the access code provided by your instructor
5. Generate captions (takes ~18 seconds per image)
6. Download the training ZIP file
7. Upload to Replicate.com

**See [TUTORIAL.md](TUTORIAL.md) for detailed step-by-step instructions with screenshots.**

---

## Example Datasets

Practice with these example image datasets from TU Delft campus spaces:

- [IDE Drawing Studio](https://www.dropbox.com/scl/fi/a0a4qglv2xfd16hzdulnp/IDE-Drawing-Studio.zip?rlkey=uaoo41ldb8nnbgul8yn9er7m3&dl=0) (24 images)
- [IDE Lecture Hall](https://www.dropbox.com/scl/fi/c7r4pq0hct6539s3e8pe4/IDE-Lecture-Hall.zip?rlkey=ht5u3zvn7oo30svm2ps9gglrl&dl=0) (39 images)
- [IDE Main Hall](https://www.dropbox.com/scl/fi/hq8pvb85977d675yynrjf/IDE-Main-Hall.zip?rlkey=oi2zhq6ot0htq5ftogmllkn9w&dl=0) (39 images)
- [IDE Studio](https://www.dropbox.com/scl/fi/vgykhjs3o8okbd637vltr/IDE-Studio.zip?rlkey=x0sru5uw2ubi886vs2z2q6lp8&dl=0) (47 images)
- [SDE Hallway](https://www.dropbox.com/scl/fi/ihxy8f0bi7o3z87yr79ez/SDE-Hallway.zip?rlkey=3gzeys2z38autw3vyax2dutg2&dl=0) (38 images)

Download, extract, and use these to test the tool!

---

## Features

- 📁 **Batch Upload**: Upload 20-100 images via drag-and-drop
- 🤖 **AI Caption Generation**: Automated captions using Google Gemini 2.5 Pro
- ✏️ **Manual Editing**: Review and refine captions with image-by-image editor
- 📊 **Progress Tracking**: Real-time upload and generation progress
- 📦 **Replicate Export**: One-click export to Replicate-compatible ZIP format
- 🎨 **Clean UI**: Modern, responsive interface

---

## Output Format

The exported ZIP file is ready for Replicate.com FLUX LoRA training:

```
trigger_word_training.zip
├── image1.jpg
├── image1.txt          ← "photo of trigger_word description..."
├── image2.jpg
├── image2.txt          ← "photo of trigger_word description..."
└── ...
```

Each image has a matching `.txt` file with its caption in Replicate's required format:
```
photo of ide_main_hall entrance area, glass doors, high ceiling, natural daylight
```

---

## Running Locally (For Development)

### Prerequisites

- Python 3.9+
- Google Gemini API key ([Get free key](https://aistudio.google.com/))

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/kortuem/idem307-image-metadata-generator.git
cd idem307-image-metadata-generator
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

4. **Run the application**
```bash
python app.py
```

5. **Open in browser**
```
http://localhost:5001
```

---

## Deployment (Render.com)

The app is deployed on Render.com (free tier). See [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) for detailed deployment instructions.

**Why Render over Vercel:**
- ✅ Supports long-running processes (caption generation takes ~18s per image)
- ✅ Persistent sessions (no "Invalid session ID" errors)
- ✅ No timeout limits on free tier
- ✅ Works perfectly with Flask apps

---

## Technical Details

### Architecture

- **Backend**: Flask (Python)
- **AI Model**: Google Gemini 2.5 Pro vision API
- **Frontend**: Vanilla JavaScript (no frameworks)
- **Deployment**: Render.com (stateful, persistent)
- **Storage**: Session-based with base64 encoding for Vercel compatibility

### Gemini API

- **Model**: `gemini-2.5-pro` (best quality for image analysis)
- **Free tier**: 15 requests/minute, 1500/day
- **Rate limiting**: 2-second delay between requests (built-in)
- **Cost**: Free tier covers ~750 images/day

### Project Structure

```
image-metadata-generator/
├── app.py                    # Flask application & API endpoints
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (gitignored)
├── utils/                    # Backend utilities
│   ├── caption_generator.py  # Gemini AI integration
│   ├── image_processor.py    # Image validation & thumbnails
│   ├── validators.py         # Trigger word validation
│   └── metadata_exporter.py  # ZIP file creation
├── templates/
│   └── index.html           # Main application UI
├── static/
│   ├── css/styles.css       # Application styles
│   └── js/app.js            # Frontend JavaScript
├── TUTORIAL.md              # Student tutorial
└── RENDER_DEPLOYMENT.md     # Deployment guide
```

---

## Environment Variables

```bash
# Required: Your Gemini API key
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Secret access code for sharing
# Students can use this code instead of their own API key
SECRET_ACCESS_CODE=your_chosen_code
```

---

## Troubleshooting

### Common Issues

**"API key or access code required"**
- Enter your Gemini API key OR the access code provided by instructor
- Get free API key at: https://aistudio.google.com/

**Upload seems to hang**
- Check browser console (F12) for errors
- Hard refresh browser (Cmd+Shift+R / Ctrl+Shift+R)
- First deployment may take 30s to wake up (cold start)

**Captions not generating**
- Verify API key is valid
- Check you entered trigger word first
- Each image takes ~18 seconds to process

**"Invalid session ID" errors**
- Should not happen on Render deployment
- If occurs on Vercel, the platform doesn't support this app

---

## Version History

**v1.0** (January 2025)
- ✅ Initial production release
- ✅ Deployed on Render.com
- ✅ Full Replicate.com FLUX LoRA format support
- ✅ Upload progress tracking
- ✅ Base64 session storage for stateless platforms
- ✅ Secret access code sharing

---

## Credits

**Developed by**: Prof. Gerd Kortuem
**With**: Claude Code (Anthropic)
**Institution**: TU Delft, Faculty of Industrial Design Engineering
**Course**: IDEM307 Generative AI and Design
**Contact**: g.w.kortuem@tudelft.nl

**Powered by**:
- Google Gemini 2.5 Pro API
- Replicate.com FLUX LoRA training format
- Render.com (hosting)

---

## License

MIT License - Free to use for educational and personal projects.

---

**🌐 Live App**: https://idem307-image-metadata-generator.onrender.com/
**📖 Tutorial**: [TUTORIAL.md](TUTORIAL.md)
**🚀 Deploy Guide**: [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)
