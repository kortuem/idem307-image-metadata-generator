# Image Metadata Generator for LoRA Training

**Developed by**: Prof. Gerd Kortuem with Claude Code  
**Institution**: TU Delft, Faculty of Industrial Design Engineering  
**Contact**: g.w.kortuem@tudelft.nl

---

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
3. Select image category (Interior, Person, Object, etc.)
4. Enter semantic context (e.g., `TU Delft drawing studio`)
5. Enter the access code provided by your instructor
6. Generate captions (takes ~5-10 seconds per image)
7. Download the training ZIP file
8. Upload to Replicate.com

**See [TUTORIAL.md](TUTORIAL.md) for detailed step-by-step instructions with screenshots.**

---

## Example Datasets

**Repository datasets**: Example image datasets from TU Delft campus spaces are included in the repository at `__images/data sets/`:

- IDE Drawing Studio (24 images)
- IDE Lecture Hall (39 images)
- IDE Main Hall (39 images)
- IDE Studio (47 images)
- SDE Hallway (38 images)

**Note**: These datasets are tracked in the repository for development/testing purposes. The `__images/` directory may also contain zipped training-ready datasets with generated captions.

**For workshop students**: Download the original datasets from Dropbox (links provided by instructor) or use your own images.

---

## Features

- 📁 **Batch Upload**: Upload 20-100 images via drag-and-drop (max 10MB/image, 100MB total)
- 🎯 **8 Image Categories**: Interior, Person, People/Groups, Object, Vehicle, Exterior, Scene, Abstract
- 🤖 **AI Caption Generation**: Automated captions using Google Gemini 2.5 Flash
- ✏️ **Manual Editing**: Review and refine captions with image-by-image editor
- 📊 **Progress Tracking**: Real-time upload and generation progress
- 🐢 **Slow Mode**: Optional 3s delay for rate limiting or high server load
- 📦 **Replicate Export**: One-click export to Replicate-compatible ZIP format
- 🎨 **Clean UI**: Modern, responsive interface

---

## Output Format

The exported ZIP file is ready for Replicate.com FLUX LoRA training:

```
semantic_context_training.zip
├── image1.jpg
├── image1.txt          ← Semantic context + detailed description
├── image2.jpg
├── image2.txt          ← Semantic context + detailed description
└── ...
```

Each image has a matching `.txt` file with a structured caption:
```
TU Delft drawing studio with high vaulted ceilings and skylights, rows of white
adjustable drawing tables with wooden stools, dark flooring, translucent partition
walls, abundant natural light complemented by fluorescent fixtures creating bright
functional workspace
```

**Note**: Replicate automatically adds your trigger word during training. You don't include it in captions.

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

The app is deployed on Render.com. See [docs/DEPLOYMENT-RENDER.md](docs/DEPLOYMENT-RENDER.md) for detailed deployment instructions.

**Why Render over Vercel:**
- ✅ Supports long-running processes (caption generation takes ~18s per image)
- ✅ Persistent sessions (no "Invalid session ID" errors)
- ✅ No timeout limits on free tier
- ✅ Works perfectly with Flask apps

### Scalability & Capacity

**Current Configuration** (Workshop Ready):
- **Render Plan**: Hobby ($7/mo) + Standard Instance ($25/mo)
- **Capacity**: 30 concurrent students
- **RAM**: 2GB (30 sessions × ~80MB each)
- **Auto-cleanup**: Sessions deleted after ZIP export

**Slow Mode**: Students can enable 3s delay if server is overloaded or API rate limits are hit.

---

## Technical Details

### Architecture

- **Backend**: Flask (Python)
- **AI Model**: Google Gemini 2.5 Flash vision API
- **Frontend**: Vanilla JavaScript (no frameworks)
- **Deployment**: Render.com (Hobby plan + Standard instance)
- **Storage**: File-based sessions with base64 encoding

For detailed architecture information, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

### Gemini API

- **Model**: `gemini-2.5-flash` (fast, cost-effective, good quality)
- **Paid Tier 1**: 1,000 requests/minute
- **Rate limiting**: 0.1s delay (or 3s in slow mode)
- **Cost**: ~$2.93 for 30 students × 30 images (vs $11.80 with Pro model)

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
├── docs/                    # Documentation
│   ├── ARCHITECTURE.md      # Technical architecture
│   ├── DEPLOYMENT-RENDER.md # Deployment guide
│   └── DEVELOPMENT.md       # Developer workflow
├── TUTORIAL.md              # Student tutorial
├── README.md                # This file
└── claude.md                # Claude Code instructions
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

**v1.0** (October 2025)
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

## Documentation

- **[README.md](README.md)** - Project overview (this file)
- **[TUTORIAL.md](TUTORIAL.md)** - Step-by-step student guide
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Technical architecture
- **[docs/DEPLOYMENT-RENDER.md](docs/DEPLOYMENT-RENDER.md)** - Deployment guide
- **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Developer workflow
- **[docs/RATE_LIMITING.md](docs/RATE_LIMITING.md)** - Scalability & rate limiting

---

**🌐 Live App**: https://idem307-image-metadata-generator.onrender.com/
**📖 Tutorial**: [TUTORIAL.md](TUTORIAL.md)
**🚀 Deploy Guide**: [docs/DEPLOYMENT-RENDER.md](docs/DEPLOYMENT-RENDER.md)
