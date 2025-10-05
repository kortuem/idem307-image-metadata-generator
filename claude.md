# Claude Project Instructions

> **Note**: This file contains AI assistant instructions for Claude Code.
> For project documentation, see [README.md](README.md) or [docs/](docs/).

---

## Project Status

**Status**: ✅ **PRODUCTION v1.0** - Deployed and in active use
**Live App**: https://idem307-image-metadata-generator.onrender.com/
**Repository**: https://github.com/kortuem/idem307-image-metadata-generator

**Purpose**: Flask web app for generating AI-powered image captions for LoRA training datasets. Built for TU Delft IDEM307 workshop students.

---

## Critical Rules (DO NOT BREAK)

### 1. Caption Format (CRITICAL)

**Required Replicate.com format**:
```
photo of [trigger_word] [description]
```

**Rules**:
- Literal "photo of " (lowercase, with space after)
- Then trigger_word (e.g., `ide_main_hall`)
- Space before description
- No trailing punctuation

**Never Accept**:
- ❌ `A photo of trigger_word...` (capital A)
- ❌ `Photo of trigger_word...` (capital P)
- ❌ `photo of trigger_word: description` (colon)
- ❌ `trigger_word description` (missing "photo of")

### 2. Export Format (CRITICAL)

**Replicate requires**: Individual .txt file per image
```
trigger_word_training.zip
├── image1.jpg
├── image1.txt    ← NOT a single metadata.txt file
├── image2.jpg
├── image2.txt
└── ...
```

### 3. Security

**Never commit**:
- `.env` file (contains real API keys)
- `static/uploads/*` (temporary files)

**Safe to commit**:
- `.env.example` (template only)
- All documentation
- Source code

---

## Development Principles

### 1. User-Centered
- **Primary users**: Non-technical students
- **Secondary user**: Instructor (technical but not Python expert)
- Clear error messages in plain language
- Works on first try (no complex setup required)

### 2. Reliability Over Features
- Better to do one thing well than many things poorly
- Don't break existing functionality
- Test locally before suggesting changes
- Graceful degradation (fallback models if primary fails)

### 3. Code Quality
- Clear variable names (`trigger_word`, not `tw`)
- Comments for non-obvious logic
- Modular functions (single responsibility)
- Use `pathlib` for cross-platform file paths
- Proper error handling with try/except

---

## Technical Constraints

### Stack
- **Backend**: Flask (Python 3.9+)
- **AI**: Google Gemini 2.5 Pro vision API
- **Frontend**: Vanilla JavaScript (no frameworks)
- **Deployment**: Render.com (free tier)
- **Session Storage**: Base64-encoded images in `/tmp/sessions/*.json`

### Why This Stack?
- **Flask**: Simple, flexible, well-understood
- **Gemini 2.5 Pro**: Best quality for image analysis (~18s per image acceptable)
- **Render**: Supports long processes, persistent sessions (Vercel failed - stateless)
- **Base64 in JSON**: Simplifies stateless/serverless architecture

### API Configuration
- Model: `gemini-2.5-pro` (with fallback chain)
- Rate limit: 2s delay between requests
- Free tier: 1,500 req/day (sufficient for ~750 images)
- Auth: `GEMINI_API_KEY` + `SECRET_ACCESS_CODE` env vars

---

## Communication Guidelines

### When Making Changes

✅ **Do**:
- Provide complete, working code (not pseudocode)
- Test changes locally before suggesting
- Explain trade-offs when multiple approaches exist
- Update documentation if architecture changes
- Show examples of expected output

❌ **Don't**:
- Break existing functionality
- Change caption format (breaks Replicate compatibility)
- Remove error handling
- Add dependencies without discussing
- Make assumptions about user's environment

### When User Reports Issues

1. **Reproduce** locally if possible
2. **Check logs** (terminal or Render dashboard)
3. **Identify root cause** before suggesting fixes
4. **Provide complete fix** (don't leave half-done)
5. **Test the fix** before pushing to production

---

## User Profile

**Prof. Gerd Kortuem**:
- Technical but not Python expert
- Values reliability > features
- Teaching workshop (6 datasets, ~180 images total)
- Tool saves 12-18 hours of manual work
- Quality matters (teaching materials)

**Students** (indirect users):
- Non-technical
- Need simple, working tool
- Process 20-40 images each
- Upload results to Replicate.com

---

## Project Documentation

For detailed technical information, see:

- **[README.md](README.md)** - Project overview and quick start
- **[TUTORIAL.md](TUTORIAL.md)** - Step-by-step student guide
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Technical architecture
- **[docs/DEPLOYMENT-RENDER.md](docs/DEPLOYMENT-RENDER.md)** - Deployment guide
- **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Developer workflow

---

**Last Updated**: January 2025 (v1.0)
