# Claude Project Instructions

**STATUS**: ✅ PRODUCTION - Deployed for TU Delft IDEM307 Workshop

## Project Overview

Web application for generating AI-powered image captions for LoRA fine-tuning datasets. Built for TU Delft IDEM307 workshop students. Publicly deployed with secret access code authentication for shared Gemini API key usage.

**Key Features**:
- Gemini 2.5 Pro AI caption generation
- Real-time progress tracking
- Per-image caption editing
- Replicate.com-compatible ZIP export (individual .txt files per image)
- Secret access code system for controlled API key sharing

## Development Principles

### 1. Iterative Development
- Build in small increments
- Show working prototypes frequently
- Get feedback before continuing
- Don't build everything at once

### 2. Practical Over Perfect
- Functional > beautiful
- Working MVP > feature-complete
- User can manually fix edge cases
- Performance: 30 images in ~5 minutes

### 3. Code Quality
- Clear variable names
- Comments for non-obvious logic
- Modular functions
- Handle errors gracefully
- Use pathlib for file operations

## Technical Constraints

### Technology Choice

**NOT Streamlit** - User explicitly rejected this.

**Options**:
- Flask web app (recommended - flexible, can deploy)
- Standalone tkinter (if simpler makes more sense)

Ask user which they prefer if unclear from context.

### API Usage (Gemini)

- API key: `GEMINI_API_KEY` environment variable (or user-provided via UI)
- Secret access code: `SECRET_ACCESS_CODE` environment variable
- Model: `gemini-2.5-pro` (priority), fallback chain: 2.5-flash → 2.0-flash-exp → 1.5-pro → 1.5-flash
- Free tier: ~15 req/min, 1500/day
- Strategy: 2s delay between requests (per-image sequential processing)
- Retry: exponential backoff (1s, 2s, 4s, 8s)
- Performance: ~18 seconds per image with Gemini 2.5 Pro

### Caption Format (CRITICAL)

**Required format**:
```
photo of [trigger_word] [description]
```

**Rules**:
- Literal "photo of " (with space after)
- Then trigger_word (e.g., "ide_main_hall")
- Space before description
- No trailing punctuation
- One line per image

**Correct**:
```
photo of ide_main_hall entrance area, glass doors, high ceiling, natural daylight, open space
```

**Wrong**:
```
A photo of ide_main_hall...  ← "A" before "photo"
photo of ide_main_hall: entrance...  ← colon
Photo of ide_main_hall...  ← capital P
ide_main_hall entrance...  ← missing "photo of"
```

### File Operations

- metadata.txt: UTF-8, LF line endings, no BOM
- Zip: `[trigger_word]_training.zip`
- Images in alphabetical order (use `sorted()`)
- Don't modify original images

## User Preferences

### UI/UX
- Simple, functional design
- Show progress during batch processing
- Confirm before overwriting files
- Can run locally without complex setup

### Workflow
- Fast batch processing (user has 6 datasets)
- Easy caption editing (main focus after generation)
- One-click export
- Reusable tool (clear state between runs)

### Caption Quality
Auto-generated captions should be:
- Specific (not generic)
- Objective (no interpretation)
- Structured format
- Lighting information always included
- Consistent detail level

User expects to edit ~20% of captions.

## Communication Guidelines

### Ask Questions When
- Architecture choice unclear (Flask vs tkinter)
- Multiple valid UX approaches
- Technical tradeoffs need user input

### Don't Ask Permission For
- Standard libraries
- Common patterns
- Obvious error handling
- Minor UI decisions

### Show Rather Than Tell
- Provide working code
- Show example outputs
- Demonstrate with examples
- Let user test and give feedback

## Development Roadmap

### Phase 1 (MVP - Start Here)
- Choose architecture
- Folder selection or upload
- Trigger word input + validation
- Gemini API integration
- Batch caption generation
- Export metadata.txt

### Phase 2 (Editing)
- Display images + captions
- Edit functionality
- Navigation
- Save changes

### Phase 3 (Export)
- Create zip file
- Download/save
- Validation

### Phase 4 (Polish - Optional)
- Progress improvements
- Better error handling
- Keyboard shortcuts

## Current Status

**Starting fresh**. Begin with Phase 1 MVP. 

**First step**: Ask user to confirm Flask vs tkinter, then build simple prototype showing:
1. Folder selection
2. Trigger word input
3. Generate one caption using Gemini
4. Show formatted output

Don't build full UI yet. Show working caption generation first.

## Important Notes

### About User
- Technical but not Python expert
- Values reliability over features
- Needs tool for ~6 datasets (~180 images total)
- One-time intensive use, may reuse later
- Tool replaces 12-18 hours manual work

### About Task
- Quality matters (used in teaching materials)
- Gemini quality worth the processing time
- Free tier sufficient for project
- Local execution important

### Anti-Patterns

❌ Don't:
- Build full UI before testing captions
- Use Streamlit (user rejected)
- Hard-code paths or API keys
- Assume user's environment
- Ignore rate limits

✅ Do:
- Test with real images early
- Validate all inputs
- Clear error messages
- Standard libraries preferred
- Follow MVP → editing → polish progression

## Starting Instructions

When user starts Claude Code, they'll say something like:

> "Read PROJECT_BRIEF.md and build the metadata generator"

Your response should:
1. Confirm you understand requirements
2. Ask: "Should I build a Flask web app or tkinter desktop app?"
3. Once decided, show Phase 1 MVP code
4. Explain how to run it
5. Wait for feedback before Phase 2

**Build incrementally. Show working code frequently.**
