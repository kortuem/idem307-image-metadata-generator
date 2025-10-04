# Vercel Deployment Guide

Complete step-by-step instructions for deploying the Image Metadata Generator to Vercel.

## ⚠️ Important Vercel Limitations

**This app may NOT work reliably on Vercel** due to these limitations:

1. **Function Timeout**: Free tier = 10s, Pro tier = 60s. Caption generation takes ~18s per image.
2. **Stateless Functions**: Each API call may hit a different server instance, causing session loss.
3. **Temporary Storage**: `/tmp` storage doesn't persist across function invocations.

**Recommended alternatives**:
- **Render.com** (free tier, supports long-running Flask apps)
- **Railway.app** (good free tier, easy deployment)
- **Fly.io** (generous free tier)

If you still want to try Vercel (may work with Pro plan + sticky sessions), continue below.

---

## Prerequisites

- GitHub repository: `kortuem/idem307-image-metadata-generator` (✅ Done)
- Vercel account (**Pro plan recommended** - $20/month for 60s timeouts)
- Gemini API key from [Google AI Studio](https://aistudio.google.com/)

---

## Step 1: Get Your Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click **"Get API Key"** in the left sidebar
4. Click **"Create API Key"**
5. Copy the API key (starts with `AIza...`)
6. Save it somewhere secure - you'll need it in Step 4

---

## Step 2: Import Project to Vercel

1. Go to [vercel.com](https://vercel.com) and sign in (or create free account)
2. Click **"Add New..."** → **"Project"**
3. Click **"Import Git Repository"**
4. Find and select: `kortuem/idem307-image-metadata-generator`
5. Click **"Import"**

---

## Step 3: Configure Build Settings

On the "Configure Project" screen:

### Framework Preset
- Select: **"Other"** (this is a Flask app, not a framework Vercel auto-detects)

### Build and Output Settings
Leave these as default - Vercel will auto-detect the Python app.

**Root Directory:** Leave blank (uses repository root)

---

## Step 4: Add Environment Variables

In the "Environment Variables" section, add these **two required variables**:

### Variable 1: GEMINI_API_KEY (Required)
- **Key:** `GEMINI_API_KEY`
- **Value:** Your Gemini API key from Step 1 (starts with `AIza...`)
- **Environment:** All (Production, Preview, Development)

### Variable 2: SECRET_ACCESS_CODE (Optional but Recommended)
- **Key:** `SECRET_ACCESS_CODE`  
- **Value:** Your chosen secret access code (e.g., `idem307_2025` or `tudelft2024`)
- **Environment:** All (Production, Preview, Development)

**Why SECRET_ACCESS_CODE?**
- Students/users enter this code instead of needing their own Gemini API key
- You pay for all API usage (Gemini free tier: 1500 requests/day)
- Choose something memorable but not too obvious
- Share it privately with your students

**Example values:**
```
GEMINI_API_KEY=AIzaSyAoMRyxjsQfqzGXs9NQb4OldybMRbzm6lA
SECRET_ACCESS_CODE=idem307_2025
```

---

## Step 5: Deploy

1. Click **"Deploy"**
2. Wait 1-2 minutes for deployment to complete
3. You'll see a success screen with your deployment URL

**Your app URL will be:**
- `https://idem307-image-metadata-generator.vercel.app` (or similar)

---

## Step 6: Test Your Deployment

1. Click **"Visit"** to open your deployed app
2. The UI should load correctly
3. Test the secret access code:
   - Upload a few images
   - Enter a trigger word (e.g., `test_space`)
   - Expand **"🔑 API Key (Required)"** section
   - Enter your `SECRET_ACCESS_CODE` (e.g., `idem307_2025`)
   - Click **"Generate Captions"**
   - Should work without errors!

---

## Step 7: Share with Students

Give your students:

1. **App URL:** `https://your-app-url.vercel.app`
2. **Secret Access Code:** (the value you chose in Step 4)
3. **Example Datasets:** Links from README.md
4. **Tutorial:** Link to TUTORIAL.md in GitHub repo

**Example announcement:**
```
Image Metadata Generator Tool:
URL: https://idem307-image-metadata-generator.vercel.app
Access Code: idem307_2025

Example datasets: See GitHub README
Tutorial: https://github.com/kortuem/idem307-image-metadata-generator/blob/main/TUTORIAL.md
```

---

## Troubleshooting

### "Application Error" on deployed site
- Check Vercel dashboard → Functions → Logs
- Verify environment variables are set correctly
- Make sure GEMINI_API_KEY is valid

### "API key required" error even with SECRET_ACCESS_CODE
- Double-check spelling of environment variable name: `SECRET_ACCESS_CODE`
- Ensure it's added to Production environment
- Try redeploying: Vercel dashboard → Deployments → ⋯ menu → Redeploy

### Rate limit errors (429)
- Gemini free tier: 15 requests/minute, 1500/day
- If hitting limits, consider:
  - Asking students to get their own API keys
  - Upgrading to Gemini paid tier
  - Rate limiting users (would need code changes)

### Deployment fails
- Check Vercel build logs for errors
- Ensure `requirements.txt` is in repository root
- Python version should auto-detect (3.9+)

---

## Vercel Dashboard Navigation

**To view logs:**
1. Vercel dashboard → Your project
2. Click **"Functions"** tab
3. Click on any function to see logs

**To update environment variables:**
1. Vercel dashboard → Your project  
2. Click **"Settings"** tab
3. Click **"Environment Variables"**
4. Edit or add new variables
5. **Important:** Redeploy for changes to take effect

**To redeploy:**
1. Go to **"Deployments"** tab
2. Find latest deployment
3. Click ⋯ (three dots) → **"Redeploy"**

---

## Cost Estimate

**Vercel Costs:** Free tier is sufficient
- Hobby plan: Free
- No credit card required
- 100GB bandwidth/month (plenty for this app)

**Gemini API Costs:** Free tier likely sufficient
- Free tier: 1500 requests/day, 15 requests/minute
- Estimate: ~25 students × 30 images each = 750 requests
- Paid tier (if needed): ~$0.002 per request with Gemini 2.5 Pro

**Recommendation:**
- Start with free tiers (Vercel + Gemini)
- Monitor usage in first week
- Upgrade only if necessary

---

## Security Notes

### Keep These Private:
- ❌ Your `GEMINI_API_KEY` (never share publicly)
- ❌ Your `SECRET_ACCESS_CODE` (share only with trusted students)

### Safe to Share:
- ✅ Your Vercel app URL
- ✅ GitHub repository (code is public anyway)
- ✅ Documentation and tutorial links

### Environment Variables Are Secure:
- Not visible in source code
- Not visible to users
- Only accessible in Vercel dashboard (with your login)

---

## Optional: Custom Domain

Want a custom URL like `metadata.tudelft.nl`?

1. Vercel dashboard → Your project → Settings → Domains
2. Add your domain
3. Follow DNS configuration instructions
4. Vercel provides free SSL certificate

---

## Need Help?

- **Vercel Documentation:** https://vercel.com/docs
- **GitHub Issues:** https://github.com/kortuem/idem307-image-metadata-generator/issues
- **Gemini API Docs:** https://ai.google.dev/docs

---

**Deployment completed! Your students can now use the tool. 🎉**
