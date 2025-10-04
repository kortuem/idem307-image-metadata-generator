# Render.com Deployment Guide

**Recommended deployment platform** for the Image Metadata Generator.

Render is better suited for this app than Vercel because it supports long-running processes and persistent sessions.

## Prerequisites

- GitHub repository: `kortuem/idem307-image-metadata-generator` (✅ Done)
- Render account (free tier works great)
- Gemini API key from [Google AI Studio](https://aistudio.google.com/)

---

## Step 1: Create Render Account

1. Go to [render.com](https://render.com)
2. Click **"Get Started"** or **"Sign Up"**
3. Sign up with GitHub (recommended - easiest integration)

---

## Step 2: Create New Web Service

1. From Render Dashboard, click **"New +"** → **"Web Service"**
2. Connect your GitHub account if not already connected
3. Find and select repository: `kortuem/idem307-image-metadata-generator`
4. Click **"Connect"**

---

## Step 3: Configure Web Service

Fill in these settings:

### Basic Settings
- **Name**: `image-metadata-generator` (or your choice)
- **Region**: Choose closest to you
- **Branch**: `main`
- **Runtime**: **Python 3**

### Build & Deploy Settings
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`

### Instance Type
- Select: **Free** (works perfectly for this app!)
  - Free tier includes:
    - 512 MB RAM
    - Shared CPU
    - No sleep/timeout limits (unlike Vercel!)

---

## Step 4: Add Environment Variables

Click **"Advanced"** → **"Add Environment Variable"** and add these:

### Variable 1: GEMINI_API_KEY
- **Key**: `GEMINI_API_KEY`
- **Value**: Your Gemini API key from Google AI Studio (starts with `AIza...`)

### Variable 2: SECRET_ACCESS_CODE
- **Key**: `SECRET_ACCESS_CODE`
- **Value**: Your chosen secret code (e.g., `idem307_spring2025`)
  - This is what students enter instead of bringing their own API key
  - Choose something memorable but not easily guessable

---

## Step 5: Deploy

1. Click **"Create Web Service"**
2. Render will:
   - Clone your repository
   - Install dependencies
   - Start the Flask app
   - This takes 2-5 minutes

3. Watch the deployment logs in real-time
4. When you see: **"Your service is live 🎉"** → deployment succeeded!

---

## Step 6: Get Your App URL

Your app will be available at:
```
https://image-metadata-generator-XXXXX.onrender.com
```

(Replace `XXXXX` with your unique Render ID)

Copy this URL and share with students!

---

## Step 7: Test the Deployment

1. Open your Render URL
2. Upload 2-3 test images
3. Enter trigger word: `test_room`
4. Enter your SECRET_ACCESS_CODE in the API Key field
5. Click **"Generate Captions"**
6. Verify captions generate successfully (~18 seconds per image)
7. Export ZIP file and verify contents

---

## Updating Your App

When you push changes to GitHub:

1. `git add .`
2. `git commit -m "Your update message"`
3. `git push`
4. Render automatically detects the push and redeploys (2-5 minutes)

---

## Monitoring & Logs

### View Live Logs
1. Go to Render Dashboard
2. Click your service name
3. Click **"Logs"** tab
4. See real-time application logs (useful for debugging)

### Check Service Status
- Dashboard shows: **"Live"** (green) = working
- Shows last deployment time
- Shows resource usage

---

## Troubleshooting

### "Application Error" on page load
**Solution**: Check logs for Python errors. Usually missing dependency or environment variable.

```bash
# Check logs in Render Dashboard → Logs tab
# Look for error messages in red
```

### Caption generation fails
**Solution**: Check that GEMINI_API_KEY is set correctly

```bash
# In Render Dashboard → Environment tab
# Verify GEMINI_API_KEY value is correct
# Click "Save Changes" if you update it
```

### "Invalid session ID" errors
**Solution**: This shouldn't happen on Render (unlike Vercel). If it does:
- Restart the service: Dashboard → Manual Deploy → "Clear build cache & deploy"

---

## Cost Estimates

### Free Tier (Recommended for Testing/Small Classes)
- **Cost**: $0/month
- **Limits**:
  - 512 MB RAM (sufficient)
  - Shared CPU (fine for this use case)
  - Spins down after 15 min inactivity (cold starts ~30s)
  - 750 hours/month free

### Paid Tier (For Production/Large Classes)
- **Starter**: $7/month
  - No sleep/cold starts
  - Better performance
  - Recommended if teaching >20 students

### API Costs (Gemini)
- **Free tier**: 1,500 requests/day (sufficient for ~75 images/day)
- **Paid tier**: $0.00025/image (~$0.25 per 1,000 images)

**Total cost for workshop (6 datasets, ~180 images)**:
- Render: $0 (free tier)
- Gemini: $0 (within free tier)

---

## Advantages Over Vercel

✅ **No timeout limits** - captions can take as long as needed
✅ **Persistent sessions** - no "Invalid session ID" errors
✅ **True free tier** - no credit card required
✅ **Automatic HTTPS** - secure by default
✅ **Auto-deploy on git push** - same as Vercel
✅ **Better for Flask apps** - designed for this use case

---

## Security Notes

- **Never commit** `.env` file to GitHub (already in `.gitignore`)
- **Rotate SECRET_ACCESS_CODE** each semester
- **Monitor API usage** in Google AI Studio to detect abuse
- **Custom domain** available on paid plans only

---

## Custom Domain (Optional)

On paid plans, you can use your own domain:

1. Dashboard → Settings → Custom Domain
2. Add your domain (e.g., `metadata.tudelft.nl`)
3. Update DNS records as instructed
4. Render handles SSL certificates automatically

---

## Questions?

- Render Docs: https://render.com/docs
- Community: https://community.render.com
- This app: https://github.com/kortuem/idem307-image-metadata-generator
