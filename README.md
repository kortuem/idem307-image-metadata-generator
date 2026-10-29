# Image Metadata Generator for LoRA Training

> Automated caption generation for FLUX LoRA fine-tuning datasets using Google Gemini vision AI

**🌐 Live App**: https://idem307-image-metadata-generator.onrender.com/
**📖 Tutorial**: [TUTORIAL.md](TUTORIAL.md) - Step-by-step student guide
**🔧 Deploy Guide**: [docs/DEPLOYMENT-RENDER.md](docs/DEPLOYMENT-RENDER.md)

**By Prof. Gerd Kortuem** - TU Delft, Faculty of Industrial Design Engineering
Built for **[IDEM307 Generative AI and Design](https://studiegids.tudelft.nl/courses/study-guide/educations/12452)**

**Maintenance review**: October 2026. This is a historical teaching tool with targeted safety fixes. Current hosting availability, support and workshop capacity are unverified. The documentation below includes October 2025 workshop records; they are not current deployment guarantees.

---

## Overview

This web application automates the time-consuming task of writing captions for image training datasets. Upload 20-100 images, and it generates structured, detailed captions using Google's Gemini vision AI - formatted for Replicate.com FLUX LoRA training.

**What it does:**
1. Upload images via drag-and-drop
2. Select image category (Interior, Person, Object, etc.)
3. Enter semantic context (e.g., "TU Delft drawing studio")
4. AI generates unique captions for each image (~8-12 seconds per image)
5. Export ZIP file ready for Replicate.com

**Output format:**
```
semantic_context_training.zip
├── image1.jpg
├── image1.txt    ← "TU Delft drawing studio with vaulted ceilings..."
├── image2.jpg
├── image2.txt    ← "TU Delft drawing studio featuring exposed beams..."
└── ...
```

---

## Quick Start

### For Students (Hosted Version)

1. Go to https://idem307-image-metadata-generator.onrender.com/
2. Upload 20-40 images
3. Select category and enter semantic context
4. Enter access code from instructor (or your own Gemini API key)
5. Generate captions and download ZIP
6. Upload ZIP to Replicate.com

**See [TUTORIAL.md](TUTORIAL.md) for detailed instructions with screenshots.**

### For Developers (Local Setup)

```bash
# Clone repository
git clone https://github.com/kortuem/idem307-image-metadata-generator.git
cd idem307-image-metadata-generator

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add GEMINI_API_KEY

# Run locally
python app.py
# Open http://localhost:5001
```

**See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for developer workflow.**

---

## Features

- 📁 **Batch Upload**: 20-100 images via drag-and-drop (max 10MB/image)
- 🎯 **8 Image Categories**: Interior, Person, People, Object, Vehicle, Exterior, Scene, Abstract
- 🤖 **AI Captions**: Google Gemini 2.5 Flash vision API
- ✏️ **Edit Mode**: Review and refine captions image-by-image
- 📊 **Progress Tracking**: Real-time upload and generation progress
- 🐢 **Slow Mode**: Optional 3s delay for rate limiting
- 📦 **Replicate Export**: One-click ZIP export in Replicate format
- 🎨 **Clean UI**: Modern, responsive interface

---

## Example Datasets

Example datasets from TU Delft campus spaces are included in `__images/image data sets/`:

- [IDE Drawing Studio](https://github.com/kortuem/idem307-image-metadata-generator/tree/main/__images/image%20data%20sets/IDE%20Drawing%20Studio) (24 images)
- [IDE Lecture Hall](https://github.com/kortuem/idem307-image-metadata-generator/tree/main/__images/image%20data%20sets/IDE%20Lecture%20Hall) (39 images)
- [IDE Main Hall](https://github.com/kortuem/idem307-image-metadata-generator/tree/main/__images/image%20data%20sets/IDE%20Main%20Hall) (39 images)
- [IDE Studio](https://github.com/kortuem/idem307-image-metadata-generator/tree/main/__images/image%20data%20sets/IDE%20Studio) (47 images)
- [SDE Hallway](https://github.com/kortuem/idem307-image-metadata-generator/tree/main/__images/image%20data%20sets/SDE%20Hallway) (38 images)

Browse [historical captioned examples](https://github.com/kortuem/idem307-image-metadata-generator/tree/main/__images/fine-tuning%20data%20sets) to see the historical output format. Dataset reuse permissions remain unverified; see [RIGHTS.md](RIGHTS.md).

---

## Technical Stack

- **Backend**: Flask (Python 3.9+)
- **AI Model**: Google Gemini 2.5 Flash vision API
- **Frontend**: Vanilla JavaScript
- **Deployment**: Render.com
- **Storage**: File-based sessions with base64 encoding

**Historical workshop claim**: 40 concurrent uploads and 30 students. Not repeated in this maintenance review; in-memory tracking is not a reliable global limit across workers.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed technical architecture.

---

## Documentation

| Document | Description |
|----------|-------------|
| **[TUTORIAL.md](TUTORIAL.md)** | Step-by-step student guide |
| **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** | Technical architecture |
| **[docs/DEPLOYMENT-RENDER.md](docs/DEPLOYMENT-RENDER.md)** | Deployment guide |
| **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)** | Developer workflow |
| **[docs/WORKSHOP_CAPACITY.md](docs/WORKSHOP_CAPACITY.md)** | Capacity testing results |

---

## Configuration

### Environment Variables

```bash
# Required: Your Gemini API key
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Secret access code for students
SECRET_ACCESS_CODE=your_chosen_code

# Optional: Session limit (default: 30)
MAX_CONCURRENT_SESSIONS=100
```

Get a free Gemini API key at https://aistudio.google.com/

### Deployment

The app is deployed on Render.com. Key configuration:

- **Gunicorn**: `--workers 4 --threads 4 --timeout 300`
- **Historical capacity claim**: 40+ concurrent uploads (not reverified)
- **Memory**: ~1-15 MB per session

See [docs/DEPLOYMENT-RENDER.md](docs/DEPLOYMENT-RENDER.md) for complete deployment instructions.

---

## Troubleshooting

**"API key or access code required"**
- Enter your Gemini API key OR the access code from instructor
- Get free key at https://aistudio.google.com/

**Upload seems to hang**
- First load may take 30s (server cold start)
- Hard refresh browser (Cmd+Shift+R / Ctrl+Shift+R)
- Check browser console (F12) for errors

**Captions not generating**
- Verify API key is valid
- Each image takes ~8-12 seconds
- Check semantic context is entered

---

## Version History

**v2.0** (October 2025) - Production Release
- ✅ Semantic context instead of trigger words
- ✅ 8 image categories with specialized prompts
- ✅ Gemini 2.5 Flash (faster, cost-effective)
- ✅ Individual caption generation (real-time progress)
- ✅ Session recovery from disk
- ✅ Deployed on Render.com

**v1.0** (October 2025) - Initial Release
- ✅ Batch caption generation
- ✅ Gemini 2.5 Pro vision API
- ✅ Base64 session storage

---

## Privacy & Copyright

**Important Notices:**
- **Copyright**: Only upload images you own or have permission to use
- **Consent**: If images contain identifiable people, obtain their consent first
- **Data processing**: Images, prompts and personal API keys pass through this server; images/prompts are sent to Google. Provider retention and billing are separate from this app.
- **Storage**: Sessions contain base64 images and captions in files or Redis. Successful export and explicit deletion attempt removal through the configured backend. Redis sessions expire 24 hours after the last save. File cleanup runs during activity and is not a guaranteed scheduled deletion service; failures, backups and abandoned files can retain data.
- **Session identifiers**: Treat them as bearer secrets. Anyone holding an identifier can access that session. The app does not provide per-user account authorization.
- **Deployment limitation**: The legacy Gemini SDK uses global credential configuration. Mixed personal/shared keys with concurrent workers/threads need a dedicated isolation review before shared public use.

**Use responsibly and respect privacy rights.**

---

## License

Original tool code and technical documentation use the [MIT License](LICENSE), including commercial reuse under its terms. The datasets in `__images/**` are excluded; see [RIGHTS.md](RIGHTS.md).

**Contact**: g.w.kortuem@tudelft.nl

## Offline maintenance checks

```sh
python -m unittest discover -s tests -p test_session_safety.py -v
node --test tests/capacity-ui.test.cjs
```

These tests use temporary directories and mock the caption provider and Redis. They do not validate Google's API or real Redis service availability. Older stress-test scripts may contact a deployed app and incur costs; they are not part of this check.

The development server binds to `127.0.0.1` with debug disabled. `UPLOAD_FOLDER` and `SESSION_FOLDER` can isolate storage for local checks. `GEMINI_MODEL` selects a model (default `gemini-2.5-flash`); model construction does not establish API access. Retired fallback model names have been removed.
