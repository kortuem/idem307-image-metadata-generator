# Image Metadata Generator - Technical Specification

**Version**: 2.0
**Date**: 2025-10-05

---

## Caption Format

### Structure
```
{SEMANTIC_CONTEXT} {connector} {description}
```

Always starts with semantic context, followed by connector word (with/featuring/showing), then visual description.

### Rules
- Must start with semantic context (exact match)
- Max 50 words, aim for 40-50 for rich detail
- Single sentence, no trailing punctuation
- No "photo of" or "image of"
- Grounded in visible evidence only

### Examples (40-50 words each)

**Example 1** (47 words):
```
TU Delft drawing studio with high barrel-vaulted skylights providing bright diffused natural light throughout the space, multiple rows of white-topped adjustable drafting tables paired with wooden stools arranged on dark rubber flooring, frosted glass partitions along one wall, green chalkboard at rear, creating functional educational workspace
```

**Example 2** (44 words):
```
TU Delft lecture hall featuring tiered seating rows with individual desks and integrated power outlets for laptops, large projection screen and whiteboard combination at front, modern acoustic wall panels in light grey tones, bright overhead fluorescent lighting creating well-lit learning environment
```

**Example 3** (41 words):
```
Hospital emergency room showing pristine white walls and ceiling with recessed lighting, multiple medical equipment stations featuring monitors and IV stands, blue privacy curtained bed areas separated by tracks, bright overhead fluorescent strips, clinical sterile atmosphere with polished linoleum flooring
```

---

## Phase 1: Interior Category (MVP)

### Prompt Template
```
You are annotating images for LoRA fine-tuning of a Flux image model.
Output exactly ONE sentence, maximum 50 words, grounded only in visible evidence.

Your sentence MUST begin with: "{SEMANTIC_CONTEXT}"

After "{SEMANTIC_CONTEXT}", add a natural connector word (with, featuring, showing) and describe in order:
1. Key architectural elements and spatial layout
2. Furniture, objects, and their arrangement
3. Materials, finishes, and colors
4. Lighting conditions and quality
5. Overall atmosphere or character

Aim for 40-50 words to provide rich, specific detail.

Example:
"{SEMANTIC_CONTEXT} with high vaulted ceilings and exposed beams, rows of modern workstations with ergonomic chairs arranged in open layout, polished concrete floors, floor-to-ceiling windows providing abundant natural light, creating bright collaborative atmosphere"

Critical rules:
- Start EXACTLY with: {SEMANTIC_CONTEXT}
- No "photo of" or "image of"
- Maximum 50 words, aim for 40-50
- Single sentence only
- Output only the sentence
```

### User Input

**Field Label**: "Describe the Space *"
**Placeholder**: "TU Delft drawing studio"
**Required**: Yes
**Help**: "Describe what kind of space this is (location + type). This starts the caption."

**Good**: "TU Delft drawing studio", "Hospital emergency room"
**Bad**: "TU Delft" (too vague), "A drawing studio" (has article)

---

## Validation & Regeneration

```python
def validate_caption(caption: str, context: str):
    caption = caption.strip()

    # Remove banned prefixes
    for prefix in ['photo of', 'image of', 'picture of']:
        if caption.lower().startswith(prefix):
            caption = caption[len(prefix):].strip()

    # MUST start with context
    if not caption.startswith(context):
        return regenerate("Must start with: " + context)

    # MUST be ≤50 words
    if len(caption.split()) > 50:
        return regenerate("Condense to max 50 words")

    # Single sentence only
    caption = caption.split('. ')[0]

    # Remove trailing punctuation
    caption = caption.rstrip('.!?,;:')

    return caption
```

---

## Export Format

```
dataset_training.zip
├── img_001.jpg
├── img_001.txt    ← Caption only, no trigger word
├── img_002.jpg
├── img_002.txt
└── README.txt     ← Replicate instructions
```

**README.txt** includes:
- Instructions to add trigger word in Replicate
- Caption format explanation
- Usage examples after training

---

## Implementation Checklist

**Backend**:
- [ ] caption_generator.py: Remove trigger_word, add semantic_context, add Interior template, validation
- [ ] metadata_exporter.py: Remove trigger from captions, add README.txt
- [ ] app.py: Add semantic_context to routes

**Frontend**:
- [ ] index.html: Remove trigger field, add semantic context field, word counter
- [ ] app.js: Send semantic_context, show word count

**Testing**:
- [ ] 5 interior images → verify 40-50 words, start with context, no "photo of"
- [ ] Test export format
- [ ] Test regeneration on failures

---

## Phase 2 (Later)
Add categories: Portrait, Group/Activity, Object, Campus, Urban
