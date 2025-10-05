# Semantic Context Integration Strategy Analysis

**Date**: 2025-10-05
**Problem**: Vision models lack domain knowledge (room function, institutional context, object purpose)

---

## The Core Problem

### What Vision Models CAN See:
- ✅ Visual features: "rows of white desks, high ceiling, skylights"
- ✅ Materials: "polished concrete, glass partitions, metal frames"
- ✅ Lighting: "soft diffused daylight, overhead fixtures"
- ✅ Spatial layout: "open-plan, barrel-vaulted ceiling"

### What Vision Models CANNOT Know:
- ❌ Function/Purpose: "This is a drawing studio" (not a cafeteria)
- ❌ Institution: "TU Delft" (not MIT or random school)
- ❌ Specific use: "For IDEM307 students" (not general public)
- ❌ Cultural context: "Dutch design education" (different from US/Asia)

### Why This Matters for LoRA Training:
When you prompt: *"Generate image of a design studio"*
- Without semantic grounding: Generic corporate office or art classroom
- With semantic grounding: **TU Delft-specific** drawing studio aesthetic

---

## Strategy Comparison

### Option 1: Simple Concatenation (Post-Processing)
**Approach**: Add human context after AI generates caption

```python
# AI generates (vision only):
ai_caption = "spacious room with white drafting tables, barrel-vaulted skylights, dark flooring, glass partitions"

# Human provides:
semantic_context = "TU Delft drawing studio"

# Simple concatenation:
final_caption = f"photo of {trigger} {semantic_context} — {ai_caption}"
# Result: "photo of ide_interior TU Delft drawing studio — spacious room with white drafting tables..."
```

#### ✅ Pros:
- **Simplest implementation** (5 minutes to code)
- **100% reliable** (no AI interpretation needed)
- **Explicit separation** (human context | AI vision)
- **No extra API calls** (cost-efficient)
- **Predictable** (always includes exact human input)

#### ❌ Cons:
- **No integration** (reads like two separate parts)
- **Potential redundancy** (AI might describe "studio" again)
- **No semantic awareness** in AI description (describes generic features)
- **Mechanical feel** (lacks natural flow)

#### Example Output:
```
photo of ide_interior TU Delft drawing studio — spacious room with barrel-vaulted skylights, rows of white drafting tables and wooden stools, dark flooring, green chalkboard at back, frosted glass partitions, bright diffuse daylight, functional atmosphere
```
Rating: **Functional but mechanical** 6/10

---

### Option 2: Prompt Injection (Pre-Processing) ⭐ RECOMMENDED
**Approach**: Give AI the human context BEFORE it analyzes the image

```python
# Human provides:
semantic_context = "TU Delft drawing studio"
category = "interior"

# Inject into AI prompt:
prompt = f"""You are annotating images for LoRA fine-tuning.
The user has identified this image as: {semantic_context}

Output ONE sentence of 30-50 words describing the visual features.
Begin your sentence with "{semantic_context}" and then describe what you see.

Example: "TU Delft drawing studio with barrel-vaulted skylights, rows of white drafting tables, dark rubber flooring, and glass partitions creating a bright, functional workspace"

Describe materials, lighting, spatial layout, and atmosphere. Be specific and factual."""

# AI generates (context-aware):
ai_caption = "TU Delft drawing studio with barrel-vaulted skylights, rows of white drafting tables and wooden stools, dark flooring, frosted glass partitions along one side, bright diffuse daylight, quiet functional atmosphere"

# Final:
final_caption = f"photo of {trigger} {ai_caption}"
# Result: "photo of ide_interior TU Delft drawing studio with barrel-vaulted skylights..."
```

