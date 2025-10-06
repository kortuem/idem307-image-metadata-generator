# Image Metadata Generator - Student Tutorial

**By Prof. Gerd Kortuem** - TU Delft, Faculty of Industrial Design Engineering
**Course**: [IDEM307 Generative AI and Design](https://studiegids.tudelft.nl/courses/study-guide/educations/12452)
**Contact**: g.w.kortuem@tudelft.nl

**🌐 Access the tool**: https://idem307-image-metadata-generator.onrender.com/

This tutorial will guide you through preparing your image dataset for FLUX LoRA fine-tuning on Replicate.com.

---

## What You'll Need

✅ **20-40 images** of the same subject/space (JPG or PNG format)
✅ **Access code** from your instructor (or your own Gemini API key)
✅ **~10-15 minutes** of time

---

## What This Tool Does

The Image Metadata Generator automatically creates detailed, AI-generated captions for your images in the format required by Replicate.com for FLUX LoRA training.

**Example caption:**
```
TU Delft drawing studio with high vaulted ceilings and skylights, rows of white
adjustable drawing tables with wooden stools, dark flooring, translucent partition
walls, abundant natural light creating bright functional workspace
```

Each image gets a unique, descriptive caption starting with your semantic context. Replicate handles trigger words automatically during training.

---

## Example Datasets (Practice First!)

Before using your own images, try the tool with these example datasets from TU Delft campus spaces:

**Original Images** (for practicing caption generation):
- [IDE Drawing Studio](https://github.com/kortuem/idem307-image-metadata-generator/tree/main/__images/image%20data%20sets/IDE%20Drawing%20Studio) (24 images)
- [IDE Lecture Hall](https://github.com/kortuem/idem307-image-metadata-generator/tree/main/__images/image%20data%20sets/IDE%20Lecture%20Hall) (39 images)
- [IDE Main Hall](https://github.com/kortuem/idem307-image-metadata-generator/tree/main/__images/image%20data%20sets/IDE%20Main%20Hall) (39 images)
- [IDE Studio](https://github.com/kortuem/idem307-image-metadata-generator/tree/main/__images/image%20data%20sets/IDE%20Studio) (47 images)
- [SDE Hallway](https://github.com/kortuem/idem307-image-metadata-generator/tree/main/__images/image%20data%20sets/SDE%20Hallway) (38 images)

**Training-Ready Examples** (see what good output looks like):
Browse the [training datasets with captions](https://github.com/kortuem/idem307-image-metadata-generator/tree/main/__images) to see examples of properly formatted caption files. These show exactly what your exported ZIP should contain!

**How to use:**
1. Click on any dataset link above
2. Click "Download ZIP" (green button) or download individual images
3. Extract and follow the steps below!

---

## Step-by-Step Instructions

### Step 1: Prepare Your Images

**Image Requirements:**
- ✅ **Format**: JPG, JPEG, or PNG
- ✅ **Quantity**: 20-40 images (Replicate recommends 12-20, but more is better)
- ✅ **Resolution**: Minimum 512x512, ideally 1024x1024 or larger
- ✅ **Aspect ratio**: Any aspect ratio works - Replicate auto-resizes
- ✅ **Size**: Max 10MB per image (100MB total upload)
- ✅ **Subject**: All images of the SAME subject/space/person

**Tips for good training data:**
- Use high-resolution images (1024x1024+ recommended)
- Include close-ups AND wide shots
- Capture different angles, lighting, and perspectives
- Show variety in settings and compositions
- Ensure images are sharp and well-lit (not blurry or dark)
- Different aspect ratios are fine - no need to crop

---

### Step 2: Open the Tool

Go to: **https://idem307-image-metadata-generator.onrender.com/**

**First time?** The page may take 20-30 seconds to load (the server "wakes up" from sleep). This only happens if nobody has used it recently.

---

### Step 3: Upload Your Images

1. Click the **upload area** (or drag and drop images)
2. Select 20-40 images from your folder
3. Wait for upload to complete (~5-10 seconds)
4. You'll see: **"✓ Uploaded X images"**

**What happens:**
- Images are validated (correct format, not corrupted)
- Thumbnails are created for preview
- Upload progress bar shows percentage

---

### Step 4: Select Image Category

Choose the category that best matches your images:

- **Interior/Architecture** - Rooms, spaces, interior environments
- **Person/Portrait** - Individual person photos
- **People/Groups** - Multiple people, group activities
- **Object/Product** - Items, tools, designed objects
- **Vehicle/Machine** - Cars, bikes, robots
- **Exterior/Building** - Building facades, architectural exteriors
- **Scene/Landscape** - Nature, outdoor scenes
- **Abstract/Artwork** - Sketches, diagrams, digital art

This ensures the AI uses the right descriptive vocabulary for your images.

---

### Step 5: Enter Semantic Context

**What is semantic context?**
A short description that will start every caption. This helps the AI understand what it's looking at.

**Examples:**
- For IDE Main Hall: `TU Delft main hall`
- For a lecture room: `Lecture room B`
- For a person named John: `John Smith`
- For your design studio: `Modern design studio`

**Rules:**
- ✅ Max 50 characters
- ✅ Be specific and descriptive
- ✅ Will appear at start of every caption

**Type your semantic context** in the "Semantic Context" field.

---

### Step 6: Enter Access Code

In the **"Gemini API Key or Access Code"** field:

**Option A - Use Instructor's Code:**
- Enter the access code provided by your instructor
- For IDEM307 students: `idem307_2025`

**Option B - Use Your Own API Key:**
- Get a free API key at: https://aistudio.google.com/
- Sign in with Google account
- Click "Get API Key" → "Create API Key"
- Copy and paste into the field

---

### Step 7: Generate Captions

1. Click **"Generate Captions"** button
2. Watch the progress: **"Processing X of Y..."**
3. Each image takes ~5-10 seconds to process
4. Total time: ~4-8 minutes for 30 images

**What's happening:**
- AI analyzes each image using category-specific prompts
- Generates detailed description starting with your semantic context
- Saves caption for export

**Optional - Slow Mode:**
If the server is busy or you see errors, check the **"🐢 Slow Mode"** box. This adds a 3-second delay between requests.

**☕ Take a break!** Come back in 5-10 minutes.

---

### Step 8: Review Captions (Optional)

After generation completes:

1. Click on any thumbnail to see its caption
2. Edit the caption if needed (click in text area)
3. Changes save automatically
4. Use arrow keys to navigate between images

**Most captions are good!** You typically only need to edit 10-20% of them.

**When to edit:**
- Caption is too generic
- Missed important details
- Incorrect description
- You want to emphasize something specific

---

### Step 9: Export Training ZIP

1. Click **"Preview Metadata"** to see all captions (optional)
2. Click **"Export Training Data"**
3. Download the ZIP file
4. File name: `[semantic_context]_training.zip`

**What's in the ZIP:**
```
tu_delft_drawing_studio_training.zip
├── image1.jpg
├── image1.txt          ← Caption for image1
├── image2.jpg
├── image2.txt          ← Caption for image2
└── ...
```

Each image has a matching `.txt` file with its caption. **No README.txt** - just images and captions ready for Replicate.

---

### Step 10: Upload to Replicate

1. Go to: https://replicate.com/
2. Sign in (create account if needed)
3. Navigate to **FLUX LoRA training**
4. Upload your ZIP file
5. Enter your **trigger word** (e.g., `ide_main_hall`)
6. Start training!

**Important**: Replicate adds your trigger word automatically during training. Your captions don't include it - that's correct!

**Using your trained model:**
When generating images, use prompts like:
```
ide_main_hall with students working
ide_main_hall at sunset
ide_main_hall empty and quiet
```

The AI will generate images in the style of your training data!

---

## Troubleshooting

### "Page won't load"
**Solution**: First time may take 30 seconds (server waking up). Refresh and wait.

### "Upload seems stuck"
**Solution**:
- Hard refresh browser (Cmd+Shift+R or Ctrl+Shift+F5)
- Check your internet connection
- Try smaller batch (20 images instead of 40)

### "API key or access code required"
**Solution**:
- Use access code: `idem307_2025` (for IDEM307 students)
- Or get your own free API key: https://aistudio.google.com/

### "Captions not generating"
**Solution**:
- Wait ~8-12 seconds per image (using Gemini 2.5 Flash)
- Check browser console (F12) for errors
- Verify you entered semantic context and API key/access code
- Try refreshing and starting over

### "Download doesn't work"
**Solution**:
- Check your browser's download folder
- Try a different browser (Chrome, Firefox, Safari)
- Disable ad blockers temporarily

---

## Tips for Best Results

### Image Selection
✅ **Good**: Varied angles, lighting, compositions
❌ **Bad**: All images look exactly the same

✅ **Good**: Clear, high-quality images
❌ **Bad**: Blurry, dark, low-resolution

✅ **Good**: 30-40 images
❌ **Bad**: Less than 20 images

### Trigger Words
✅ **Good**: `ide_main_hall`, `john_smith`, `studio_a`
❌ **Bad**: `hall`, `person`, `room` (too generic)

### Caption Editing
✅ **Edit**: Generic descriptions, obvious errors
❌ **Don't edit everything**: AI does a good job!

---

## Example Caption Quality

**Image**: Photo of an empty architecture studio with drafting tables

**AI-Generated Caption** (with semantic context: "TU Delft drawing studio"):
```
TU Delft drawing studio featuring a prominent arched barrel-vaulted ceiling
with exposed dark metal trusses and large translucent skylights that cast
even, diffused daylight across a dark grey linoleum floor, where a long row
of high-top workbenches and chrome-based stools with wooden seats are arranged
along a light wood-paneled wall, creating a bright and functional workspace
```

**Quality**: ✅ Detailed, specific, professional - perfect for training!

---

## FAQ

**Q: How long does it take?**
A: ~10 minutes for 30 images (18 seconds per image)

**Q: Can I use my phone photos?**
A: Yes! Just make sure they're good quality and all the same subject.

**Q: What if I don't like a caption?**
A: Click the image thumbnail and edit the caption manually.

**Q: Can I process multiple datasets?**
A: Yes! Just refresh the page and start over with new images.

**Q: Is my data private?**
A: Images are processed by Google's Gemini AI and deleted after you download the ZIP. They're not stored permanently.

**Q: Can I use this for commercial projects?**
A: Yes! The tool is MIT licensed - free to use.

**Q: What's the best trigger word?**
A: Something unique and descriptive. If training on "IDE Main Hall", use `ide_main_hall` not just `hall`.

---

## Getting Help

**For IDEM307 Students:**
- Ask your instructor during class
- Post in the course forum
- Email: g.w.kortuem@tudelft.nl

**Technical Issues:**
- Check browser console (F12) for errors
- Try different browser
- Clear browser cache

**GitHub Repository:**
https://github.com/kortuem/idem307-image-metadata-generator

---

## What's Next?

After downloading your training ZIP:

1. **Upload to Replicate**: https://replicate.com/
2. **Train your FLUX LoRA** (~20-30 minutes training time)
3. **Generate images** using your trigger word
4. **Experiment** with different prompts
5. **Share** your results with the class!

---

**Good luck with your AI image generation project!** 🎨✨

*Developed by Prof. Gerd Kortuem with Claude Code*
*TU Delft - IDEM307 Generative AI and Design*
