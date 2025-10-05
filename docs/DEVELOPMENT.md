# Developer Guide

This guide is for developers who want to run, modify, or extend the Image Metadata Generator locally.

---

## Quick Start

### 1. Prerequisites

- **Python 3.9+** ([Download](https://www.python.org/downloads/))
- **Git** ([Download](https://git-scm.com/downloads))
- **Gemini API Key** ([Get free key](https://aistudio.google.com/))

### 2. Clone Repository

```bash
git clone https://github.com/kortuem/idem307-image-metadata-generator.git
cd idem307-image-metadata-generator
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies**:
- `Flask==3.0.0` - Web framework
- `google-generativeai>=0.8.0` - Gemini API
- `Pillow>=10.1.0` - Image processing
- `python-dotenv==1.0.0` - Environment variables
- `Werkzeug==3.0.1` - WSGI utilities
- `gunicorn==21.2.0` - Production server

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add:

```bash
# Required: Your Gemini API key
GEMINI_API_KEY=AIza...your_key_here

# Optional: Secret access code for sharing
SECRET_ACCESS_CODE=idem307_2025
```

### 5. Run Locally

```bash
python app.py
```

Open browser to: **http://localhost:5001**

---

## Project Structure

```
image-metadata-generator/
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── .env                      # Local environment (gitignored)
├── .env.example              # Environment template
│
├── utils/                    # Backend modules
│   ├── caption_generator.py  # Gemini API integration
│   ├── image_processor.py    # Image validation/thumbnails
│   ├── validators.py         # Input validation
│   └── metadata_exporter.py  # ZIP file creation
│
├── templates/
│   └── index.html           # Main UI template
│
├── static/
│   ├── css/styles.css       # Application styles
│   └── js/app.js            # Frontend JavaScript
│
├── docs/                    # Documentation
│   ├── ARCHITECTURE.md      # Technical architecture
│   ├── DEPLOYMENT-RENDER.md # Deployment guide
│   └── DEVELOPMENT.md       # This file
│
├── archive/                 # Deprecated files
│   ├── VERCEL_DEPLOYMENT.md
│   └── vercel.json
│
├── README.md                # Project overview
├── TUTORIAL.md              # Student tutorial
└── claude.md                # Claude Code instructions
```

---

## Development Workflow

### Making Changes

1. **Create feature branch**:
```bash
git checkout -b feature/your-feature-name
```

2. **Make changes** and test locally:
```bash
python app.py
# Test in browser at http://localhost:5001
```

3. **Commit changes**:
```bash
git add .
git commit -m "feat: Description of your changes"
```

4. **Push to GitHub**:
```bash
git push origin feature/your-feature-name
```

5. **Test on Render** (if deployed):
   - Merge to `main` branch triggers auto-deploy
   - Monitor deployment in Render dashboard

### Commit Message Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style/formatting
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

**Examples**:
```bash
git commit -m "feat: Add batch delete captions feature"
git commit -m "fix: Correct caption format validation"
git commit -m "docs: Update API endpoint documentation"
```

---

## Testing

### Manual Testing Checklist

**Upload Flow**:
- [ ] Drag-and-drop upload works
- [ ] File input upload works
- [ ] Progress bar shows during upload
- [ ] Thumbnails display correctly
- [ ] Invalid files are rejected
- [ ] Error messages are clear

**Caption Generation**:
- [ ] API key validation works
- [ ] Secret access code works
- [ ] Captions format correctly: `photo of {trigger_word} ...`
- [ ] Progress updates during generation
- [ ] Error handling for API failures
- [ ] 2-second delay between requests

**Editing**:
- [ ] Previous/Next navigation works
- [ ] Caption editing saves correctly
- [ ] Image display matches caption
- [ ] Keyboard shortcuts work (if implemented)

**Export**:
- [ ] ZIP file downloads
- [ ] Contains correct files (image + .txt pairs)
- [ ] Caption .txt files have correct format
- [ ] Filename is `{trigger_word}_training.zip`

### Testing with Example Datasets

Use the example datasets from README.md:
- [IDE Drawing Studio](https://www.dropbox.com/scl/fi/a0a4qglv2xfd16hzdulnp/IDE-Drawing-Studio.zip?rlkey=uaoo41ldb8nnbgul8yn9er7m3&dl=0)
- [IDE Main Hall](https://www.dropbox.com/scl/fi/hq8pvb85977d675yynrjf/IDE-Main-Hall.zip?rlkey=oi2zhq6ot0htq5ftogmllkn9w&dl=0)

### API Testing

Test Gemini API integration:

```python
# Test script: test_gemini.py
import os
from dotenv import load_dotenv
from utils.caption_generator import generate_caption

load_dotenv()

# Test with local image
with open('test_image.jpg', 'rb') as f:
    image_data = f.read()

caption = generate_caption(
    image_data=image_data,
    trigger_word='test_room',
    api_key=os.getenv('GEMINI_API_KEY')
)

print(f"Generated caption: {caption}")
assert caption.startswith('photo of test_room ')
print("✅ Test passed!")
```

Run:
```bash
python test_gemini.py
```

---

## Debugging

### Enable Flask Debug Mode

Edit `app.py`:
```python
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True  # ← Enable debug mode
    )
```

**Features**:
- Auto-reload on code changes
- Detailed error pages
- Interactive debugger in browser

### View Logs

**Local**:
```bash
python app.py
# Logs print to terminal
```

**Render.com**:
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click your service
3. Click **Logs** tab
4. Filter by log level (Info, Error, etc.)

### Common Issues

#### "No module named 'google.generativeai'"
**Solution**:
```bash
pip install -r requirements.txt
```

#### "API key not found"
**Solution**:
- Check `.env` file exists
- Verify `GEMINI_API_KEY` is set
- Don't use quotes around value

#### "Invalid session ID"
**Solution** (shouldn't happen on Render):
- Restart Flask app
- Clear browser cache
- Check `/tmp/sessions/` exists

#### Port already in use
**Solution**:
```bash
# Find process using port 5001
lsof -i :5001

# Kill process
kill -9 <PID>

# Or change port in app.py
app.run(port=5002)
```

---

## Modifying Components

### Adding New Route

Edit `app.py`:

```python
@app.route('/api/new_endpoint', methods=['POST'])
def new_endpoint():
    """Your new API endpoint"""
    try:
        data = request.get_json()
        # Your logic here
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### Modifying Caption Prompt

Edit `utils/caption_generator.py`:

```python
def generate_caption(image_data, trigger_word, api_key):
    # Modify prompt here
    prompt = f"""Analyze this image and create a caption.

    Format: photo of {trigger_word} [your new instructions]

    Rules:
    - [Your new rules]
    """
    # ... rest of function
```

### Changing UI Styles

Edit `static/css/styles.css`:

```css
/* Example: Change primary color */
:root {
    --primary-color: #2563eb;  /* Change this */
    --primary-hover: #1d4ed8;
}
```

### Adding Frontend Features

Edit `static/js/app.js`:

```javascript
// Example: Add keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight') {
        nextImage();
    } else if (e.key === 'ArrowLeft') {
        previousImage();
    }
});
```

---

## Performance Optimization

### Current Performance

- **Upload**: ~100ms for 30 images (5MB)
- **Caption generation**: ~18s per image (Gemini 2.5 Pro)
- **Export**: ~2s for 30 images

### Optimization Ideas

**1. Faster Caption Generation**:
```python
# Switch to Gemini 2.5 Flash for speed
MODEL = "gemini-2.5-flash"  # ~5-7s per image
# Trade-off: Lower quality
```

**2. Parallel Processing** (requires refactor):
```python
# Process multiple images concurrently
# Requires: queue system, worker processes
# Trade-off: More complex code
```

**3. Image Compression**:
```python
# Compress images before base64 encoding
# In utils/image_processor.py
def compress_image(image, max_size_mb=1):
    # Resize if too large
    # Reduce quality
    # Trade-off: Quality vs size
```

---

## Deployment

### Deploy to Render.com

See [docs/DEPLOYMENT-RENDER.md](DEPLOYMENT-RENDER.md) for detailed instructions.

**Quick Deploy**:
1. Push to GitHub
2. Create Render web service
3. Connect GitHub repo
4. Set environment variables
5. Deploy

### Environment Variables (Production)

Set in Render dashboard:

```bash
GEMINI_API_KEY=your_production_key
SECRET_ACCESS_CODE=idem307_2025
```

### Auto-Deploy on Push

Render auto-deploys when you push to `main`:

```bash
git push origin main
# Render detects push → builds → deploys (2-5 min)
```

Monitor deployment:
- Render Dashboard → Your Service → Events tab

---

## Code Style Guidelines

### Python (PEP 8)

```python
# Good
def generate_caption(image_data: bytes, trigger_word: str, api_key: str) -> str:
    """Generate AI caption for image.

    Args:
        image_data: Binary image data
        trigger_word: LoRA trigger word
        api_key: Gemini API key

    Returns:
        Formatted caption string
    """
    # Implementation
    pass

# Use type hints
# Clear docstrings
# 4 spaces indentation
```

### JavaScript (Modern ES6+)

```javascript
// Good
const generateCaptions = async () => {
    const response = await fetch('/api/generate_caption', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({session_id: sessionId})
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
};

// Use const/let (not var)
// Async/await over callbacks
// Clear error handling
```

### CSS

```css
/* Good - BEM naming convention */
.caption-editor__input {
    padding: 0.5rem;
    border: 1px solid var(--border-color);
}

.caption-editor__input--error {
    border-color: var(--error-color);
}

/* Use CSS variables for colors */
/* Mobile-first responsive design */
```

---

## Adding Features

### Example: Add "Clear All Captions" Button

**1. Backend** (`app.py`):
```python
@app.route('/clear_captions', methods=['POST'])
def clear_captions():
    """Clear all captions in session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')

        session_file = f"/tmp/sessions/{session_id}.json"
        with open(session_file, 'r') as f:
            session_data = json.load(f)

        # Clear all captions
        for image in session_data['images']:
            image['caption'] = ''

        # Save
        with open(session_file, 'w') as f:
            json.dump(session_data, f)

        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**2. Frontend** (`static/js/app.js`):
```javascript
async function clearAllCaptions() {
    if (!confirm('Clear all captions? This cannot be undone.')) {
        return;
    }

    const response = await fetch('/clear_captions', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({session_id: appState.sessionId})
    });

    if (response.ok) {
        // Update UI
        appState.images.forEach(img => img.caption = '');
        renderEditor();
    }
}
```

**3. UI** (`templates/index.html`):
```html
<button onclick="clearAllCaptions()" class="btn btn-danger">
    Clear All Captions
</button>
```

---

## Security Best Practices

### Never Commit Secrets

`.gitignore` includes:
```
.env
static/uploads/*
/tmp/sessions/*
```

**Always**:
- Use `.env` for secrets
- Check `.gitignore` before committing
- Rotate secrets periodically

### Input Validation

Always validate user input:

```python
# Example: Trigger word validation
def validate_trigger_word(word):
    if not word or len(word) < 3 or len(word) > 50:
        raise ValueError("Trigger word must be 3-50 characters")

    if not re.match(r'^[a-zA-Z0-9_]+$', word):
        raise ValueError("Only alphanumeric and underscore allowed")

    return word.lower()
```

### API Rate Limiting

Respect Gemini API limits:

```python
# Built-in 2-second delay
import time

for image in images:
    caption = generate_caption(image)
    time.sleep(2)  # Rate limiting
```

---

## Troubleshooting Development Issues

### Python Version Issues

```bash
# Check Python version
python --version  # Should be 3.9+

# Use virtual environment
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### Port Conflicts

```bash
# Find what's using port 5001
lsof -i :5001

# Kill process
kill -9 <PID>

# Or use different port
python app.py --port 5002
```

### Session File Permissions

```bash
# Ensure /tmp/sessions/ is writable
mkdir -p /tmp/sessions
chmod 755 /tmp/sessions
```

---

## Contributing

### Contribution Workflow

1. **Fork** repository
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes** and test
4. **Commit**: `git commit -m "feat: Add amazing feature"`
5. **Push**: `git push origin feature/amazing-feature`
6. **Open Pull Request** on GitHub

### Pull Request Guidelines

- Clear description of changes
- Reference any related issues
- Include testing notes
- Update documentation if needed

---

## Resources

### Documentation
- [Flask Docs](https://flask.palletsprojects.com/)
- [Gemini API Docs](https://ai.google.dev/docs)
- [Render Docs](https://render.com/docs)

### Project Docs
- [README.md](../README.md) - Project overview
- [TUTORIAL.md](../TUTORIAL.md) - Student guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical architecture
- [DEPLOYMENT-RENDER.md](DEPLOYMENT-RENDER.md) - Deployment guide

### Contact
- **Maintainer**: Prof. Gerd Kortuem
- **Email**: g.w.kortuem@tudelft.nl
- **GitHub**: https://github.com/kortuem/idem307-image-metadata-generator

---

**Last Updated**: January 2025 (v1.0)
