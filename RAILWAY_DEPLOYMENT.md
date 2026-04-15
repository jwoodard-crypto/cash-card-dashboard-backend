# 🚂 Railway Deployment Guide

Deploy your Cash Card Dashboard to Railway for team-wide access!

## 🎯 What You'll Get

After deployment:
- **Public URL**: `https://cash-card-dashboard-xxxxx.up.railway.app`
- **Always online**: No need to keep your laptop running
- **Team access**: Anyone can access via URL (no Goose needed!)
- **Auto-updates**: Data refreshes every 4 hours automatically

---

## 📋 Prerequisites

1. **Railway Account** (free tier works!)
   - Sign up at: https://railway.app
   - Connect your GitHub account

2. **Snowflake Service Account** (for automation)
   - You'll need the credentials from `SERVICE_ACCOUNT_REQUEST.md`
   - Or we can start with manual refresh

---

## 🚀 Quick Deploy (5 minutes)

### Step 1: Push to GitHub

```bash
cd cash_card_dashboard_backend

# Initialize git repo
git init
git add .
git commit -m "Initial commit - Cash Card Dashboard"

# Create GitHub repo (you'll need to do this on github.com)
# Then:
git remote add origin https://github.com/YOUR_USERNAME/cash-card-dashboard.git
git push -u origin main
```

### Step 2: Deploy to Railway

1. Go to https://railway.app
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your `cash-card-dashboard` repo
5. Railway will auto-detect Python and deploy!

### Step 3: Set Environment Variables

In Railway dashboard:
1. Go to your project → **Variables** tab
2. Add these:

```
SNOWFLAKE_ACCOUNT=SQUARE
SNOWFLAKE_USER=svc_cash_card_dashboard
SNOWFLAKE_PASSWORD=<from service account>
SNOWFLAKE_WAREHOUSE=ADHOC__LARGE
SNOWFLAKE_DATABASE=APP_DATAMART_CCO
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=svc_cash_card_dashboard
PORT=8000
```

### Step 4: Get Your URL

Railway will give you a URL like:
```
https://cash-card-dashboard-production-xxxx.up.railway.app
```

That's your dashboard API!

---

## 🎨 Deploy the Frontend

### Option A: Host on Railway (Recommended)

Create a second Railway service for the dashboard HTML:

1. Create `frontend` folder:
```bash
mkdir frontend
cp ~/.local/share/goose/apps/cash-card-operations-dashboard.html frontend/index.html
```

2. Create `frontend/server.py`:
```python
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        SimpleHTTPRequestHandler.end_headers(self)

port = int(os.environ.get('PORT', 8080))
httpd = HTTPServer(('0.0.0.0', port), CORSRequestHandler)
print(f"Serving on port {port}")
httpd.serve_forever()
```

3. Deploy to Railway (same process as backend)

### Option B: Use GitHub Pages (Free!)

1. Create a new repo: `cash-card-dashboard-frontend`
2. Upload the HTML file as `index.html`
3. Enable GitHub Pages in repo settings
4. Your dashboard will be at: `https://YOUR_USERNAME.github.io/cash-card-dashboard-frontend`

---

## 🔧 Update Dashboard to Use Railway URL

After deployment, update the dashboard's default API URL:

1. Open `cash-card-operations-dashboard.html`
2. Find the line with `apiBaseUrl`
3. Change to your Railway URL:
```javascript
const apiBaseUrl = 'https://cash-card-dashboard-production-xxxx.up.railway.app';
```

---

## 🔄 Set Up Auto-Refresh

Railway can run scheduled tasks! Add this to your project:

**Create `refresh_cron.py`:**
```python
import schedule
import time
from auto_refresh_data import main as refresh_data

# Run every 4 hours
schedule.every(4).hours.do(refresh_data)

print("🔄 Auto-refresh scheduler started")
while True:
    schedule.run_pending()
    time.sleep(60)
```

**Update `Procfile`:**
```
web: python app_file_based.py
worker: python refresh_cron.py
```

Railway will run both processes!

---

## 💰 Cost Estimate

**Railway Free Tier:**
- $5 credit/month
- Should cover this dashboard easily
- ~$0.01/hour for small apps

**Paid Plan (if needed):**
- $5/month for hobby plan
- Plenty for this use case

---

## 🎯 Final Result

After deployment, share this with your team:

```
📊 Cash Card Dashboard is Live!

Dashboard: https://YOUR-FRONTEND-URL
API Docs: https://YOUR-BACKEND-URL/docs

No setup needed - just click and view!
Updates every 4 hours automatically.
```

---

## 🆘 Troubleshooting

### Deployment fails?
- Check Railway logs in dashboard
- Verify all environment variables are set
- Make sure `requirements.txt` is in repo

### Data not updating?
- Check if service account credentials are correct
- Verify Snowflake access from Railway IP
- Check Railway logs for errors

### Dashboard shows "Connection Error"?
- Verify CORS is enabled in backend
- Check Railway URL is correct in dashboard
- Test API directly: `https://YOUR-URL/health`

---

## 📞 Need Help?

Just ask me! I can help with:
- Setting up GitHub repo
- Configuring Railway
- Debugging deployment issues
- Setting up the service account

---

**Ready to deploy?** Let me know and I'll walk you through it step by step! 🚀
