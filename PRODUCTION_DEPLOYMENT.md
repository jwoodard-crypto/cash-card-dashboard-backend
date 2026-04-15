# Production Deployment Guide

Complete guide for deploying the Cash Card Dashboard to production for team access.

## Overview

This guide will help you deploy the dashboard so your entire team can access it via a web URL.

## Deployment Options

### Option 1: Internal Server (Recommended for Block)
Deploy to an internal Block server with authentication.

### Option 2: Cloud Platform (AWS/GCP/Azure)
Deploy to cloud infrastructure with proper security.

### Option 3: Heroku/Railway (Quick & Easy)
Fast deployment for testing/demos.

---

## Option 1: Internal Server Deployment

### Prerequisites
- Access to a Block internal server
- Docker installed on server
- Internal domain name (e.g., `cash-card-dashboard.sqprod.co`)

### Step 1: Prepare for Deployment

```bash
# On your local machine
cd cash_card_dashboard_backend

# Create production environment file
cp .env.example .env.production

# Edit with production credentials
nano .env.production
```

**Important Production Settings:**
```env
# Snowflake - Use service account credentials
SNOWFLAKE_ACCOUNT=SQUARE
SNOWFLAKE_USER=svc_cash_card_dashboard
SNOWFLAKE_PASSWORD=<service_account_password>
SNOWFLAKE_WAREHOUSE=ADHOC__SMALL  # Use smaller warehouse
SNOWFLAKE_ROLE=<service_role>

# API
API_PORT=8000
CACHE_TTL_SECONDS=300
CORS_ORIGINS=https://cash-card-dashboard.sqprod.co

# Security
API_KEY=<generate_secure_key>  # openssl rand -hex 32
```

### Step 2: Build Docker Image

```bash
# Build the image
docker build -t cash-card-dashboard:latest .

# Test locally
docker run -d \
  --name cash-card-test \
  -p 8000:8000 \
  --env-file .env.production \
  cash-card-dashboard:latest

# Test it works
curl http://localhost:8000/

# Stop test container
docker stop cash-card-test && docker rm cash-card-test
```

### Step 3: Push to Internal Registry

```bash
# Tag for internal registry
docker tag cash-card-dashboard:latest \
  registry.sqprod.co/cash-card-dashboard:latest

# Push to registry
docker push registry.sqprod.co/cash-card-dashboard:latest
```

### Step 4: Deploy to Server

SSH into your production server:

```bash
ssh your-server.sqprod.co
```

Create deployment directory:

```bash
mkdir -p /opt/cash-card-dashboard
cd /opt/cash-card-dashboard

# Create production docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  api:
    image: registry.sqprod.co/cash-card-dashboard:latest
    container_name: cash-card-api
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - SNOWFLAKE_ACCOUNT=${SNOWFLAKE_ACCOUNT}
      - SNOWFLAKE_USER=${SNOWFLAKE_USER}
      - SNOWFLAKE_PASSWORD=${SNOWFLAKE_PASSWORD}
      - SNOWFLAKE_WAREHOUSE=${SNOWFLAKE_WAREHOUSE}
      - SNOWFLAKE_ROLE=${SNOWFLAKE_ROLE}
      - API_PORT=8000
      - CACHE_TTL_SECONDS=300
      - CORS_ORIGINS=*
      - API_KEY=${API_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
EOF

# Create .env file with production credentials
nano .env  # Add your production credentials

# Start the service
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Step 5: Set Up Nginx Reverse Proxy

```bash
# Install nginx if not already installed
sudo apt-get install nginx

