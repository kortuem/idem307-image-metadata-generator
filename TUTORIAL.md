# Image Metadata Generator - User Tutorial

## What is This Tool?

The **Image Metadata Generator** is a web application that automatically creates detailed, AI-generated descriptions for your images. It's primarily designed to help you prepare training data for fine-tuning AI image models (like FLUX on Replicate.com), but it can also be used for:

- Creating detailed image captions for machine learning datasets
- Generating descriptive metadata for image libraries
- Building training data for custom AI models
- Archiving images with rich textual descriptions

The tool uses Google's advanced **Gemini 2.5 Pro AI model** to analyze your images and generate professional, detailed descriptions that capture:
- The main subject and objects
- The environment and setting
- Photographic style and composition
- Colors, materials, and textures
- Spatial relationships between elements
- Mood and atmosphere

---

## How It Works (Simple Overview)

1. **Upload your images** → The tool stores them temporarily
2. **Choose a trigger word** → A unique identifier for your image set
3. **Generate captions** → AI analyzes each image and writes a detailed description
4. **Review & edit** → Manually refine any captions if needed
5. **Download** → Get a ready-to-use ZIP file for Replicate or other platforms

---

## Step-by-Step Instructions

### Step 1: Upload Your Images

1. Open the application in your web browser (typically at `http://127.0.0.1:5001`)
2. Click the **"Choose Files"** button or drag-and-drop images onto the upload area
3. Select all the images you want to caption (you can select multiple files at once)
4. Wait for the upload confirmation showing how many images were accepted

**Image Requirements:**
- ✅ **Formats supported:** JPG, JPEG, PNG, WebP, MPO
- ✅ **Resolution:** 1024×1024 pixels or higher recommended
- ✅ **Aspect ratio:** Any (square, landscape, portrait all work)
- ✅ **File size:** Individual images should be under 7MB
- ✅ **Quantity:** Minimum 2 images, recommended 10-25 images for fine-tuning

**Example:**
If you're preparing to fine-tune an AI model to generate images of "a modern architecture studio," you'd upload 10-25 photos of that space from different angles and lighting conditions.

---

### Step 2: Enter a Trigger Word

After uploading, you'll see a text field labeled **"Trigger Word"**.

**What is a trigger word?**
A trigger word is a unique identifier that will be added to all your image descriptions. When you later use your fine-tuned AI model, you'll use this word in prompts to activate your custom training.

**Rules for trigger words:**
- ✅ Must be unique (not a common word like "dog" or "photo")
- ✅ Use underscores instead of spaces: `my_studio` not `my studio`
- ✅ Keep it memorable and descriptive: `ide_drawing_studio` or `zeke_portrait`
- ✅ Avoid generic terms like `TOK` (conflicts with other models)
- ✅ Can use capital letters for clarity: `IDE_STUDIO` or `ide_studio` both work

**Examples of good trigger words:**
- `ide_drawing_studio` (for an interior design studio)
- `zeke_portrait` (for portraits of a person named Zeke)
- `vintage_car_1965` (for a specific vintage car)
- `my_product_v2` (for product photography)

The tool will validate your trigger word in real-time and show a green checkmark when it's valid.

---

### Step 2.5: Enter API Key or Access Code (REQUIRED)

The **"🔑 API Key (Required)"** section will be open by default. You must provide either an access code or your own API key.

**How it works:**
- **Have an access code?** Enter it in the password field (provided separately by the tool maintainer)
- **Need your own API key?** Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/) and enter it here

**Important:** This field is required. The tool uses the Google Gemini 2.5 Pro API, which requires authentication. You cannot generate captions without either an access code or your own API key.

---

### Step 3: Generate Captions

1. Click the **"Generate Captions"** button
2. Watch the progress bar update in real-time as each image is processed
3. The debug console will show which image is being processed (e.g., "Processing 1/24")

