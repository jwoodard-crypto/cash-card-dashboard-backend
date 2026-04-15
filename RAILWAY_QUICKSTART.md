# 🚂 Railway Quick Deploy (10 Minutes)

Get your dashboard online in 10 minutes!

---

## Before You Start

**Do you have a Snowflake service account?**
- ✅ **Yes** → Follow this guide
- ❌ **No** → Submit `SERVICE_ACCOUNT_REQUEST.md` first, or use your personal credentials temporarily

---

## Step 1: Sign Up for Railway (2 min)

1. Go to: https://railway.app
2. Click **"Login with GitHub"**
3. Authorize Railway

✅ You now have a Railway account!

---

## Step 2: Push Code to GitHub (3 min)

```bash
cd cash_card_dashboard_backend

# Initialize git
git init
git add .
git commit -m "Cash Card Dashboard - Initial commit"
```

**Now create GitHub repo:**
1. Go to: https://github.com/new
2. Name: `cash-card-dashboard-backend`
3. Make it **Private** ⚠️
4. Click **"Create repository"**

**Push your code:**
```bash
# Replace YOUR_USERNAME with your GitHub username
git remote add origin https://github.com/YOUR_USERNAME/cash-card-dashboard-backend.git
git branch -M main
git push -u origin main
```

✅ Code is on GitHub!

---

## Step 3: Deploy to Railway (2 min)

1. Go to: https://railway.app/new
2. Click **"Deploy from GitHub repo"**
3. Select `cash-card-dashboard-backend`
4. Click **"Deploy Now"**

Railway will:
- Detect Python automatically ✅
- Install dependencies ✅
- Start your API ✅

Wait ~2 minutes for deployment...

✅ Your API is deployed!

---

## Step 4: Set Environment Variables (2 min)

In Railway dashboard:

1. Click your project
2. Click **"Variables"** tab
3. Click **"+ New Variable"**
4. Add these:

```
SNOWFLAKE_ACCOUNT
Value: SQUARE

SNOWFLAKE_USER
Value: svc_cash_card_dashboard
(or your username temporarily)

SNOWFLAKE_PASSWORD
Value: <from IT or your password>

SNOWFLAKE_WAREHOUSE
Value: ADHOC__LARGE

SNOWFLAKE_DATABASE
Value: APP_DATAMART_CCO

SNOWFLAKE_SCHEMA
Value: PUBLIC

SNOWFLAKE_ROLE
Value: svc_cash_card_dashboard
(or your role temporarily)

PORT
Value: 8000
```

5. Click **"Deploy"** to restart with new variables

✅ Backend configured!

---

## Step 5: Get Your URL (1 min)

1. In Railway dashboard → **Settings** tab
2. Scroll to **"Domains"**
3. Click **"Generate Domain"**

You'll get a URL like:
```
https://cash-card-dashboard-production-a1b2.up.railway.app
```

**Test it:**
```bash
curl https://YOUR-RAILWAY-URL/health
```

Should return: `{"status": "healthy"}`

✅ API is live!

---

## Step 6: Update Dashboard (1 min)

Now we need to point the dashboard to your Railway URL:

**I'll help you with this!** Just tell me your Railway URL and I'll update the dashboard app for you.

---

## Step 7: Share with Team! 🎉

**Option A: Share the Goose App**

Send in Slack:
```
📊 Cash Card Dashboard is Live!

Link: goose://apps/cash-card-operations-dashboard

Setup:
1. Install Goose: https://block.github.io/goose/
2. Click the link above
3. Click ⚙️ Settings
4. Enter: https://YOUR-RAILWAY-URL
5. Save

Dashboard shows real-time queue volumes, network rejects, and alerts!
```

**Option B: Host Dashboard on GitHub Pages**

Make it accessible without Goose - just a regular website!

1. Create new repo: `cash-card-dashboard-frontend`
2. Upload dashboard HTML as `index.html`
3. Enable GitHub Pages
4. Share URL: `https://YOUR_USERNAME.github.io/cash-card-dashboard-frontend`

---

## 🔄 Enable Auto-Refresh

Railway needs to run the refresh script every 4 hours.

### Add Cron Job:

1. In Railway dashboard → **Settings**
2. Scroll to **"Cron Jobs"**
3. Click **"Add Cron Job"**
4. Command: `python auto_refresh_data.py`
5. Schedule: `0 */4 * * *` (every 4 hours)
6. Save

✅ Auto-refresh enabled!

---

## 💰 Cost

**Free Tier:**
- $5 credit/month
- ~500 hours uptime
- Good for testing

**Hobby Plan: $5/month**
- Unlimited projects
- Always online
- Recommended for production

**Total: ~$5/month** 🎯

---

## ✅ Deployment Checklist

- [ ] Railway account created
- [ ] GitHub repo created (private!)
- [ ] Code pushed to GitHub
- [ ] Railway project deployed
- [ ] Environment variables set
- [ ] Domain generated
- [ ] API health check passes
- [ ] Dashboard updated with Railway URL
- [ ] Cron job configured
- [ ] Team can access dashboard
- [ ] Service account credentials added (or on roadmap)

---

## 🆘 Need Help?

**Common Issues:**

### "Deployment failed"
- Check Railway logs
- Verify `requirements.txt` exists
- Make sure all files are committed to git

### "Can't connect to Snowflake"
- Verify environment variables are correct
- Check service account has permissions
- Try with your personal credentials first

### "Dashboard shows connection error"
- Verify Railway URL is correct
- Check CORS settings
- Test API: `curl https://YOUR-URL/health`

---

## 🎯 Next Steps

After deployment:
1. **Monitor**: Check Railway dashboard daily
2. **Optimize**: Adjust refresh schedule if needed
3. **Expand**: Add more metrics as requested
4. **Document**: Share Railway access with team lead

---

## 📞 Get Help

Just ask me! I can help with:
- GitHub setup
- Railway configuration
- Debugging errors
- Adding features

**Ready to deploy?** Let's do it! 🚀
