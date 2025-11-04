# Deployment Guide

This guide provides step-by-step instructions for deploying the YouTube Analytics System.

## Prerequisites

1. **YouTube API Keys**: Get at least one API key from [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. **GitHub Account**: For hosting the frontend
3. **Render.com Account** (or alternative PaaS): For hosting the backend

## Step 1: Get YouTube API Keys

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **YouTube Data API v3**
4. Go to **Credentials** → **Create Credentials** → **API Key**
5. Copy the API key
6. (Recommended) Create 2-3 more keys for redundancy

## Step 2: Deploy Backend to Render.com

### Option A: Web Dashboard

1. **Sign up/Login** to [Render.com](https://render.com)

2. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Or use "Deploy from Git URL"

3. **Configure Service**:
   ```
   Name: youtube-analytics-api
   Environment: Python 3
   Branch: main (or your deployment branch)
   Build Command: cd backend && pip install -r requirements.txt
   Start Command: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

4. **Add Environment Variables**:
   Go to "Environment" tab and add:
   ```
   YOUTUBE_API_KEYS=AIzaSyXXXXXX,AIzaSyYYYYYY,AIzaSyZZZZZZ
   DATABASE_URL=sqlite:////opt/render/project/data/youtube_analytics.db
   CORS_ORIGINS=https://yourusername.github.io
   API_HOST=0.0.0.0
   API_PORT=8000
   ```

   **Important**:
   - Use commas to separate multiple API keys (no spaces)
   - Replace `yourusername` with your actual GitHub username

5. **Add Persistent Disk**:
   - Go to "Disks" tab
   - Click "Add Disk"
   - Name: `data`
   - Mount Path: `/opt/render/project/data`
   - Size: 1 GB (minimum)

6. **Deploy**:
   - Click "Create Web Service"
   - Wait for deployment (first deploy takes 5-10 minutes)
   - Note your service URL: `https://your-service-name.onrender.com`

7. **Verify Deployment**:
   - Visit `https://your-service-name.onrender.com/health`
   - Should return `{"status": "ok"}`
   - Visit `https://your-service-name.onrender.com/docs` for API docs

### Option B: Using Blueprint (Infrastructure as Code)

Create `render.yaml` in your repository root:

```yaml
services:
  - type: web
    name: youtube-analytics-api
    env: python
    buildCommand: "cd backend && pip install -r requirements.txt"
    startCommand: "cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: YOUTUBE_API_KEYS
        sync: false
      - key: DATABASE_URL
        value: sqlite:////opt/render/project/data/youtube_analytics.db
      - key: CORS_ORIGINS
        sync: false
    disk:
      name: data
      mountPath: /opt/render/project/data
      sizeGB: 1
```

Then connect the repository in Render dashboard.

### Alternative: Railway.app

1. Visit [Railway.app](https://railway.app)
2. Create new project from GitHub repo
3. Add environment variables (same as Render)
4. Railway will auto-detect Python and deploy
5. Add volume for persistent storage

### Alternative: Fly.io

1. Install flyctl: `brew install flyctl` (Mac) or see [docs](https://fly.io/docs/flyctl/install/)
2. Login: `fly auth login`
3. Create `fly.toml` in backend directory
4. Deploy: `fly deploy backend`

## Step 3: Deploy Frontend to GitHub Pages

### Setup Repository

1. **Push your code** to GitHub:
   ```bash
   git add .
   git commit -m "Initial commit: YouTube Analytics System"
   git push origin main
   ```

2. **Enable GitHub Pages**:
   - Go to your repository on GitHub
   - Click **Settings** → **Pages**
   - Under "Source", select **GitHub Actions**

3. **Add Secrets**:
   - Go to **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret**
   - Add:
     ```
     Name: NEXT_PUBLIC_API_URL
     Value: https://your-service-name.onrender.com/api/v1
     ```

4. **Update next.config.js** (if needed):

   Open `frontend/next.config.js` and update the basePath:
   ```javascript
   const nextConfig = {
     output: 'export',
     images: {
       unoptimized: true,
     },
     basePath: process.env.NODE_ENV === 'production' ? '/your-repo-name' : '',
     assetPrefix: process.env.NODE_ENV === 'production' ? '/your-repo-name/' : '',
   }
   ```

   Replace `your-repo-name` with your actual repository name.

5. **Trigger Deployment**:
   - Make any commit to main branch
   - Or go to **Actions** tab → **Deploy Frontend to GitHub Pages** → **Run workflow**

6. **Wait for Deployment**:
   - Go to **Actions** tab
   - Watch the workflow run (takes 2-5 minutes)
   - Once complete, your site is live!

7. **Access Your Site**:
   - Visit `https://yourusername.github.io/repository-name`

### Manual Deployment (Alternative)

If GitHub Actions doesn't work:

```bash
cd frontend
npm install
npm run build

# The static files are now in frontend/out/
# Upload these to any static hosting service
```

## Step 4: Connect Frontend and Backend

1. **Update Backend CORS**:
   In Render.com, update `CORS_ORIGINS`:
   ```
   CORS_ORIGINS=https://yourusername.github.io,http://localhost:3000
   ```

2. **Verify Connection**:
   - Open your GitHub Pages site
   - Open browser DevTools (F12)
   - Check Console for errors
   - Try adding a channel

3. **Troubleshooting Connection**:
   - Check that backend URL in secret matches actual Render URL
   - Verify CORS includes your GitHub Pages URL
   - Check backend logs in Render dashboard

## Step 5: Initial Setup and Testing

1. **Add Your First Channel**:
   - Go to "Channels" page
   - Click "Add Channel"
   - Paste a YouTube channel URL (e.g., `https://www.youtube.com/@mkbhd`)
   - Wait for import (may take 30-60 seconds)

2. **Verify Data**:
   - Check that channel appears in list
   - Click "View Details" to see videos
   - Go to Dashboard to see overview

3. **Set Up Alerts** (Optional):
   Use the API to create alerts:
   ```bash
   curl -X POST "https://your-service.onrender.com/api/v1/alerts" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Viral Video Alert",
       "alert_type": "viral_video",
       "threshold_field": "view_count",
       "threshold_value": 10000,
       "time_window_hours": 24
     }'
   ```

## Monitoring and Maintenance

### Backend Monitoring

1. **Check Logs**:
   - Render.com: Go to your service → **Logs** tab
   - Look for errors or quota warnings

2. **Monitor API Quota**:
   - Visit `/api/v1/system/api-keys` to see usage
   - If keys hit quota, add more keys

3. **Database Backups**:
   - Render persistent disks have automatic backups
   - Or manually download the SQLite file via SSH

### Frontend Updates

To update the frontend:
```bash
# Make changes
git add .
git commit -m "Update frontend"
git push origin main

# GitHub Actions will automatically redeploy
```

### Backend Updates

To update the backend:
```bash
# Make changes to backend code
git add .
git commit -m "Update backend"
git push origin main

# Render will automatically detect and redeploy
```

## Cost Estimates

### Free Tier (Development/Testing)
- **Render.com**: Free tier available (with limitations)
  - Service spins down after 15 min inactivity
  - 750 hours/month
- **GitHub Pages**: Completely free
- **YouTube API**: Free (10,000 units/day per key)

**Total: $0/month**

### Production (Recommended)
- **Render.com**: Starter plan $7/month
  - Always-on service
  - More memory and CPU
- **GitHub Pages**: Free
- **YouTube API**: Free (or add more keys)

**Total: $7/month**

### Scaling Up
- **Render.com**: Standard plan $25/month
- **PostgreSQL**: $7-15/month (if migrating from SQLite)
- **Multiple API Keys**: Free

**Total: $32-40/month**

## Troubleshooting

### Backend Issues

**Service won't start**:
- Check environment variables are set
- Verify build command is correct
- Check logs for Python errors

**Database errors**:
- Verify persistent disk is mounted
- Check DATABASE_URL path matches mount path

**API quota exceeded**:
- Add more YouTube API keys
- Reduce refresh frequency in .env

### Frontend Issues

**Page not found (404)**:
- Verify basePath in next.config.js matches repo name
- Check GitHub Pages is enabled
- Wait a few minutes after deploy

**Can't connect to API**:
- Check NEXT_PUBLIC_API_URL secret
- Verify CORS settings in backend
- Check browser console for errors

**Images not loading**:
- Verify `images: { unoptimized: true }` in next.config.js
- This is required for static export

## Advanced Configuration

### Using PostgreSQL Instead of SQLite

1. Create PostgreSQL database on Render:
   - Click "New +" → "PostgreSQL"
   - Note the connection string

2. Update environment variable:
   ```
   DATABASE_URL=postgresql://user:pass@host/db
   ```

3. Restart service

### Setting Up Custom Domain

**Backend**:
1. Add custom domain in Render dashboard
2. Update DNS records
3. Update CORS_ORIGINS with new domain

**Frontend**:
1. Add CNAME record pointing to GitHub Pages
2. Add custom domain in repository settings
3. Update backend URL if needed

### Enabling HTTPS

Both Render and GitHub Pages provide automatic HTTPS.

No additional configuration needed!

## Next Steps

1. **Add More Channels**: Import your channels and competitors
2. **Set Up Alerts**: Create alerts for important metrics
3. **Monitor Daily**: Check trending videos and growth
4. **Iterate**: Adjust refresh intervals and alert thresholds

## Support

If you encounter issues:
1. Check logs in Render dashboard
2. Verify all environment variables
3. Test API endpoints in `/docs`
4. Check GitHub Actions logs for frontend
5. Review README.md for additional help

## Security Notes

- Never commit `.env` files
- Keep API keys secret
- Use environment variables for all secrets
- Regularly rotate API keys
- Monitor quota usage

Good luck with your YouTube Analytics System!