**How long does this take?**
- Each image takes approximately **15-20 seconds** to process
- For 24 images, expect **7-8 minutes** total
- The AI is performing deep analysis for maximum quality, so the wait is worth it!

**What's happening behind the scenes?**
The Gemini 2.5 Pro AI model:
1. Analyzes the visual content of each image
2. Identifies subjects, objects, materials, and spatial relationships
3. Determines photographic style, lighting, and mood
4. Generates a single, detailed sentence describing everything

---

### Step 4: Review and Edit Captions

Once generation is complete:

1. The **Caption Editor** section appears automatically
2. Use the ◀ **Previous** and **Next** ▶ buttons to navigate between images
3. Each image shows:
   - The image preview
   - The AI-generated caption
   - An editable text area where you can refine the description

**Why would you edit a caption?**
- Fix any misidentified objects or details
- Adjust emphasis on certain features
- Correct style descriptions
- Make the description more specific to your needs

**Example of what you'll see:**

For an image named `ide_drawing_studio - 1.jpeg`, the AI might generate:

```
photo of ide_drawing_studio A wide-angle shot of an empty architecture
studio under a high, arched ceiling with exposed black steel trusses and
large skylights that provide bright, diffuse overhead lighting, featuring
neat rows of white-topped adjustable drafting tables with weathered metal
bases and simple wooden stools on a dark grey floor, all set against a
wall of translucent frosted glass panels in black frames, creating a
functional, organized, and quietly industrious atmosphere
```

Notice how the description includes:
- **Trigger word:** `ide_drawing_studio` (appears right after "photo of")
- **Camera angle:** "wide-angle shot"
- **Subject:** "empty architecture studio"
- **Environment:** "high, arched ceiling with exposed black steel trusses"
- **Lighting:** "bright, diffuse overhead lighting" from "large skylights"
- **Details:** "white-topped adjustable drafting tables," "wooden stools," "dark grey floor"
- **Materials:** "translucent frosted glass panels in black frames"
- **Mood:** "functional, organized, and quietly industrious atmosphere"

This level of detail helps AI models learn exactly what makes your subject unique.

---

### Step 5: Export Your Training Data

Once you're satisfied with all captions:

1. Click the **"Export Training Data"** button
2. A ZIP file will download automatically (named `[your_trigger_word]_training.zip`)
3. This ZIP file is ready to upload to Replicate.com or other training platforms

**What's inside the ZIP file?**

The ZIP contains:
- ✅ All your original images (JPEG format)
- ✅ Individual `.txt` files for each image with matching filenames

**Example ZIP structure:**
```
ide_drawing_studio_training.zip
├── ide_drawing_studio - 1.jpeg
├── ide_drawing_studio - 1.txt
├── ide_drawing_studio - 2.jpeg
├── ide_drawing_studio - 2.txt
├── ide_drawing_studio - 3.jpeg
├── ide_drawing_studio - 3.txt
└── ... (etc.)
```

**Why this format?**
Replicate.com (and most AI training platforms) expect:
- Each image paired with a text file of the same name
- The text file contains the caption/description
- All files at the root level of the ZIP (no subfolders)

---

## Using Your Training Data on Replicate.com

### Quick Guide to Fine-Tuning FLUX

1. Go to https://replicate.com/replicate/fast-flux-trainer/train
2. Upload your ZIP file to the **"input_images"** field
3. Enter your **trigger word** in the **"trigger_word"** field
4. Select **"subject"** for the **"lora_type"** (or "style" if training on artistic style)
5. Leave **"training_steps"** at **1000**
6. Click **"Create training"**

**Cost:** Approximately **$1.50 USD** for ~2 minutes of training on 20-25 images

Once training completes, you can generate new images using prompts like:
```
photo of ide_drawing_studio as a futuristic space station classroom,
cyberpunk style, neon lighting
```

The AI will generate images that maintain the architectural characteristics of your original studio while applying the new creative direction.

---

## Troubleshooting

