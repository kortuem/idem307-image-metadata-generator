# Claude Project Instructions

> **Note**: This file contains AI assistant instructions for Claude Code.
> For project documentation, see [README.md](README.md) or [docs/](docs/).

---

## Project Overview

**Status**: ✅ Production v1.0 - Workshop Wednesday (30 students concurrent)
**Live App**: https://idem307-image-metadata-generator.onrender.com/
**Purpose**: Flask app for AI-powered image captions for LoRA training (TU Delft workshop)

---

## Commands

```bash
# Local development
python3 app.py              # Run dev server (port 5001)

# Deployment
git push                    # Auto-deploys to Render

# Environment
# Render: Hobby plan ($7) + Standard instance ($25, 2GB RAM)
# Gemini 2.5 Flash (paid tier, 1000 RPM)
# MAX_CONCURRENT_SESSIONS=30

# Image Categories (8 types)
# - Interior/Architecture: Spaces, rooms, interior environments
# - Person/Portrait: Individual person, face, portrait
# - People/Groups: Multiple people, activities, interactions
# - Object/Product: Items, tools, designed objects
# - Vehicle/Machine: Cars, bikes, robots, transportation
# - Exterior/Building: Building facades, architectural exteriors
# - Scene/Landscape: Nature, outdoor scenes, environments
# - Abstract/Artwork: Sketches, diagrams, digital compositions
# Each category uses specialized prompts optimized for that content type

# Slow Mode (Workshop Safety Valve)
# Students can enable via checkbox in UI
# - Increases delay: 0.1s → 3s between API calls
# - Use if: API rate limits hit, or server overloaded
# - Reduces throughput but prevents failures
```

---

## Critical Rules (DO NOT BREAK)

### Caption Format
**MUST be**: `photo of [trigger_word] [description]`
- Literal "photo of " (lowercase, space after)
- Replicate.com requirement - breaks training if violated
- No punctuation at end

**Never accept**: `A photo of`, `Photo of`, `trigger_word description`

### Export Format
Individual .txt file per image (Replicate requirement):
```
image1.jpg
image1.txt  ← NOT a single metadata.txt
image2.jpg
image2.txt
```

### Security
- Never commit: `.env`, `static/uploads/*`
- Safe to commit: `.env.example`, all docs, source code

---

## Session Management (Bug-Prone Area)

**Critical implementation details** (has caused production bugs):

1. **Timestamp tracking**: Uses `active_sessions` dict, NOT file mtime
2. **Update on activity**: Call `update_session_activity()` on every caption request
3. **Cleanup logic**: Checks `active_sessions[sid]` timestamp for 2hr timeout
4. **Three-tier cleanup**:
   - Client: Delete old session before new upload
   - Server: Delete after ZIP export
   - Abandoned: 2hr timeout based on dict timestamp

**Known bug (fixed in 4bb282c)**: Cleanup was checking file mtime instead of dict timestamp, causing sessions to be deleted 2hrs after UPLOAD instead of 2hrs after LAST ACTIVITY.

---

## Code Style

- Clear variable names: `trigger_word` not `tw`
- Comments for non-obvious logic
- `pathlib` for cross-platform paths
- Proper error handling with try/except

---

## Debugging Guidelines

**When bugs occur**:
1. Ask for complete context (full logs, exact sequence, timing)
2. Trace complete flow (don't assume - verify every step)
3. Document assumptions first (write how it SHOULD work)
4. Audit critical paths when in doubt
5. **Fix root cause, not symptoms**

**Lesson learned**: "Invalid session ID" bug took multiple attempts because we fixed symptoms (added updates, cleanup, delete-on-export) instead of finding root cause (cleanup checking wrong timestamp). Systematic audit on day 1 would have found it immediately.

---

## User Profile

**Prof. Gerd Kortuem**:
- Technical but not Python expert
- Values reliability > features
- Prefers deploy-and-test workflow (not local testing first)
- Workshop: 30 students, 4 hours, 20-40 images each

**Students**: Non-technical, need simple working tool

---

## Development Principles

1. **Reliability over features** - Do one thing well
2. **Understand root causes** - Don't just fix symptoms
3. **User-centered** - Clear error messages, works first try
4. **Graceful degradation** - Fallback models if primary fails

---

## Project Documentation

- [README.md](README.md) - Project overview
- [TUTORIAL.md](TUTORIAL.md) - Student guide
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - Technical architecture
- [docs/DEPLOYMENT-RENDER.md](docs/DEPLOYMENT-RENDER.md) - Deployment guide

---

**Last Updated**: October 2025 (v1.0)
