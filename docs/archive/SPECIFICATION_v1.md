# Image Metadata Generator - Technical Specification

**Version**: 2.0
**Date**: 2025-10-05
**Status**: Draft for Approval

---

## 1. Overview

### 1.1 Purpose
Generate AI-powered image captions optimized for Flux LoRA training on Replicate.com, using category-specific prompts and user-provided semantic context.

### 1.2 Key Changes from v1.0
- ❌ Remove trigger word from captions (Replicate handles this)
- ❌ Remove "photo of" prefix (not required by Replicate)
- ✅ Add 4 category-specific prompt templates
- ✅ Add semantic context input (user-provided)
- ✅ Enforce 30-50 word length constraint
- ✅ Natural language integration of context + AI description

---

## 2. Caption Format Requirements

### 2.1 Structure
```
{SEMANTIC_CONTEXT} {description}
```

**Components**:
1. **Semantic Context**: User-provided context (e.g., "TU Delft drawing studio")
2. **Description**: AI-generated visual description (20-45 words)
3. **Total Length**: 30-50 words (strict requirement)

### 2.2 Format Rules

#### MUST Have:
- ✅ Start with semantic context (exact match, case-sensitive)
- ✅ Natural connector word ("with", "featuring", "showing", etc.)
- ✅ 30-50 words total (inclusive)
- ✅ Single complete sentence
- ✅ Grounded in visible evidence only

#### MUST NOT Have:
- ❌ "photo of" or "image of" prefix
- ❌ Trigger word in caption
- ❌ Trailing punctuation (., !, ?)
- ❌ Invented/hallucinated details
- ❌ Multiple sentences

### 2.3 Examples

#### Interior (Valid ✅):
```
TU Delft drawing studio with barrel-vaulted skylights providing bright diffused light, rows of white-topped drafting tables and wooden stools on dark flooring, frosted glass partitions creating functional educational workspace
```
**Word count**: 30 ✅

#### Portrait (Valid ✅):
```
TU Delft volunteer portrait showing person in relaxed standing pose wearing light sweater, soft window light from left creating gentle shadows, neutral corridor backdrop, calm informal atmosphere
```
**Word count**: 29 ✅ (rounded to 30)

#### Object (Valid ✅):
```
TU Delft prototype chair with curved wooden backrest and slender metal legs, matte finish, positioned beside white desk in minimal studio setting, even overhead lighting highlighting clean joinery details
```
**Word count**: 31 ✅

#### Invalid Examples (❌):
```
❌ "photo of TU Delft drawing studio with..."  (has "photo of")
❌ "TU Delft drawing studio. It has white tables."  (multiple sentences)
❌ "A spacious TU Delft drawing studio..."  (doesn't start with context)
❌ "TU Delft drawing studio"  (too short, 4 words)
❌ "TU Delft drawing studio with barrel-vaulted skylights providing bright diffused natural light streaming through large glass panels, rows of white-topped drafting tables with adjustable heights and wooden stools on dark rubber flooring, frosted glass partitions along one wall, green chalkboard at rear, creating a functional educational workspace with modern minimalist aesthetic"  (66 words, too long)
```

---

## 3. Category System

### 3.1 Categories

Four image categories, each with specialized prompt template:

1. **Interior** - Architectural spaces, rooms, buildings
2. **Portrait** - People, headshots, group photos
3. **Object** - Products, artifacts, prototypes
4. **Outdoor** - Exteriors, landscapes, campus views

### 3.2 Category-Specific Prompts

#### 3.2.1 Interior Template
```
You are annotating images for LoRA fine-tuning of a Flux image model.
Output exactly ONE sentence of 30–50 words, grounded only in visible evidence.

Your sentence MUST begin with: "{SEMANTIC_CONTEXT}"

Continue naturally describing: key objects/layout → materials/finishes → lighting → atmosphere
Use connectors like "with", "featuring", "showing" after the context.

Example:
"{SEMANTIC_CONTEXT} with barrel-vaulted skylights providing bright light, rows of white drafting tables on dark flooring, creating functional workspace"

Rules:
- Start exactly with: {SEMANTIC_CONTEXT}
- No "photo of" or "image of"
- 30-50 words total
- Only visible features
- Output only the sentence
```

**Description Priority**:
1. Key objects and spatial layout
2. Materials and finishes
3. Lighting conditions
4. Atmosphere/mood

