# Claude Project Instructions

> **Note**: This file contains AI assistant instructions for Claude Code.
> For project documentation, see [README.md](README.md) or [docs/](docs/).

---

## Project Status

**Status**: 🚧 **UPGRADING to v2.0** - Interior category MVP
**Live App**: https://idem307-image-metadata-generator.onrender.com/ (v1.0)
**Repository**: https://github.com/kortuem/idem307-image-metadata-generator

**Purpose**: Flask web app for generating AI-powered image captions for LoRA training datasets. Built for TU Delft IDEM307 workshop students.

---

## Critical Rules (v2.0 - DO NOT BREAK)

### 1. Caption Format (UPDATED)

**New format** (Replicate adds trigger word during training):
```
{SEMANTIC_CONTEXT} {connector} {description}
```

**Example**:
```
TU Delft drawing studio with high barrel-vaulted skylights providing bright diffused natural light, multiple rows of white-topped drafting tables on dark flooring, frosted glass partitions, creating functional educational workspace
```

**Rules**:
- MUST start with semantic context (exact match)
- Max 50 words, aim for 40-50 for detail
- NO "photo of" prefix (not needed)
- NO trigger word in caption (Replicate adds it)
- Single sentence, no trailing punctuation

**Never Accept**:
- ❌ `photo of TU Delft...` (no "photo of")
- ❌ `ide_interior TU Delft...` (no trigger word)
- ❌ Captions >50 words (too long)
- ❌ Multiple sentences

### 2. Export Format (UNCHANGED)

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

## Development Approach (v2.0)

### Documentation Strategy
- **ONE specification**: [SPECIFICATION.md](SPECIFICATION.md) - Single source of truth
- **Archive analysis docs**: Move exploration docs to `docs/archive/`
- **Avoid creating**: Temporary documents, multiple specs, redundant files
- **Keep minimal**: Only essential documentation

### Testing Approach
- **Phase 1**: Interior category only (MVP)
- **Test with real images**: 5 TU Delft interior photos
- **Manual testing first**: Verify captions work before automating
- **Iterate**: Get Interior perfect before adding other categories

### Implementation Strategy
1. **Start simple**: Interior category only
2. **Test early**: Don't wait until complete
3. **One thing at a time**: Perfect one feature before next
4. **No premature optimization**: Make it work, then make it better

### When Developing
✅ **Do**:
- Focus on ONE category (Interior) first
- Test with real images frequently
- Keep specification updated in ONE place
- Archive exploration/analysis docs

❌ **Don't**:
- Create multiple specification documents
- Add all categories at once
- Write extensive docs before testing
- Keep temporary analysis files in root

---

## Project Documentation

**Active**:
- **[SPECIFICATION.md](SPECIFICATION.md)** - Technical spec (v2.0)
- **[README.md](README.md)** - Project overview
- **[CLAUDE.md](CLAUDE.md)** - This file (AI instructions)

**Archive** (reference only):
- `docs/archive/` - Old specs, analysis, exploration docs

---

**Last Updated**: October 2025 (v2.0 in progress)