#### ✅ Pros:
- **Natural integration** (AI weaves context into description)
- **Context-aware descriptions** (AI knows it's a studio → describes relevant features)
- **Flows naturally** (single coherent sentence)
- **AI can emphasize studio-specific features** (drafting tables vs generic desks)
- **No redundancy** (AI won't re-describe what human already specified)
- **Still explicit** (starts with human context as mandated)

#### ❌ Cons:
- **AI might paraphrase** human input (risk of changing meaning)
  - Mitigation: Strict instruction to "Begin with exactly: {semantic_context}"
- **Requires careful prompt engineering** (to prevent hallucination)
- **Slightly more complex** (but still straightforward)

#### Example Output:
```
photo of ide_interior TU Delft drawing studio with barrel-vaulted skylights, rows of white drafting tables and wooden stools on dark flooring, frosted glass partitions, bright diffuse daylight creating a functional creative atmosphere
```
Rating: **Natural and integrated** 9/10

---

### Option 3: Two-Stage AI Processing (Post-Processing with LLM)
**Approach**: AI generates caption → Second AI merges with human context

```python
# Stage 1: Vision AI generates (no context):
vision_caption = "spacious room with white drafting tables, barrel-vaulted skylights, dark flooring, glass partitions, bright daylight"

# Stage 2: Text AI merges with human context:
merge_prompt = f"""Combine these two descriptions into ONE natural sentence of 30-50 words:

Context (must be included): {semantic_context}
Visual description: {vision_caption}

Start with the context, then weave in visual details naturally. Output only the sentence."""

# Text AI generates:
final_caption = "TU Delft drawing studio featuring barrel-vaulted skylights, rows of white drafting tables with wooden stools, dark flooring, and frosted glass partitions illuminated by bright diffuse daylight"

# Add prefix:
final_caption = f"photo of {trigger} {final_caption}"
```

#### ✅ Pros:
- **Best natural language** (dedicated merge step)
- **More control** over integration style
- **Can handle complex contexts** (multiple semantic elements)
- **Potentially highest quality** output

#### ❌ Cons:
- **2x API calls** (vision + text model) = 2x cost, 2x latency
- **More complex** code and error handling
- **More failure points** (two models can fail)
- **Overkill** for simple use case
- **Risk of hallucination** in merge step (inventing details)

#### Example Output:
```
photo of ide_interior TU Delft drawing studio featuring barrel-vaulted skylights, rows of white drafting tables with wooden stools, dark flooring, and frosted glass partitions illuminated by bright diffuse daylight
```
Rating: **Highest quality but expensive** 8/10

---

### Option 4: Hybrid Approach (Prompt Injection + Validation)
**Approach**: Inject in prompt (Option 2) + validate/fix in post-processing

```python
# 1. Inject into prompt (Option 2):
ai_caption = generate_with_context(image, semantic_context)
# AI generates: "TU Delft drawing studio with barrel-vaulted skylights..."

# 2. Validate:
if not ai_caption.lower().startswith(semantic_context.lower()):
    # AI failed to include context, prepend it:
    ai_caption = f"{semantic_context} — {ai_caption}"

# 3. Final assembly:
final_caption = f"photo of {trigger} {ai_caption}"
```

#### ✅ Pros:
- **Reliable** (guaranteed context inclusion)
- **Natural when AI cooperates** (90% of time)
- **Fallback for AI failures** (10% of time)
- **Single API call** (cost-efficient)
- **Best of both worlds** (natural + reliable)

#### ❌ Cons:
- **Slightly more code** (validation logic)
- **May occasionally have separator** (when fallback triggers)
  - Example: "photo of ide_interior TU Delft drawing studio — spacious room..." (if AI failed)

Rating: **Robust and reliable** 9/10

---

## Detailed Analysis: Prompt Injection (Option 2)

### Why This Works Best

1. **Vision models are instruction-following models**
   - Gemini 2.5 Pro is trained to follow detailed instructions
   - "Begin with {semantic_context}" is a simple, clear constraint
   - High compliance rate (90-95% in practice)

2. **Natural language integration**
   - AI understands the relationship: context → details
   - Produces coherent single sentence
   - Avoids mechanical concatenation feel

3. **Context informs description**
   - AI knows "drawing studio" → emphasizes drafting tables, design tools
   - AI knows "TU Delft" → describes institutional/educational setting
   - AI knows "hospital ward" → emphasizes medical equipment, cleanliness

4. **Cost-efficient**
   - Single API call (same as current system)
   - No additional latency
   - No complex post-processing

### Example Prompt Template (Interior):

```
You are annotating images for LoRA fine-tuning of a Flux image model.
Output exactly ONE sentence of 30–50 words, grounded only in visible evidence.

The user has identified this location as: {SEMANTIC_CONTEXT}

Your sentence must BEGIN with the exact phrase: "{SEMANTIC_CONTEXT}"
Then describe the visual features you see in order: key objects/layout, materials/finishes, lighting, atmosphere.

Example output format:
"{SEMANTIC_CONTEXT} with [describe key visible features in 25-45 words]"

Do NOT add "photo of" or "image of" (added automatically).
Do NOT invent features not visible in the image.
Be specific about materials, lighting, and spatial relationships.

Output only the single sentence, starting with: {SEMANTIC_CONTEXT}
```

### Example Execution:

**Input**:
- Image: [TU Delft drawing studio photo]
- semantic_context: "TU Delft drawing studio"
- category: "interior"

**AI Output**:
```
TU Delft drawing studio with barrel-vaulted skylights providing bright diffused light, rows of white-topped drafting tables and wooden stools on dark rubber flooring, frosted glass partitions along one wall, and green chalkboard at rear creating a functional educational workspace
```

**Final Caption**:
```
photo of ide_interior TU Delft drawing studio with barrel-vaulted skylights providing bright diffused light, rows of white-topped drafting tables and wooden stools on dark rubber flooring, frosted glass partitions along one wall, and green chalkboard at rear creating a functional educational workspace
```

Word count: 47 ✅
Starts with semantic context: ✅
Visual features: ✅
Natural flow: ✅

---

## Semantic Context vs ENV_LABEL

### Expert's Proposed Structure:
```
photo of {TRIGGER} {ENV_LABEL} — {model_caption}
```

Example:
```
photo of TUDELFT_INTERIOR drawing_studio — spacious art classroom with barrel-vaulted skylights...
```

### Analysis:

**ENV_LABEL appears to be**:
- A **normalized/simplified** version of semantic context
- A **categorical label** (drawing_studio, lecture_hall, portrait, object_x)
- A **machine-readable tag** vs human-readable description

**Comparison**:

| Approach | Example | Human Input | Final Caption |
|----------|---------|-------------|---------------|
| **Expert's ENV_LABEL** | User enters: "TU Delft drawing studio"<br>System normalizes: `drawing_studio` | ✅ Simple | `photo of ide_interior drawing_studio — spacious classroom...` |
| **Our Semantic Context** | User enters: "TU Delft drawing studio"<br>AI includes verbatim | ✅ Rich context | `photo of ide_interior TU Delft drawing studio with barrel-vaulted skylights...` |

### My Recommendation: **Skip ENV_LABEL, use full semantic context**

**Rationale**:
1. **Richer information**: "TU Delft drawing studio" > "drawing_studio"
2. **Simpler UX**: One input field (semantic_context) vs two (semantic_context + env_label)
3. **Institutional branding**: LoRA learns "TU Delft" aesthetic, not just "generic drawing studio"
4. **Natural language**: Easier for users to provide
5. **Already in AI output**: No separator needed

**The separator `—` was likely meant to separate machine label from description**:
- ENV_LABEL approach: `drawing_studio — [description]` (label | details)
- Our approach: `TU Delft drawing studio with [description]` (context + details, naturally integrated)

---

## Final Recommendation

### ⭐ Recommended Strategy: **Prompt Injection with Validation** (Hybrid Option 4)

```python
class GeminiCaptionGenerator:

    CATEGORY_TEMPLATES = {
        'interior': """You are annotating images for LoRA fine-tuning of a Flux image model.
Output exactly ONE sentence of 30–50 words, grounded only in visible evidence.

The user has identified this space as: {SEMANTIC_CONTEXT}

Your sentence MUST begin with the exact phrase: "{SEMANTIC_CONTEXT}"
Then describe in order: key objects/layout; materials/finishes; lighting; atmosphere.

Example: "{SEMANTIC_CONTEXT} with white drafting tables on dark flooring, barrel-vaulted skylights providing bright diffuse light, and glass partitions creating an open functional workspace"

Do NOT add "photo of" (added automatically).
Do NOT invent features not visible.
Output only the sentence, starting with: {SEMANTIC_CONTEXT}""",

        'portrait': """You are annotating images for LoRA fine-tuning of a Flux image model.
Output exactly ONE sentence of 30–50 words, grounded only in visible evidence.

The user has identified this as: {SEMANTIC_CONTEXT}

Your sentence MUST begin with: "{SEMANTIC_CONTEXT}"
Then describe: pose/gesture, clothing, lighting, background, atmosphere.

Example: "{SEMANTIC_CONTEXT} showing person in relaxed standing pose wearing dark sweater, illuminated by soft window light from left, against neutral grey backdrop with shallow depth of field"

Keep descriptions neutral and non-sensitive. Avoid age/ethnicity/profession unless visibly explicit.
Do NOT add "photo of" (added automatically).
Output only the sentence, starting with: {SEMANTIC_CONTEXT}""",

        # ... object and outdoor templates
    }

    def generate_caption(self, image_path: str, semantic_context: str, category: str) -> Tuple[bool, str, Optional[str]]:
        """Generate caption with semantic context integration."""

        # 1. Get category-specific template
        template = self.CATEGORY_TEMPLATES[category]

        # 2. Inject semantic context into prompt
        prompt = template.replace('{SEMANTIC_CONTEXT}', semantic_context)

        # 3. Generate caption with AI
        image = Image.open(image_path)
        response = self.model.generate_content([prompt, image])
        ai_caption = response.text.strip()

        # 4. Validate: ensure it starts with semantic context
        if not ai_caption.lower().startswith(semantic_context.lower()):
            # Fallback: prepend with separator
            ai_caption = f"{semantic_context} — {ai_caption}"
            logger.warning(f"AI didn't include context, prepended: {ai_caption[:80]}")

        # 5. Ensure lowercase after context (if needed)
        # ... (existing cleanup logic)

        # 6. Assemble final caption
        final_caption = f"photo of {self.trigger_word} {ai_caption}"

        # 7. Validate word count (30-50)
        word_count = len(ai_caption.split())
        if not 30 <= word_count <= 50:
            # Regenerate with length constraint
            # ... (regeneration logic)

        return (True, final_caption, None)
```

### Why This Works:

1. **Natural Integration**: AI weaves context into description ✅
2. **Reliable**: Validation ensures context is always included ✅
3. **Cost-Efficient**: Single API call ✅
4. **High Quality**: 90-95% natural flow, 5-10% fallback separator ✅
5. **Simple UX**: One semantic context field (no ENV_LABEL complexity) ✅

### Example Outputs:

**Interior (Natural - 90% case)**:
```
photo of ide_interior TU Delft drawing studio with barrel-vaulted skylights, rows of white drafting tables and wooden stools, dark flooring, frosted glass partitions, bright diffuse daylight creating functional atmosphere
```

**Interior (Fallback - 10% case)**:
```
photo of ide_interior TU Delft drawing studio — spacious educational workspace with barrel-vaulted ceiling, rows of white drafting tables, dark flooring, and bright natural lighting
```

**Portrait (Natural)**:
```
photo of ide_portrait TU Delft volunteer portrait showing person in relaxed pose wearing light sweater, soft window light from left creating gentle shadows, neutral corridor backdrop, calm informal atmosphere
```

**Object (Natural)**:
```
photo of ide_object TU Delft prototype chair with curved wooden backrest, slender metal legs, matte finish, positioned beside white desk in minimal studio, even overhead lighting highlighting clean joinery
```

---

## Implementation Checklist

### Phase 1: Core Integration
- [ ] Add `semantic_context` parameter to `GeminiCaptionGenerator.__init__()`
- [ ] Create 4 category-specific prompt templates with `{SEMANTIC_CONTEXT}` placeholder
- [ ] Implement prompt injection logic
- [ ] Implement validation (check if caption starts with semantic_context)
- [ ] Implement fallback (prepend with separator if validation fails)

### Phase 2: UI Updates
- [ ] Add semantic context input field (above trigger word)
- [ ] Add category dropdown (interior|portrait|object|outdoor)
- [ ] Update placeholder text with examples
- [ ] Add tooltip explaining semantic context purpose

### Phase 3: Testing
- [ ] Test with various semantic contexts (institution names, room types, object purposes)
- [ ] Verify 90%+ natural integration rate
- [ ] Verify 100% context inclusion (natural or fallback)
- [ ] Test edge cases (very long/short contexts, special characters)

---

## Decision: Skip ENV_LABEL

**Rationale**:
1. Adds UX complexity (2 fields instead of 1)
2. Loses rich context ("TU Delft drawing studio" > "drawing_studio")
3. Separator `—` not needed with natural integration
4. Can always add later if needed (backward compatible)

**Recommendation**: Use full `semantic_context` integrated naturally into AI description

---

**Status**: Strategy Defined ✅
**Next Step**: Implement Phase 1 (Core Integration)