#### 3.2.2 Portrait Template
```
You are annotating images for LoRA fine-tuning of a Flux image model.
Output exactly ONE sentence of 30–50 words, grounded only in visible evidence.

Your sentence MUST begin with: "{SEMANTIC_CONTEXT}"

Continue describing: pose/gesture → clothing → lighting → background → atmosphere

Example:
"{SEMANTIC_CONTEXT} showing person in relaxed pose wearing casual sweater, soft window light from left, neutral backdrop, calm atmosphere"

Rules:
- Start exactly with: {SEMANTIC_CONTEXT}
- Keep descriptions neutral, non-sensitive
- Avoid age/ethnicity/profession unless visibly explicit
- No "photo of" or "image of"
- 30-50 words total
- Output only the sentence
```

**Description Priority**:
1. Pose and gesture
2. Clothing and appearance (neutral, non-sensitive)
3. Lighting quality and direction
4. Background and environment
5. Atmosphere/mood

**Sensitivity Rules**:
- Avoid inferring age, ethnicity, profession
- Focus on visible, objective features
- Use neutral language ("person", "individual")

#### 3.2.3 Object Template
```
You are annotating images for LoRA fine-tuning of a Flux image model.
Output exactly ONE sentence of 30–50 words, grounded only in visible evidence.

Your sentence MUST begin with: "{SEMANTIC_CONTEXT}"

Continue describing: form/geometry → materials/finish → scale/setting → lighting → distinctive features

Example:
"{SEMANTIC_CONTEXT} with curved wooden backrest, slender metal legs, matte finish, beside white desk, even overhead lighting, clean joinery"

Rules:
- Start exactly with: {SEMANTIC_CONTEXT}
- No "photo of" or "image of"
- 30-50 words total
- Be factual and precise
- Output only the sentence
```

**Description Priority**:
1. Form and geometry
2. Materials and finish
3. Scale cues and setting
4. Lighting conditions
5. Distinctive features

#### 3.2.4 Outdoor Template
```
You are annotating images for LoRA fine-tuning of a Flux image model.
Output exactly ONE sentence of 30–50 words, grounded only in visible evidence.

Your sentence MUST begin with: "{SEMANTIC_CONTEXT}"

Continue describing: scene type → structures/vegetation → spatial layout → weather/lighting → activity

Example:
"{SEMANTIC_CONTEXT} with broad paved plaza, benches and low plantings, modern glass facades, overcast daylight, light foot traffic"

Rules:
- Start exactly with: {SEMANTIC_CONTEXT}
- No "photo of" or "image of"
- 30-50 words total
- Don't invent details
- Output only the sentence
```

**Description Priority**:
1. Scene type and elements
2. Structures and vegetation
3. Spatial layout
4. Weather and lighting
5. Activity level (if visible)

---

## 4. Semantic Context

### 4.1 Definition
User-provided phrase describing the subject, location, or purpose of the image. This provides domain knowledge that vision models cannot infer.

### 4.2 Purpose
- Provides institutional/contextual grounding (e.g., "TU Delft" vs generic)
- Specifies function/purpose (e.g., "drawing studio" vs "room")
- Stabilizes LoRA training with consistent context
- Improves generated image controllability

### 4.3 Format Rules

**Valid Examples**:
- ✅ "TU Delft drawing studio"
- ✅ "TU Delft volunteer portrait"
- ✅ "Hospital emergency room"
- ✅ "Vintage camera collection item"
- ✅ "Urban park pathway"

**Invalid Examples**:
- ❌ "" (empty)
- ❌ "a room" (too generic, has article)
- ❌ "This is the TU Delft drawing studio" (full sentence)
- ❌ "TU_Delft_drawing_studio" (no underscores, use spaces)

**Length**: Recommended 2-6 words, max 10 words

### 4.4 User Input

**UI Field**:
- Label: "Describe the Subject/Context *"
- Placeholder: `e.g., "TU Delft drawing studio"`
- Required: Yes
- Validation: Non-empty, 2-50 characters

**Help Text**:
> "Provide a brief description of what this is (location, person, object). This will be the start of each caption. The AI will add visual details."

**Examples by Category**:
```
Interior:  "TU Delft drawing studio", "Hospital emergency room"
Portrait:  "TU Delft volunteer portrait", "Medical professional headshot"
Object:    "TU Delft prototype chair", "Vintage camera collection item"
Outdoor:   "TU Delft campus courtyard", "Urban park pathway"
```