# Create nginx config
sudo nano /etc/nginx/sites-available/cash-card-dashboard
```

Add this configuration:

```nginx
server {
    listen 80;
    server_name cash-card-dashboard.sqprod.co;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name cash-card-dashboard.sqprod.co;

    # SSL certificates (get from your IT team)
    ssl_certificate /etc/ssl/certs/cash-card-dashboard.crt;
    ssl_certificate_key /etc/ssl/private/cash-card-dashboard.key;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy to backend
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000/;
        access_log off;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/cash-card-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 6: Set Up Automatic Data Refresh

```bash
cd /opt/cash-card-dashboard

# Create refresh script
cat > refresh_data.sh << 'EOF'
#!/bin/bash
cd /opt/cash-card-dashboard
docker-compose exec -T api python3 /app/auto_refresh_data.py
EOF

chmod +x refresh_data.sh

# Add to crontab (runs every 4 hours)
(crontab -l 2>/dev/null; echo "0 */4 * * * /opt/cash-card-dashboard/refresh_data.sh >> /var/log/cash-card-refresh.log 2>&1") | crontab -
```

### Step 7: Deploy Dashboard Frontend

The dashboard is a standalone HTML app. You have two options:

**Option A: Host on Same Server**

```bash
# Create web directory
sudo mkdir -p /var/www/cash-card-dashboard

# Copy dashboard HTML (you'll need to export it from the app)
# For now, users can access via the Goose app or you can extract the HTML
```

**Option B: Use Goose App (Easier)**

Users can:
1. Install Goose
2. Open the app: `cash-card-operations-dashboard`
3. Configure API URL: `https://cash-card-dashboard.sqprod.co`
4. Enter API key (if required)

---

## Option 2: Cloud Deployment (AWS Example)

### Using AWS ECS Fargate

1. **Push Image to ECR**

```bash
# Login to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-west-2.amazonaws.com

# Create repository
aws ecr create-repository --repository-name cash-card-dashboard

# Tag and push
docker tag cash-card-dashboard:latest <account-id>.dkr.ecr.us-west-2.amazonaws.com/cash-card-dashboard:latest
docker push <account-id>.dkr.ecr.us-west-2.amazonaws.com/cash-card-dashboard:latest
```

2. **Create ECS Task Definition**

```json
{
  "family": "cash-card-dashboard",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "<account-id>.dkr.ecr.us-west-2.amazonaws.com/cash-card-dashboard:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "API_PORT", "value": "8000"},
        {"name": "CACHE_TTL_SECONDS", "value": "300"}
      ],
      "secrets": [
        {"name": "SNOWFLAKE_ACCOUNT", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "SNOWFLAKE_USER", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "SNOWFLAKE_PASSWORD", "valueFrom": "arn:aws:secretsmanager:..."}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/cash-card-dashboard",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

3. **Create ECS Service with Load Balancer**

```bash
aws ecs create-service \
  --cluster production \
  --service-name cash-card-dashboard \
  --task-definition cash-card-dashboard \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=api,containerPort=8000"
```

---

## Option 3: Quick Deploy (Railway/Heroku)

### Railway (Easiest)

1. Install Railway CLI:
```bash
npm install -g @railway/cli
```

2. Login and deploy:
```bash
cd cash_card_dashboard_backend
railway login
railway init
railway up
```

3. Add environment variables in Railway dashboard

4. Get your URL: `https://cash-card-dashboard.railway.app`

---

## Security Checklist

Before going to production:

- [ ] Use service account credentials (not personal)
- [ ] Enable API key authentication
- [ ] Restrict CORS to specific domains
- [ ] Use HTTPS/TLS everywhere
- [ ] Store secrets in secure vault (not in code)
- [ ] Set up monitoring and alerts
- [ ] Configure proper logging
- [ ] Implement rate limiting
- [ ] Set up backup/disaster recovery
- [ ] Document access procedures
- [ ] Get security review approval

---

## Monitoring & Alerts

### Set Up Health Checks

```bash
# Add to monitoring system
curl https://cash-card-dashboard.sqprod.co/health

# Expected response:
# {"status":"healthy","timestamp":"...","data_files_exist":true}
```

### Set Up Alerts

Configure alerts for:
- API downtime
- High error rates
- Slow response times
- Data refresh failures
- Volume spikes >20K

### Logging

View logs:
```bash
# Docker
docker-compose logs -f

# Or check log files
tail -f logs/api.log
tail -f logs/refresh.log
```

---

## Team Access Instructions

Once deployed, share these instructions with your team:

### For Team Members:

1. **Install Goose** (if not already installed)
   - Visit: [goose installation page]

2. **Open Dashboard App**
   - In Goose, open: `cash-card-operations-dashboard`

3. **Configure API Connection**
   - Click ⚙️ Settings
   - Enter API URL: `https://cash-card-dashboard.sqprod.co`
   - Enter API Key: `[provide to team securely]`
   - Click "Test Connection"
   - Click "Save"

4. **View Dashboard**
   - Dashboard will load with real-time data
   - Auto-refreshes every 5 minutes
   - Shows queue volumes, network rejects, and trends

### Alternative: Web Browser Access

If you host the dashboard HTML:
- Visit: `https://cash-card-dashboard.sqprod.co`
- Enter API key when prompted
- Bookmark for easy access

---

## Maintenance

### Update Dashboard

```bash
# Build new version
docker build -t cash-card-dashboard:v2 .

# Push to registry
docker tag cash-card-dashboard:v2 registry.sqprod.co/cash-card-dashboard:v2
docker push registry.sqprod.co/cash-card-dashboard:v2

# Update on server
ssh your-server.sqprod.co
cd /opt/cash-card-dashboard
docker-compose pull
docker-compose up -d
```

### Backup Data

```bash
# Backup JSON data files
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Backup logs
tar -czf logs-$(date +%Y%m%d).tar.gz logs/
```

### Troubleshooting

**Dashboard shows old data:**
- Check data refresh cron job: `crontab -l`
- Manually refresh: `./refresh_data.sh`
- Check logs: `tail -f logs/refresh.log`

**API not responding:**
- Check container: `docker-compose ps`
- Check logs: `docker-compose logs api`
- Restart: `docker-compose restart api`

**Snowflake connection errors:**
- Verify credentials in `.env`
- Check warehouse is running
- Verify role has table access

---

## Cost Estimates

### Infrastructure
- **Small VM**: $20-50/month
- **AWS ECS Fargate**: $30-60/month
- **Railway/Heroku**: $5-25/month

### Snowflake
- **Warehouse (X-Small)**: ~$2-5/day
- **With auto-suspend**: ~$50-100/month
- **Query caching**: Reduces costs significantly

### Total Estimated Cost
- **Development**: $5-10/month
- **Production**: $100-200/month

---

## Support

For issues or questions:
1. Check logs first
2. Verify Snowflake connection
3. Test API endpoints directly
4. Review monitoring dashboards
5. Contact: [your team contact]

---

## Next Steps

After deployment:
- [ ] Train team on dashboard usage
- [ ] Set up monitoring alerts
- [ ] Schedule regular maintenance windows
- [ ] Document incident response procedures
- [ ] Plan for scaling if needed
