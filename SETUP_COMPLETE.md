# 🎉 Setup Complete!

Your Cash Card Dashboard is ready with automatic refresh and spike alerts!

## ✅ What You Have Now

### 1. **Working Dashboard** 
- Real-time queue volumes (Cash Card & Service Claims)
- Network rejects tracking (Visa & Marqeta)
- 7-day trend chart
- Spike detection alerts
- **NEW:** High-volume alert (>20K cases)

### 2. **Automatic Data Refresh**
- Script that runs Snowflake queries automatically
- Updates dashboard data on schedule
- Logs all refresh activity
- Detects and alerts on spikes >20K

### 3. **Production Deployment Guide**
- Complete instructions for team access
- Docker deployment ready
- Security best practices included

---

## 🚀 Quick Start Commands

### Start the Dashboard (if not running)
```bash
cd cash_card_dashboard_backend
python3 app_file_based.py
```

### Manually Refresh Data
```bash
cd cash_card_dashboard_backend
python3 auto_refresh_data.py
```

### Set Up Automatic Refresh (Cron Job)
```bash
cd cash_card_dashboard_backend
./setup_cron.sh
```

Choose from:
1. Daily at 6 AM
2. Twice daily (6 AM & 6 PM)
3. Every 4 hours
4. Hourly during business hours

---

## 📊 Dashboard Features

### Main Metrics
- **Cash Card Queue**: Current volume with baseline comparison
- **Service Claims Queue**: Current volume with baseline comparison
- **Network Rejects**: Visa and Marqeta reject counts
- **7-Day Trend**: Visual chart showing volume trends

### Alerts
1. **Spike Alert** (Red banner): When volume exceeds 2 standard deviations
2. **High Volume Alert** (Orange banner): When any queue >20,000 cases
3. Both update automatically with data refresh

---

## 🔄 How Automatic Refresh Works

```
Cron Job (scheduled)
    ↓
auto_refresh_data.py runs
    ↓
Queries Snowflake
    ↓
Updates JSON files (data/)
    ↓
Checks for spikes >20K
    ↓
Logs results
    ↓
Dashboard shows new data (next refresh)
```

### Refresh Schedule Options

| Option | Schedule | Best For |
|--------|----------|----------|
| 1 | Daily at 6 AM | Low-frequency updates |
| 2 | 6 AM & 6 PM | Twice-daily updates |
| 3 | Every 4 hours | Regular updates |
| 4 | Hourly (business hours) | Real-time monitoring |

---

## 📁 File Structure

```
cash_card_dashboard_backend/
├── app_file_based.py          # Main API server
├── auto_refresh_data.py       # Automatic refresh script ✨ NEW
├── setup_cron.sh              # Cron setup helper ✨ NEW
├── data/
│   ├── queue_volumes.json     # Queue data
│   ├── network_rejects.json   # Reject data
│   └── spike_alerts.json      # Spike alerts ✨ NEW
├── logs/
│   └── refresh.log            # Refresh logs ✨ NEW
└── PRODUCTION_DEPLOYMENT.md   # Deployment guide ✨ NEW
```

---

## 🎯 Next Steps

### 1. Set Up Automatic Refresh (Recommended!)

```bash
cd cash_card_dashboard_backend
./setup_cron.sh
```

This will:
- Ask you to choose a refresh schedule
- Set up cron job automatically
- Start logging to `logs/refresh.log`

### 2. Test the Refresh Script

```bash
cd cash_card_dashboard_backend
python3 auto_refresh_data.py
```

You should see:
```
🔄 Cash Card Dashboard - Automatic Data Refresh
============================================================
📡 Connecting to Snowflake...
✅ Connected successfully
📊 Fetching queue volumes...
✅ Saved 16 records to data/queue_volumes.json
🔌 Fetching network rejects...
✅ Saved 16 records to data/network_rejects.json
⚠️  Checking for volume spikes (>20K)...
✅ No high-volume spikes detected
============================================================
✅ Data refresh completed successfully!
```

### 3. Deploy to Production (Optional)

See `PRODUCTION_DEPLOYMENT.md` for complete instructions on:
- Deploying to internal server
- Setting up team access
- Configuring security
- Monitoring and alerts

---

## 🔍 Monitoring

### View Refresh Logs
```bash
tail -f cash_card_dashboard_backend/logs/refresh.log
```

### Check Cron Job Status
```bash
crontab -l | grep cash_card
```

### Test API Health
```bash
curl http://localhost:8000/
```

### View Spike Alerts
```bash
cat cash_card_dashboard_backend/data/spike_alerts.json
```

---

## 🚨 Spike Alert Details

The system checks for two types of alerts:

### 1. Statistical Spike (Red Banner)
- Triggered when: Volume > (7-day avg + 2 × std deviation)
- Shows in: Main dashboard spike alert banner
- Indicates: Unusual volume compared to recent trends

### 2. High Volume Alert (Orange Banner) ✨ NEW
- Triggered when: Any queue >20,000 cases
- Shows in: Small banner at top of dashboard
- Indicates: Absolute high volume threshold reached

Both alerts:
- Update automatically with data refresh
- Show queue name and volume
- Include baseline comparison
- Log to `spike_alerts.json`

---

## 📞 Troubleshooting

### Dashboard shows old data
```bash
# Manually refresh
cd cash_card_dashboard_backend
python3 auto_refresh_data.py

# Check cron job
crontab -l

# View logs
tail -f logs/refresh.log
```

### Refresh script fails
```bash
# Check Snowflake connection
cd cash_card_dashboard_backend
python3 -c "from auto_refresh_data import get_snowflake_connection; \
            conn = get_snowflake_connection(); \
            print('✅ Connected'); \
            conn.close()"

# Check .env file
cat .env
```

### Cron job not running
```bash
# Check cron service
sudo systemctl status cron  # Linux
# or
launchctl list | grep cron  # macOS

# Check cron logs
grep CRON /var/log/syslog  # Linux
# or
log show --predicate 'process == "cron"' --last 1h  # macOS
```

---

## 📚 Documentation

- **README.md** - Quick start guide
- **DEPLOYMENT.md** - Original deployment guide
- **PRODUCTION_DEPLOYMENT.md** - Team deployment guide ✨ NEW
- **ARCHITECTURE.md** - Technical architecture
- **QUICKSTART.md** - 5-minute setup

---

## 🎊 Success!

You now have:
- ✅ Working dashboard with real Snowflake data
- ✅ Automatic data refresh (set up with `./setup_cron.sh`)
- ✅ Spike detection and alerts (>20K threshold)
- ✅ Production deployment guide
- ✅ Complete documentation

**Your dashboard is production-ready!**

---

## 💡 Tips

1. **Start with hourly refresh** during business hours to see how it works
2. **Monitor the logs** for the first few days
3. **Adjust the schedule** based on your team's needs
4. **Set up Slack/email alerts** for spike notifications (future enhancement)
5. **Deploy to production** when ready for team access

---

## 🤝 Need Help?

- Check the logs: `tail -f logs/refresh.log`
- Review documentation in this directory
- Test components individually
- Ask me in Goose for assistance!

**Enjoy your new dashboard!** 🎉