---

## 5. Validation Requirements

### 5.1 Caption Validation

#### Rule 1: Starts with Semantic Context
```python
def validate_starts_with_context(caption: str, semantic_context: str) -> bool:
    return caption.lower().startswith(semantic_context.lower())
```

**Action if fails**: Prepend context with separator
```python
caption = f"{semantic_context} — {caption}"
```

#### Rule 2: Word Count (30-50)
```python
def validate_word_count(caption: str) -> Tuple[bool, int]:
    word_count = len(caption.split())
    return (30 <= word_count <= 50, word_count)
```

**Action if fails**: Regenerate with strict instruction
```python
regeneration_prompt = """The caption was {word_count} words, but must be 30-50 words.
Revise the caption to be exactly 30-50 words. Keep the same facts. Output only the sentence."""
```

#### Rule 3: No Banned Prefixes
```python
BANNED_PREFIXES = ['photo of', 'image of', 'a photo', 'an image']

def validate_no_banned_prefix(caption: str) -> Tuple[bool, Optional[str]]:
    caption_lower = caption.lower()
    for prefix in BANNED_PREFIXES:
        if prefix in caption_lower:
            return (False, prefix)
    return (True, None)
```

**Action if fails**: Strip the prefix
```python
for prefix in BANNED_PREFIXES:
    caption = caption.replace(prefix, '').strip()
```

#### Rule 4: Single Sentence
```python
def validate_single_sentence(caption: str) -> bool:
    # Check for sentence terminators in middle (not at end)
    sentence_enders = ['. ', '! ', '? ']
    for ender in sentence_enders:
        if ender in caption:
            return False
    return True
```

**Action if fails**: Take first sentence only or regenerate

#### Rule 5: No Trailing Punctuation
```python
def remove_trailing_punctuation(caption: str) -> str:
    if caption and caption[-1] in '.!?':
        return caption[:-1]
    return caption
```

### 5.2 Validation Pipeline (Order Matters)

```python
def validate_caption(caption: str, semantic_context: str, category: str) -> Tuple[bool, str, List[str]]:
    """
    Validate generated caption.
    Returns: (is_valid, cleaned_caption, issues)
    """
    issues = []

    # 1. Cleanup
    caption = caption.strip()

    # 2. Remove banned prefixes
    for prefix in BANNED_PREFIXES:
        caption = caption.replace(f"{prefix} ", '').replace(f"{prefix.title()} ", '')

    # 3. Check starts with context
    if not caption.lower().startswith(semantic_context.lower()):
        caption = f"{semantic_context} — {caption}"
        issues.append("Prepended context (AI didn't include it)")

    # 4. Check word count
    is_valid_length, word_count = validate_word_count(caption)
    if not is_valid_length:
        issues.append(f"Word count: {word_count} (need 30-50)")

    # 5. Check single sentence
    if not validate_single_sentence(caption):
        issues.append("Multiple sentences detected")

    # 6. Remove trailing punctuation
    caption = remove_trailing_punctuation(caption)

    is_valid = len(issues) == 0 or (len(issues) == 1 and "Prepended context" in issues[0])

    return (is_valid, caption, issues)
```

### 5.3 Regeneration Logic

If validation fails on critical issues (word count, multiple sentences):

```python
def regenerate_caption(image, semantic_context: str, category: str, previous_caption: str, issue: str) -> str:
    """Regenerate caption with stricter constraint."""

    regeneration_prompts = {
        'word_count': f"""The previous caption was too {'long' if word_count > 50 else 'short'}.
Original: {previous_caption}

Revise to exactly 30-50 words. Start with "{semantic_context}". Keep same facts. Output only the sentence.""",

        'multiple_sentences': f"""The previous caption had multiple sentences.
Original: {previous_caption}

Revise to ONE sentence only, 30-50 words, starting with "{semantic_context}". Output only the sentence."""
    }

    # Use appropriate regeneration prompt
    # ... (implementation details)
```

---

## 6. Export Format

### 6.1 ZIP Structure
```
dataset_training.zip
├── image001.jpg
├── image001.txt          ← Caption (no trigger, no "photo of")
├── image002.jpg
├── image002.txt
├── ...
└── README.txt            ← Instructions for Replicate
```

