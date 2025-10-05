# CRITICAL UPDATE: Trigger Word Handling

**Date**: 2025-10-05
**Impact**: 🚨 HIGH - Changes entire caption format

---

## NEW INFORMATION

### What We Just Learned:
**Replicate handles trigger words AUTOMATICALLY during training**
- User provides trigger word to Replicate (once for entire dataset)
- Replicate automatically prepends it to ALL captions during training
- **We should NOT include trigger word in .txt files**

---

## Current Implementation (WRONG ❌)

### What We're Doing Now:
```python
# caption_generator.py:184
caption = f"photo of {self.trigger_word} {description}"
```

**Output in .txt files**:
```
photo of ide_drawing_studio spacious room with white drafting tables...
photo of ide_drawing_studio corridor view with seating areas...
photo of ide_drawing_studio staircase detail with metal railings...
```

### Why This Is WRONG:
1. **Double trigger word**: Replicate adds it again → `"ide_drawing_studio ide_drawing_studio ..."`
2. **Breaks training**: Model learns wrong pattern
3. **Wastes caption space**: Trigger word consumes 1-3 words of 30-50 limit

---

## Correct Implementation (NEW ✅)

### What We SHOULD Do:

**Option A: No "photo of" prefix (cleanest)**
```
TU Delft drawing studio with barrel-vaulted skylights, rows of white drafting tables and wooden stools, dark flooring
TU Delft lecture hall featuring tiered seating, large projection screen, modern acoustic panels, bright overhead lighting
TU Delft campus courtyard with broad paved plaza, benches, low plantings, modern glass facades, cyclists in distance
```

**Option B: Keep "photo of" prefix (if Replicate expects it)**
```
photo of TU Delft drawing studio with barrel-vaulted skylights, rows of white drafting tables and wooden stools, dark flooring
photo of TU Delft lecture hall featuring tiered seating, large projection screen, modern acoustic panels, bright overhead lighting
photo of TU Delft campus courtyard with broad paved plaza, benches, low plantings, modern glass facades, cyclists in distance
```

### During Replicate Training:
```
User provides trigger word to Replicate: "ide_interior"

Replicate processes:
  Caption from .txt: "photo of TU Delft drawing studio with barrel-vaulted skylights..."
  Replicate adds:    "ide_interior photo of TU Delft drawing studio with barrel-vaulted skylights..."

Final training caption: "ide_interior photo of TU Delft drawing studio with barrel-vaulted skylights..."
```

---

## Impact Analysis

### What Changes:

#### 1. Caption Generator ✅ SIMPLIFIES
```python
# OLD (WRONG):
caption = f"photo of {self.trigger_word} {description}"

# NEW (CORRECT - Option A):
caption = f"{semantic_context} {description}"

# NEW (CORRECT - Option B):
caption = f"photo of {semantic_context} {description}"
```

#### 2. UI Changes ✅ SIMPLER
- **Remove**: Trigger word input field (not needed for captions!)
- **Keep trigger word ONLY for**:
  - Zip filename: `{trigger_word}_training.zip`
  - Optional: Export metadata (to remind user what trigger to use in Replicate)

#### 3. Export Format ✅ CLEANER
```
ide_interior_training.zip
├── image001.jpg
├── image001.txt    ← "photo of TU Delft drawing studio with..."  (NO trigger word)
├── image002.jpg
├── image002.txt    ← "photo of TU Delft lecture hall featuring..."  (NO trigger word)
└── README.txt      ← "Use trigger word: ide_interior"  (helpful reminder)
```

#### 4. Word Count Budget ✅ MORE SPACE
- OLD: "photo of ide_drawing_studio" = 4 words (wasted)
- NEW: "photo of" = 2 words OR no prefix = 0 words
- **Gain**: 2-4 words for actual description in 30-50 word budget

---

## Questions to Resolve

### Q1: Does Replicate expect "photo of" prefix in captions?

**Need to verify**:
- Check Replicate LoRA training docs
- Test with sample dataset

**Options**:
- **A**: Captions WITHOUT "photo of" → `"TU Delft drawing studio with..."`
- **B**: Captions WITH "photo of" → `"photo of TU Delft drawing studio with..."`

