# Development Notes & Issues

**Last Updated**: 2025-10-05

---

## 🚨 Critical Bug Found

### Caption Format Issue (2025-10-05)

**Problem**: Missing space between trigger word and description

**Current Output**:
```
photo of ide_drawing_studio A spacious and empty...
                          ^ no space here
```

**Should Be**:
```
photo of ide_drawing_studio a spacious and empty...
                          ^ space + lowercase
```

**Impact**: Breaks Replicate.com compatibility

**Location**: Likely in [caption_generator.py:184](utils/caption_generator.py#L184) where caption is assembled

**Fix Required**:
- Add space between trigger_word and description
- Ensure description starts with lowercase letter

---

## 📋 Major Upgrade Specification

### Expert Feedback: Upgrade for Replicate LoRA Datasets

**Source**: User with Replicate.com & Gemini expertise
**Priority**: High - Complete system overhaul

### Key Requirements

#### 1. Image Categories (NEW)
- **Categories**: interior | portrait | object | outdoor
- Each category gets specialized prompt template
- Category-specific description priorities

#### 2. Semantic Context (NEW)
- User provides context per batch (e.g., "TU Delft drawing studio")
- Must appear at/near start of caption
- Stabilizes LoRA training, improves prompt controllability

#### 3. Caption Length Constraint (NEW)
- **Target**: 30-50 words (optimal for Flux LoRA)
- Must be enforced via validation
- Regenerate if outside range

#### 4. Caption Structure
```
photo of {TRIGGER} {ENV_LABEL} — {model_caption}
```
- `TRIGGER`: LoRA trigger word (e.g., `TUDELFT_INTERIOR`)
- `ENV_LABEL`: normalized label (e.g., `drawing_studio`, `lecture_hall`)
- `model_caption`: 30-50 word description from AI

#### 5. Export Format (UPDATED)
```
/export/
  img_0001.jpg
  img_0001.txt      ← final_caption (one line)
  img_0002.jpg
  img_0002.txt
  metadata.csv      ← optional metadata
```

**Note**: Individual .txt files (CORRECT - already doing this!)

---

## 🎯 New Prompt Templates

### Template Design Principles
- ONE sentence only
- 30-50 words exactly
- Grounded in visible evidence only
- Begin with {SEMANTIC_CONTEXT}
- No "photo of" prefix
- No camera specs/brand jargon
- No trigger word (added later)

### (A) Interior / Architecture Template

```
You are annotating images for LoRA fine-tuning of a Flux image model.
Output exactly ONE sentence of 30–50 words, grounded only in visible evidence.

Begin near the start with: {SEMANTIC_CONTEXT} (e.g., "TU Delft drawing studio").
Describe in order: room label; key objects/layout; materials/finishes; lighting; optional attributes ({OPTIONAL_TAGS}).
Rules: no trigger word; no "photo/image"; no camera specs; be objective; do not invent elements.
Output only the sentence.
```

**Example Output**:
```
TU Delft drawing studio — spacious art and design classroom with barrel-vaulted skylights, rows of white drafting tables and wooden stools, dark flooring, green chalkboard at the back, frosted glass partitions along one side, bright diffuse daylight, quiet and functional atmosphere.
```

### (B) Portrait / People Template

```
You are annotating images for LoRA fine-tuning of a Flux image model.
Output exactly ONE sentence of 30–50 words, grounded only in visible evidence.

Begin near the start with: {SEMANTIC_CONTEXT} (e.g., "TU Delft volunteer portrait").
Describe in order: overall appearance (neutral, non-sensitive), pose/gesture, clothing; visible background context; lighting; overall atmosphere.
Avoid inferring identity, age, or emotions if unclear.
Rules: no trigger word; no "photo/image"; no camera specs; only the sentence.
```

**Example Output**:
```
TU Delft volunteer portrait — adult person in light sweater standing near glass wall, relaxed posture, neutral expression, soft side daylight creating gentle shadows, uncluttered corridor backdrop, calm and informal atmosphere.
```

### (C) Object / Artifact Template

```
You are annotating images for LoRA fine-tuning of a Flux image model.
Output exactly ONE sentence of 30–50 words, grounded only in visible evidence.

Begin near the start with: {SEMANTIC_CONTEXT} (e.g., "TU Delft prototype chair").
Describe in order: object category; form/geometry; materials/finishes; scale cues; setting/background; lighting; distinctive features.
Rules: no trigger word; no "photo/image"; only the sentence; be factual and precise.
```

**Example Output**:
```
TU Delft prototype chair — compact wooden seat with curved backrest and slender metal legs, matte finish, placed beside white desk in a minimal studio setting, even overhead lighting, clean joinery details and functional aesthetic.
```

### (D) Outdoor / Campus Template

```
You are annotating images for LoRA fine-tuning of a Flux image model.
Output exactly ONE sentence of 30–50 words, grounded only in visible evidence.

Begin near the start with: {SEMANTIC_CONTEXT} (e.g., "TU Delft campus courtyard").
Describe in order: scene type; structures/vegetation; spatial layout; materials; lighting/weather; activity level if visible; atmosphere.
Rules: no trigger word; no "photo/image"; only the sentence; do not invent details.
```

**Example Output**:
```
TU Delft campus courtyard — broad paved plaza with benches and low plantings, modern glass facades framing the space, cyclists in the distance, overcast daylight producing soft contrast, open circulation area with light foot traffic and clear wayfinding signage.
```

---

## ✅ Post-Processing & Validation

### Required Validation Steps

1. **Cleanup**:
   - Trim whitespace
   - Unify punctuation
   - Strip stray quotes

2. **Word Count**: 30-50 words (inclusive)
   - If fails: regenerate with: *"Revise to 30–50 words; keep same facts; output only the sentence."*

3. **Semantic Context Check**:
   - Must contain semantic_context (case-insensitive)
   - If missing: prepend `{SEMANTIC_CONTEXT} — {caption}`

4. **Banned Prefixes**:
   - ❌ "photo of"
   - ❌ "image of"
   - Strip if found

5. **Portrait Sensitivity** (for portrait category):
   - Blacklist: age, ethnicity, profession (unless visibly explicit)
   - If found: regenerate with stricter instruction

---

## 🎨 UI Changes Required

### Batch Header Controls (NEW)
- **Category** (dropdown): interior | portrait | object | outdoor
- **Semantic context** (text input): e.g., "TU Delft drawing studio"
- **Optional tags** (chips/checkboxes): empty_room, few_people, daylight, artificial_lighting, etc.
- **Trigger** (text): LoRA trigger word (not in model prompt, only for export)
- **Env label** (dropdown): normalized label (e.g., drawing_studio, lecture_hall)

### Per-Image Panel (ENHANCED)
- Image preview
- "Generate caption" button
- **Live word count** indicator
- Editable `model_caption` field
- Read-only `final_caption` preview (shows trigger + env + caption)
- **Status icons**:
  - ✅ length OK (30-50 words)
  - ⚠️ too short/long
  - ❌ banned term found

### Export (ENHANCED)
- "Export Replicate Zip" button
- Writes individual .txt sidecars
- Optional metadata.csv export
- Validation blocking: if any image fails validation, show dialog with "Fix" shortcuts

---

## 🔬 Optimization Suggestions (A/B Testing)

### Suggestion 1: One-Shot Prompting
Add golden example directly in prompt for better consistency:

```
Example output:
TU Delft drawing studio — spacious classroom with barrel-vaulted skylights, rows of white drafting tables and wooden stools on dark flooring, green chalkboard at the back, frosted glass partitions along one side, bright diffuse daylight, quiet and functional atmosphere.
```

### Suggestion 2: Emphasis Re-ordering
Move critical constraint to beginning:

```
Output exactly ONE sentence of 30–50 words. You are an expert annotator for LoRA fine-tuning of a Flux image model. Your entire output must be grounded only in visible evidence from the image.
...
Remember, the final output must be only the single sentence and nothing else.
```

### Suggestion 3: Chain-of-Thought Regeneration
More robust regeneration prompt (slower but better):

```
The previous caption was not between 30 and 50 words.
First, list the key factual elements from the original caption.
Second, rewrite those facts into a single, new sentence that is between 30 and 50 words long.
Output only the final rewritten sentence.
```

---

## 📝 Edge Cases & Constraints

### Truthfulness
- Never add elements not visible
- If semantic context contradicts image, prefer what's visible but still include context string

### Duplicates
- Near-identical images should get varied captions
- Vary minor details (object ordering, lighting description)

### People (Portrait Category)
- Keep descriptions neutral, non-sensitive
- Avoid inferring age/identity
- Focus on: pose, clothing, lighting, context

### Length Enforcement
- If model can't produce 30-50 words reliably:
  - Apply simple trimming of redundant clauses
  - OR request regeneration once

### Language
- Default: English
- Optional: language selector (pass to template)

### Safety
- Strip personally identifying text on signage (unless explicitly allowed)

---

## ✅ Testing Checklist (Acceptance Criteria)

- [ ] UI shows: Category, Semantic context, Optional tags, Trigger, Env label
- [ ] Each category outputs ONE sentence, 30-50 words
- [ ] Post-processor enforces:
  - [ ] Length (30-50 words)
  - [ ] Presence of semantic context
  - [ ] No banned prefixes
- [ ] .txt sidecars created per image (one line each)
- [ ] Trigger/env label prepended correctly
- [ ] "Export Replicate Zip" produces:
  - [ ] Matching .jpg/.txt pairs
  - [ ] Optional metadata.csv
- [ ] Batch generation supports:
  - [ ] Shared semantic context
  - [ ] Per-image edits
- [ ] Example cases reproduce acceptable outputs without manual fixes

---

## 🏗️ Implementation Plan

### Phase 1: Fix Critical Bug
1. Fix spacing in caption assembly ([caption_generator.py:184](utils/caption_generator.py#L184))
2. Ensure lowercase start of description
3. Test with existing workflow

### Phase 2: Add Category Support
1. Create template system (4 categories)
2. Add category selection UI
3. Update caption_generator.py to use category-specific prompts

### Phase 3: Add Semantic Context
1. Add semantic context input field
2. Inject into prompts
3. Validate presence in output

### Phase 4: Length Enforcement
1. Add word counter utility
2. Implement validation (30-50 words)
3. Add regeneration logic

### Phase 5: Enhanced Export
1. Update final_caption format: `photo of {TRIGGER} {ENV_LABEL} — {model_caption}`
2. Add env_label UI control
3. Add metadata.csv export option

### Phase 6: UI Polish
1. Add status icons (✅⚠️❌)
2. Add live word count
3. Add validation blocking on export

---

## 📚 References

- Current CLAUDE.md instructions
- Replicate.com LoRA training docs
- Flux model best practices