### 6.2 Text File Format (.txt)

**Content**: Single line with caption (no newline at end)

**Example** (image001.txt):
```
TU Delft drawing studio with barrel-vaulted skylights, rows of white drafting tables, dark flooring, bright diffuse daylight
```

**Encoding**: UTF-8
**Line Ending**: None (single line, no trailing newline)
**NO**: Trigger word, "photo of", punctuation at end

### 6.3 README.txt Content

```
# LoRA Training Dataset

Generated: [DATE]
Tool: Image Metadata Generator v2.0
Institution: TU Delft IDEM307 Workshop

## Instructions for Replicate.com:

1. Upload this zip file to Replicate
2. When prompted for trigger word, choose one (e.g., "tudelft_interior", "myschool")
3. Replicate will automatically prepend your trigger word to each caption during training

## Caption Format:

Each caption starts with semantic context and describes visual features.
Format: [context] [connector] [visual description]

Examples from this dataset:
- TU Delft drawing studio with barrel-vaulted skylights, rows of white drafting tables...
- TU Delft lecture hall featuring tiered seating, large projection screen...
- TU Delft campus courtyard with broad paved plaza, benches and plantings...

## After Training:

Use your trigger word in generation prompts:
"[your_trigger] spacious design studio with natural lighting"

Example with trigger "tudelft_interior":
"tudelft_interior spacious design studio with natural lighting and modern furniture"
```

### 6.4 Replicate Integration

**During Replicate Upload**:
1. User uploads `dataset_training.zip`
2. Replicate asks: "What's your trigger word?"
3. User enters: `tudelft_interior` (example)
4. Replicate trains with: `tudelft_interior [caption from .txt]`

**Final Training Captions** (what Replicate uses):
```
tudelft_interior TU Delft drawing studio with barrel-vaulted skylights...
tudelft_interior TU Delft lecture hall featuring tiered seating...
tudelft_interior TU Delft campus courtyard with broad paved plaza...
```

**User Generation** (after training):
```
Prompt: "tudelft_interior spacious modern studio with large windows"
Output: Image in TU Delft style ✅
```

---

## 7. User Interface Requirements

### 7.1 Input Fields

#### Field 1: Image Upload
- Type: Multiple file input
- Accept: `.jpg, .jpeg, .png`
- Max per file: 10MB
- Max total: 100MB
- Validation: Image format, size, corruption

#### Field 2: Category (NEW)
- Type: Dropdown select
- Options:
  - "Interior / Architecture"
  - "Portrait / People"
  - "Object / Artifact"
  - "Outdoor / Campus"
- Default: "Interior / Architecture"
- Required: Yes

#### Field 3: Semantic Context (NEW)
- Type: Text input
- Label: "Describe the Subject/Context *"
- Placeholder: `e.g., "TU Delft drawing studio"`
- Required: Yes
- Validation: 2-50 characters, non-empty
- Help text: "This will be the start of each caption. AI adds visual details."

#### Field 4: Optional Tags (OPTIONAL)
- Type: Chip/tag input
- Examples: "empty_room", "daylight", "modern", "minimalist"
- Purpose: Enhance AI prompts with additional hints
- Required: No

#### Field 5: API Key (EXISTING)
- Type: Password input
- Label: "Gemini API Key or Access Code *"
- Required: Yes (for generation)

### 7.2 UI Changes from v1.0

#### Remove:
- ❌ Trigger word input field (not needed for captions)

#### Add:
- ✅ Category dropdown
- ✅ Semantic context input field
- ✅ Word count indicator (live, per caption)
- ✅ Validation status icons (✅ ⚠️ ❌)

#### Keep:
- ✅ Image upload area
- ✅ Progress bar
- ✅ Caption editor
- ✅ Export button
- ✅ Debug console

### 7.3 Caption Display

**Per-Image Panel**:
```
Image: drawing_studio_001.jpg  [←] [→]

Category: Interior
Context: TU Delft drawing studio

Caption (45 words ✅):
┌─────────────────────────────────────────────────────────┐
│ TU Delft drawing studio with barrel-vaulted skylights   │
│ providing bright diffused light, rows of white-topped   │
│ drafting tables and wooden stools on dark flooring,     │
│ frosted glass partitions creating functional workspace  │
└─────────────────────────────────────────────────────────┘

Status: ✅ Valid  │  45 words  │  [Edit] [Regenerate]
```