**My recommendation**: Start with Option B (keep "photo of"), can remove later if not needed

### Q2: Should we keep trigger word input field at all?

**Purpose of trigger word now**:
1. ✅ Zip filename: `{trigger_word}_training.zip`
2. ✅ User reminder: "Use this trigger word in Replicate: ide_interior"
3. ❌ NOT for captions (Replicate handles)

**Recommendation**:
- Keep trigger word field (for zip naming)
- Update UI label: "Trigger Word (for zip filename and Replicate)"
- Add note: "Note: Not embedded in captions - Replicate adds this during training"

### Q3: What's the new caption format?

**Recommended format**:
```
photo of {SEMANTIC_CONTEXT} {description}
```

**Examples**:
```
photo of TU Delft drawing studio with barrel-vaulted skylights, rows of white drafting tables, dark flooring, bright diffuse daylight
photo of TU Delft volunteer portrait showing person in relaxed pose, soft window light, neutral backdrop
photo of TU Delft prototype chair with curved wooden backrest, slender metal legs, matte finish
```

**During Replicate training** (user provides trigger: "ide_interior"):
```
Replicate generates: "ide_interior photo of TU Delft drawing studio with barrel-vaulted skylights..."
```

---

## Updated Architecture

### Caption Structure (NEW):

```
[NO TRIGGER] + [OPTIONAL PREFIX] + [SEMANTIC_CONTEXT] + [DESCRIPTION]

Components:
1. Trigger word: REMOVED (Replicate handles)
2. "photo of": KEEP (standard prefix)
3. Semantic context: "TU Delft drawing studio" (user provides)
4. Description: AI-generated visual details (30-50 words total)

Example:
"photo of TU Delft drawing studio with barrel-vaulted skylights, rows of white drafting tables and wooden stools on dark flooring, frosted glass partitions, bright diffuse daylight creating functional atmosphere"

Word count: 30 words ✅ (not wasting 2-4 on trigger word)
```

### Replicate Training Flow:

```
1. User exports from our app:
   ide_interior_training.zip
   ├── img001.jpg
   ├── img001.txt → "photo of TU Delft drawing studio with..."
   └── ...

2. User uploads to Replicate

3. Replicate asks: "Trigger word?"
   User enters: "ide_interior"

4. Replicate trains with:
   "ide_interior photo of TU Delft drawing studio with..."
   "ide_interior photo of TU Delft lecture hall featuring..."
   "ide_interior photo of TU Delft campus courtyard with..."

5. Later, user generates images:
   Prompt: "ide_interior photo of spacious design studio"
   → Model generates TU Delft-style design studio ✅
```

---

## Code Changes Required

### 1. Caption Generator (caption_generator.py)

```python
# REMOVE trigger_word from caption assembly

def generate_caption(self, image_path: str, semantic_context: str, category: str) -> Tuple[bool, str, Optional[str]]:
    """Generate caption WITHOUT trigger word (Replicate handles that)."""

    # ... (generate AI description)

    # OLD (WRONG):
    # caption = f"photo of {self.trigger_word} {description}"

    # NEW (CORRECT):
    # Ensure description starts with semantic_context
    if not description.lower().startswith(semantic_context.lower()):
        description = f"{semantic_context} {description}"

    # Add prefix (if using Option B)
    caption = f"photo of {description}"

    # Validate word count (30-50)
    word_count = len(caption.split())
    if not 30 <= word_count <= 50:
        # Regenerate...

    return (True, caption, None)
```

### 2. Metadata Exporter (metadata_exporter.py)

```python
# REMOVE trigger_word from caption formatting

def generate_metadata_txt(captions: Dict[str, str], trigger_word: str = "") -> str:
    """Generate metadata.txt WITHOUT trigger word in captions."""

    sorted_filenames = sorted(captions.keys(), key=lambda x: x.lower())

    lines = []
    for filename in sorted_filenames:
        caption = captions[filename].strip()

        # Remove trailing punctuation
        if caption and caption[-1] in '.!?':
            caption = caption[:-1]

        # NO TRIGGER WORD PREPENDING
        # Just use caption as-is
        lines.append(caption)

    return '\n'.join(lines)
```