### "Processing takes too long"
- **Normal:** Gemini 2.5 Pro takes 15-20 seconds per image for maximum quality
- **Expected time:** 7-8 minutes for 24 images
- **Speed option:** Contact the developer to switch to Gemini 2.5 Flash (faster but slightly less detailed)

### "Trigger word is invalid"
- Make sure you're not using common words
- Use underscores instead of spaces
- Avoid special characters except underscores
- Don't use `TOK` (reserved word)

### "Image upload failed"
- Check that images are under 7MB each
- Ensure you're using supported formats (JPG, PNG, WebP)
- Try uploading fewer images at once if you have many large files

### "Caption doesn't match my image"
- Use the caption editor to manually correct any errors
- The AI is very accurate but may occasionally misidentify details
- Your manual edits will be preserved in the exported ZIP

---

## Best Practices for Fine-Tuning

### Image Selection
- ✅ Use 10-25 high-quality images minimum
- ✅ Include variety: different angles, lighting, times of day
- ✅ Keep consistent subject: same space, person, or object
- ✅ Use 1024×1024 or higher resolution

### Trigger Word Strategy
- ✅ Make it unique and memorable
- ✅ Related to your subject: `my_studio`, `brand_logo`, `pet_name`
- ✅ Short but descriptive: 2-3 words max

### Caption Quality
- ✅ Let the AI generate detailed descriptions (don't oversimplify)
- ✅ Review each caption to catch any errors
- ✅ Keep descriptions factual and detailed
- ✅ Don't remove important spatial or material details

---

## Additional Use Cases

While this tool is optimized for Replicate.com fine-tuning, you can also use it for:

### 1. Image Dataset Documentation
Generate detailed metadata for research or archival image collections

### 2. Accessibility
Create comprehensive alt-text descriptions for visually impaired users

### 3. E-commerce
Generate detailed product descriptions from product photos

### 4. Content Management
Auto-tag and describe images in large media libraries

### 5. Training Data for Other Platforms
Export format works with many AI training tools beyond Replicate

---

## Technical Details (For Advanced Users)

### AI Model
- **Model:** Google Gemini 2.5 Pro
- **Strengths:** Deep reasoning, nuanced analysis, complex scene understanding
- **API:** `google-generativeai` Python library (version 0.8+)

### Caption Format
All captions follow this structure:
```
photo of [TRIGGER_WORD] [detailed single-sentence description including
subject, environment, style, materials, spatial relationships, and mood]
```

### Processing Pipeline
1. Image upload → Flask backend stores in temporary session folder
2. Trigger word validation → Real-time API check
3. Caption generation → Gemini API call per image with expert prompt
4. MPO conversion → iPhone MPO format auto-converted to JPEG
5. Export → ZIP creation with individual .txt files per image

### Rate Limiting
- 2-second delay between Gemini API calls (prevents throttling)
- Exponential backoff on API failures (3 retry attempts)

---

## Support

For issues, questions, or feature requests:
- Check the troubleshooting section above
- Review server logs in the terminal/console
- Report issues on the project's GitHub repository

---

## Example Workflow Summary

**Goal:** Fine-tune FLUX to generate images of my architecture studio

1. ✅ Photograph my studio from 20 different angles (1024×1024 JPEGs)
2. ✅ Open Image Metadata Generator in browser
3. ✅ Upload all 20 images
4. ✅ Enter trigger word: `ide_drawing_studio`
5. ✅ Click "Generate Captions" and wait ~6 minutes
6. ✅ Review captions, edit 2-3 that need refinement
7. ✅ Click "Export Training Data"
8. ✅ Upload `ide_drawing_studio_training.zip` to Replicate
9. ✅ Train FLUX model for ~2 minutes ($1.50)
10. ✅ Generate new creative images: "photo of ide_drawing_studio as an underwater research lab"

**Result:** A custom AI model that generates images maintaining my studio's architectural style while applying any creative scenario I imagine!

---

*Last updated: October 2025*
