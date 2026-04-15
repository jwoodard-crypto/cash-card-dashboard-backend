# Deployment Guide - Cash Card Dashboard

Complete guide for deploying the Cash Card Dashboard with real Snowflake data.

## Architecture

```
┌─────────────────┐      HTTP/REST      ┌──────────────────┐
│   Dashboard     │ ◄─────────────────► │   Backend API    │
│   (Frontend)    │                      │   (FastAPI)      │
└─────────────────┘                      └──────────────────┘
                                                  │
                                                  │ SQL
                                                  ▼
                                         ┌──────────────────┐
                                         │    Snowflake     │
                                         │    Database      │
                                         └──────────────────┘
```

## Prerequisites

- Python 3.11+
- Snowflake account with access to:
  - `APP_DATAMART_CCO.SFDC_CFONE.DISPUTE_VOLUME_BY_QUEUE_DRILL_DOWN`
  - `CASH_DISPUTES.PUBLIC.CC_DISPUTES_CLAIM_DETAILS`
- Network access to Snowflake from deployment environment

## Step 1: Backend Setup

### Option A: Quick Setup (Recommended for Testing)

```bash
cd cash_card_dashboard_backend
./setup.sh
```

The script will:
1. Create virtual environment
2. Install dependencies
3. Create `.env` file
4. Test Snowflake connection
5. Guide you through configuration

### Option B: Manual Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your Snowflake credentials

# 3. Test connection
python -c "from app import get_snowflake_connection; \
           with get_snowflake_connection() as conn: print('✓ Connected')"

# 4. Start server
python app.py
```

## Step 2: Verify Backend

### Test Health Check
```bash
curl http://localhost:8000/
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-15T10:30:00.000000",
  "snowflake_connected": true
}
```

### Test Data Endpoints
```bash
# Queue volumes
curl http://localhost:8000/api/queue-volumes | jq

# Network rejects
curl http://localhost:8000/api/network-rejects | jq

# Dashboard summary
curl http://localhost:8000/api/dashboard-summary | jq
```

## Step 3: Frontend Configuration

### Open the Dashboard
The dashboard should already be open in your browser. If not, navigate to the app.

### Configure API Connection

1. Click the **⚙️ Settings** icon in the top right
2. Enter your API configuration:
   - **API Base URL**: `http://localhost:8000` (or your deployed URL)
   - **API Key**: (leave blank if not using authentication)
3. Click **Test Connection**
4. If successful, click **Save**

### Verify Data Flow

You should now see real data:
- ✅ Queue volumes (Cash Card & Service Claims)
- ✅ Network rejects (Visa & Marqeta)
- ✅ Spike alerts (if volumes exceed baseline)
- ✅ 7-day trend chart

## Step 4: Production Deployment

### Option 1: Docker (Recommended)

```bash
# Build image
docker build -t cash-card-dashboard-api .

# Run container
docker run -d \
  --name cash-card-api \
  -p 8000:8000 \
  --env-file .env \
  cash-card-dashboard-api

# Check logs
docker logs -f cash-card-api
```

Or use Docker Compose:
```bash
docker-compose up -d
```

### Option 2: Kubernetes

Create `deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cash-card-dashboard-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: cash-card-api
  template:
    metadata:
      labels:
        app: cash-card-api
    spec:
      containers:
      - name: api
        image: your-registry/cash-card-dashboard-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: SNOWFLAKE_ACCOUNT
          valueFrom:
            secretKeyRef:
              name: snowflake-creds
              key: account
        - name: SNOWFLAKE_USER
          valueFrom:
            secretKeyRef:
              name: snowflake-creds
              key: user
        - name: SNOWFLAKE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: snowflake-creds
              key: password
        # ... other env vars
        livenessProbe:
          httpGet:
            path: /
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: cash-card-api
spec:
  selector:
    app: cash-card-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

Deploy:
```bash
kubectl apply -f deployment.yaml
```

### Option 3: Cloud Run (GCP)

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/cash-card-api

# Deploy
gcloud run deploy cash-card-api \
  --image gcr.io/PROJECT_ID/cash-card-api \
  --platform managed \
  --region us-central1 \
  --set-env-vars SNOWFLAKE_ACCOUNT=xxx,SNOWFLAKE_USER=xxx \
  --set-secrets SNOWFLAKE_PASSWORD=snowflake-password:latest
```

### Option 4: AWS ECS/Fargate

1. Push image to ECR
2. Create task definition with environment variables
3. Create ECS service
4. Configure load balancer

## Step 5: Security Hardening

### Enable API Key Authentication

1. Generate a secure API key:
```bash
openssl rand -hex 32
```

2. Add to `.env`:
```env
API_KEY=your_generated_key_here
```

3. Restart backend

4. Update dashboard settings with the API key

### Restrict CORS Origins

In `.env`:
```env
CORS_ORIGINS=https://your-dashboard-domain.com
```

### Use Key-Pair Authentication (Recommended)

Instead of password, use Snowflake key-pair authentication:

1. Generate key pair:
```bash
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
```

2. Add public key to Snowflake user:
```sql
ALTER USER your_user SET RSA_PUBLIC_KEY='MIIBIjANBg...';
```

3. Update `app.py` to use private key instead of password

### Enable HTTPS

Use a reverse proxy (nginx, Caddy) or cloud load balancer to terminate SSL.

## Step 6: Monitoring & Alerts

### Health Monitoring

Set up monitoring for:
- API health endpoint: `GET /`
- Response times
- Error rates
- Snowflake query performance

### Example with Prometheus

Add to `app.py`:
```python
from prometheus_client import Counter, Histogram, generate_latest

request_count = Counter('api_requests_total', 'Total API requests')
request_duration = Histogram('api_request_duration_seconds', 'API request duration')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Logging

Configure structured logging:
```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Step 7: Maintenance

### Update Data Queries

To modify queries, edit `app.py`:
- `QUEUE_VOLUMES_QUERY`
- `NETWORK_REJECTS_QUERY`

Then restart the service.

### Adjust Cache TTL

In `.env`:
```env
CACHE_TTL_SECONDS=300  # 5 minutes (default)
```

Lower for more real-time data, higher to reduce Snowflake load.

### Database Maintenance

Ensure Snowflake tables are:
- Regularly updated
- Properly indexed
- Accessible by service account

## Troubleshooting

### Backend won't start
- Check `.env` configuration
- Verify Snowflake credentials
- Check port 8000 is available
- Review logs for errors

### Dashboard shows "Unable to connect"
- Verify backend is running
- Check API URL in dashboard settings
- Verify CORS settings
- Check network/firewall rules

### Slow queries
- Increase Snowflake warehouse size
- Optimize SQL queries
- Increase cache TTL
- Add query result caching in Snowflake

### Authentication errors
- Verify API key matches
- Check Snowflake user permissions
- Ensure role has access to required tables

## Cost Optimization

### Snowflake
- Use smaller warehouse (X-Small sufficient for this workload)
- Enable auto-suspend (1 minute)
- Use query result caching
- Schedule warehouse suspension during off-hours

### API
- Increase cache TTL to reduce query frequency
- Use connection pooling
- Implement query result pagination if needed

## Support

For issues:
1. Check logs: `docker logs cash-card-api`
2. Test Snowflake connection directly
3. Verify table permissions
4. Review API documentation: `http://localhost:8000/docs`

## Next Steps

- [ ] Set up automated backups
- [ ] Configure alerting (PagerDuty, Slack)
- [ ] Add more metrics/charts
- [ ] Implement user authentication
- [ ] Create mobile-responsive version
- [ ] Add export functionality (CSV, PDF)