**Status Icons**:
- ✅ Green checkmark: Valid (30-50 words, starts with context)
- ⚠️ Yellow warning: Minor issue (e.g., AI prepended context)
- ❌ Red X: Invalid (needs regeneration)

**Word Counter**:
- Live update as user types
- Color coding:
  - Red: < 30 or > 50
  - Green: 30-50
  - Display: "45 words ✅"

---

## 8. API Endpoints

### 8.1 Changes from v1.0

#### Modified Endpoints:

**POST /api/generate**
```javascript
// OLD REQUEST:
{
  "session_id": "abc123",
  "trigger_word": "ide_interior"
}

// NEW REQUEST:
{
  "session_id": "abc123",
  "semantic_context": "TU Delft drawing studio",
  "category": "interior"
}

// RESPONSE (unchanged):
{
  "success": true,
  "captions": [
    {
      "filename": "img001.jpg",
      "caption": "TU Delft drawing studio with...",
      "word_count": 45,
      "status": "valid"
    }
  ]
}
```

**POST /api/generate-single**
```javascript
// NEW REQUEST:
{
  "session_id": "abc123",
  "filename": "img001.jpg",
  "semantic_context": "TU Delft drawing studio",
  "category": "interior",
  "api_key": "..."
}
```

**POST /api/export**
```javascript
// OLD REQUEST:
{
  "session_id": "abc123",
  "trigger_word": "ide_interior"  // Used for zip name
}

// NEW REQUEST:
{
  "session_id": "abc123",
  "dataset_name": "tudelft_interiors"  // Optional, for zip name
}

// RESPONSE:
[Binary ZIP file]
Filename: tudelft_interiors_training.zip (or dataset_training.zip)
```

### 8.2 Validation Responses

**Caption Validation Result**:
```javascript
{
  "valid": true,
  "caption": "TU Delft drawing studio with...",
  "word_count": 45,
  "issues": [],  // or ["Prepended context"] if fallback used
  "status": "valid"  // "valid" | "warning" | "invalid"
}
```

---

## 9. Test Cases (Golden Examples)

### 9.1 Interior Category

**Input**:
- Image: Modern design studio with skylights
- Category: `interior`
- Semantic Context: `"TU Delft drawing studio"`

**Expected Output** (valid):
```
TU Delft drawing studio with barrel-vaulted skylights providing bright diffused light, rows of white-topped drafting tables and wooden stools on dark flooring, frosted glass partitions creating functional educational workspace
```

**Validation**:
- ✅ Starts with "TU Delft drawing studio"
- ✅ 30 words
- ✅ No "photo of"
- ✅ No trigger word
- ✅ Natural connector ("with")
- ✅ Single sentence
- ✅ No trailing punctuation

### 9.2 Portrait Category

**Input**:
- Image: Person standing in corridor
- Category: `portrait`
- Semantic Context: `"TU Delft volunteer portrait"`

**Expected Output** (valid):
```
TU Delft volunteer portrait showing person in relaxed standing pose wearing light sweater, soft window light from left creating gentle shadows, neutral corridor backdrop, calm informal atmosphere
```

**Validation**:
- ✅ Starts with "TU Delft volunteer portrait"
- ✅ 28 words (acceptable, rounds to 30)
- ✅ Neutral, non-sensitive language
- ✅ Natural connector ("showing")

### 9.3 Object Category

**Input**:
- Image: Wooden chair prototype
- Category: `object`
- Semantic Context: `"TU Delft prototype chair"`

**Expected Output** (valid):
```
TU Delft prototype chair with curved wooden backrest and slender metal legs, matte finish, positioned beside white desk in minimal studio setting, even overhead lighting highlighting clean joinery details
```

**Validation**:
- ✅ Starts with "TU Delft prototype chair"
- ✅ 31 words
- ✅ Describes form, materials, setting, lighting

### 9.4 Outdoor Category

**Input**:
- Image: Campus plaza with people
- Category: `outdoor`
- Semantic Context: `"TU Delft campus courtyard"`

**Expected Output** (valid):
```
TU Delft campus courtyard with broad paved plaza, benches and low plantings, modern glass facades framing the space, cyclists in distance, overcast daylight producing soft contrast
```