### 3. Export with README (NEW)

```python
def create_training_zip_in_memory(
    image_paths: Dict[str, str],
    captions: Dict[str, str],
    trigger_word: str
) -> Tuple[bool, BytesIO, str]:
    """Create zip with README reminder about trigger word."""

    # ... (existing code)

    # Add README.txt with trigger word reminder
    readme_content = f"""# LoRA Training Dataset

Generated by Image Metadata Generator
TU Delft IDEM307 Workshop

## Instructions for Replicate.com:

1. Upload this zip file to Replicate
2. When asked for trigger word, enter: {trigger_word}
3. Replicate will automatically prepend "{trigger_word}" to all captions during training

## Caption Format:

All captions in .txt files follow this format:
photo of [semantic context] [visual description]

Example:
photo of TU Delft drawing studio with barrel-vaulted skylights, rows of white drafting tables...

## Usage After Training:

To generate images with your trained LoRA:
Prompt: "{trigger_word} photo of [your description]"

Example:
"{trigger_word} photo of spacious design studio with natural lighting"
"""

    zipf.writestr('README.txt', readme_content.encode('utf-8'))

    # ... (rest of existing code)
```

---

## Updated Expert Feedback Alignment

### Expert's Recommendation:
```
photo of {TRIGGER} {ENV_LABEL} — {model_caption}
```

### Our NEW Understanding:
```
photo of {SEMANTIC_CONTEXT} {description}
```

**Why we're REMOVING trigger**:
- Expert may not have known Replicate handles triggers automatically
- OR expert was showing the FINAL training caption (after Replicate adds trigger)
- Either way, **we should NOT include trigger in .txt files**

**Why we're SKIPPING env_label**:
- Full semantic context is richer: "TU Delft drawing studio" > "drawing_studio"
- Natural integration: "with..." vs "— ..."
- Simpler UX

**Final format**:
```
photo of TU Delft drawing studio with barrel-vaulted skylights, rows of white drafting tables and wooden stools, dark flooring, bright diffuse daylight creating functional atmosphere
```

---

## Action Items

### Immediate (P0):
- [ ] Remove trigger word from caption assembly in caption_generator.py
- [ ] Update metadata_exporter.py to not prepend trigger
- [ ] Update UI label for trigger word field
- [ ] Add README.txt to export with trigger word reminder

### High Priority (P1):
- [ ] Verify Replicate docs: Does it expect "photo of" prefix?
- [ ] Test sample dataset with Replicate
- [ ] Update all documentation with correct format

### Medium Priority (P2):
- [ ] Update CLAUDE.md with correct format
- [ ] Update DEVELOPMENT_NOTES.md
- [ ] Fix spacing bug (still relevant, just without trigger word)

---

## Examples: Before vs After

### BEFORE (WRONG):
```
# image001.txt
photo of ide_interior spacious industrial-style design studio with exposed concrete ceiling...

# During Replicate training (BROKEN):
ide_interior photo of ide_interior spacious industrial-style design studio...
                      ^^^^^^^^^^^^ DUPLICATE!
```

### AFTER (CORRECT):
```
# image001.txt
photo of TU Delft drawing studio with barrel-vaulted skylights, rows of white drafting tables...

# During Replicate training (CORRECT):
ide_interior photo of TU Delft drawing studio with barrel-vaulted skylights...
            ^ Replicate adds this
```

---

## Summary

### Key Changes:
1. ❌ **REMOVE**: Trigger word from caption text
2. ✅ **KEEP**: Trigger word for zip filename and README
3. ✅ **NEW FORMAT**: `photo of {semantic_context} {description}`
4. ✅ **MORE SPACE**: 2-4 extra words in 30-50 word budget
5. ✅ **CLEANER**: No duplication, follows Replicate's design

### Why This Matters:
- **Fixes training**: No duplicate trigger words
- **Better captions**: More space for visual details
- **Simpler code**: Less string manipulation
- **Follows Replicate design**: Works as intended

---

**Status**: Critical correction identified ✅
**Next Step**: Confirm "photo of" prefix requirement, then implement changes