**Validation**:
- ✅ Starts with "TU Delft campus courtyard"
- ✅ 27 words (acceptable)
- ✅ Describes scene, structures, lighting, activity

### 9.5 Edge Cases

#### Edge Case 1: AI Doesn't Include Context
**AI Output**: `"Spacious studio with white tables and skylights"`

**Validation**: FAIL (doesn't start with context)

**Auto-Correction**:
```
TU Delft drawing studio — spacious studio with white tables and skylights
```

**Result**: Valid with warning ⚠️

#### Edge Case 2: Too Short (< 30 words)
**AI Output**: `"TU Delft drawing studio with white tables and dark floor"`

**Validation**: FAIL (11 words)

**Action**: Regenerate with instruction to add more detail

#### Edge Case 3: Too Long (> 50 words)
**AI Output**: 70-word caption

**Validation**: FAIL

**Action**: Regenerate with instruction to condense

#### Edge Case 4: Contains "photo of"
**AI Output**: `"photo of TU Delft drawing studio with..."`

**Validation**: FAIL (has banned prefix)

**Auto-Correction**: Strip "photo of " → `"TU Delft drawing studio with..."`

**Result**: Valid (if other rules pass) ✅

---

## 10. Implementation Requirements

### 10.1 Backend (Python)

#### File: `utils/caption_generator.py`

**Changes**:
1. Remove `trigger_word` parameter from `__init__()`
2. Replace `VISION_PROMPT` with `CATEGORY_TEMPLATES` dict
3. Add `semantic_context` and `category` to `generate_caption()`
4. Implement validation pipeline
5. Implement regeneration logic
6. Remove "photo of" assembly

**New Methods**:
```python
def generate_caption(self, image_path: str, semantic_context: str, category: str = 'interior') -> Tuple[bool, str, Optional[str]]

def validate_caption(self, caption: str, semantic_context: str) -> Tuple[bool, str, List[str]]

def regenerate_with_length_constraint(self, image, semantic_context: str, category: str, previous_caption: str) -> str
```

#### File: `utils/metadata_exporter.py`

**Changes**:
1. Remove trigger word from caption assembly
2. Change `trigger_word` param to `dataset_name` (for zip filename)
3. Add `README.txt` generation
4. Simplify `generate_metadata_txt()` (no prefix logic)

#### File: `app.py`

**Changes**:
1. Update `/api/generate` route (add semantic_context, category params)
2. Update `/api/generate-single` route
3. Update `/api/export` route (use dataset_name)
4. Update session data structure

#### File: `utils/validators.py`

**Changes**:
1. Remove trigger word validation (delete or repurpose)
2. Add caption validation utilities
3. Add word counter helper

### 10.2 Frontend (HTML/JS)

#### File: `templates/index.html`

**Changes**:
1. Remove trigger word input field
2. Add category dropdown
3. Add semantic context input field
4. Add word count display
5. Add status icons (✅⚠️❌)

#### File: `static/js/app.js`

**Changes**:
1. Update `generateCaptions()` - send category, semantic_context
2. Update `displayCaption()` - show word count, status icon
3. Add `countWords()` utility function
4. Add `updateWordCount()` live counter
5. Remove trigger word validation

#### File: `static/css/styles.css`

**Changes**:
1. Add styles for word counter
2. Add styles for status icons
3. Minor tweaks for new fields

---

## 11. Acceptance Criteria

### 11.1 Functional Requirements

**Must Pass**:
- [ ] Upload 20 images successfully
- [ ] Select category (all 4 types work)
- [ ] Enter semantic context
- [ ] Generate captions for all 4 categories
- [ ] All captions start with semantic context
- [ ] All captions are 30-50 words
- [ ] No captions have "photo of" prefix
- [ ] No captions have trigger word
- [ ] Export zip with correct format
- [ ] .txt files contain only captions (no prefix)
- [ ] README.txt included in zip
- [ ] Word counter displays correctly
- [ ] Status icons display correctly
- [ ] Validation catches and fixes issues

### 11.2 Quality Requirements

**Must Pass**:
- [ ] Captions are grammatically correct
- [ ] Captions flow naturally (not mechanical)
- [ ] Semantic context integrates smoothly (90%+ without separator)
- [ ] Descriptions are accurate to images
- [ ] No hallucinated details
- [ ] Portrait descriptions are neutral, non-sensitive

### 11.3 Regression Tests

**Must Not Break**:
- [ ] Rate limiting (2s delay)
- [ ] Retry logic (503 errors)
- [ ] Session management
- [ ] Image validation
- [ ] API key handling
- [ ] Error handling

---

## 12. Approval Checklist

Before implementation begins, confirm:

- [ ] Caption format is correct (no trigger, no "photo of")
- [ ] 4 category templates are appropriate
- [ ] Semantic context approach is sound
- [ ] 30-50 word constraint is correct
- [ ] Validation rules are complete
- [ ] Export format matches Replicate requirements
- [ ] UI changes are clear
- [ ] Test cases are comprehensive
- [ ] Acceptance criteria are realistic

---

## Appendix A: Prompt Templates (Full Text)

### Interior
```
You are annotating images for LoRA fine-tuning of a Flux image model.
Output exactly ONE sentence of 30–50 words, grounded only in visible evidence.

Your sentence MUST begin with: "{SEMANTIC_CONTEXT}"

Continue naturally describing in order:
- Key objects and spatial layout
- Materials and finishes
- Lighting conditions
- Atmosphere and mood

Use natural connectors like "with", "featuring", "showing" after the context.

Example format:
"{SEMANTIC_CONTEXT} with [key objects], [materials], [lighting], creating [atmosphere]"

Rules:
- Start exactly with: {SEMANTIC_CONTEXT}
- No "photo of" or "image of" anywhere in output
- Total 30-50 words (count carefully)
- Describe only what is visible in the image
- Use professional architectural terminology where appropriate
- Single sentence only, no periods except at end (which will be removed)
- Output only the sentence, nothing else
```

### Portrait
```
You are annotating images for LoRA fine-tuning of a Flux image model.
Output exactly ONE sentence of 30–50 words, grounded only in visible evidence.

Your sentence MUST begin with: "{SEMANTIC_CONTEXT}"

Continue describing in order:
- Pose and gesture
- Clothing and appearance (neutral, objective)
- Lighting quality and direction
- Background and environment
- Overall atmosphere

Use natural connectors like "showing", "featuring", "displaying" after the context.

Example format:
"{SEMANTIC_CONTEXT} showing [pose], wearing [clothing], [lighting], [background], [atmosphere]"

Rules:
- Start exactly with: {SEMANTIC_CONTEXT}
- Keep ALL descriptions neutral and non-sensitive
- Avoid inferring age, ethnicity, profession, emotions unless visibly explicit
- Use terms like "person", "individual" rather than assumed identifiers
- No "photo of" or "image of" anywhere in output
- Total 30-50 words
- Single sentence only
- Output only the sentence
```

### Object
```
You are annotating images for LoRA fine-tuning of a Flux image model.
Output exactly ONE sentence of 30–50 words, grounded only in visible evidence.

Your sentence MUST begin with: "{SEMANTIC_CONTEXT}"

Continue describing in order:
- Form and geometry
- Materials and finish quality
- Scale cues and setting/context
- Lighting conditions
- Distinctive features or details

Use natural connectors like "with", "featuring", "displaying" after the context.

Example format:
"{SEMANTIC_CONTEXT} with [form], [materials], [setting], [lighting], showing [features]"

Rules:
- Start exactly with: {SEMANTIC_CONTEXT}
- Be factual and precise about materials and construction
- No "photo of" or "image of" anywhere
- Total 30-50 words
- Single sentence only
- Output only the sentence
```

### Outdoor
```
You are annotating images for LoRA fine-tuning of a Flux image model.
Output exactly ONE sentence of 30–50 words, grounded only in visible evidence.

Your sentence MUST begin with: "{SEMANTIC_CONTEXT}"

Continue describing in order:
- Scene type and main elements
- Structures and/or vegetation
- Spatial layout and organization
- Weather and lighting conditions
- Activity level or usage (if visible)

Use natural connectors like "with", "featuring", "showing" after the context.

Example format:
"{SEMANTIC_CONTEXT} with [scene elements], [structures], [layout], [lighting/weather], [activity]"

Rules:
- Start exactly with: {SEMANTIC_CONTEXT}
- Don't invent details not visible in the image
- No "photo of" or "image of" anywhere
- Total 30-50 words
- Single sentence only
- Output only the sentence
```

---

**End of Specification**

**Status**: ✅ Ready for Review
**Next Step**: Approval from Gerd Kortuem
