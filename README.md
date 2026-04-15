# Cash Card Dashboard Backend API

Backend service for the Cash Card Volume Dashboard. Connects to Snowflake and serves real-time data.

## Features

- ✅ Real-time queue volume tracking (Cash Card & Service Claims)
- ✅ Network reject monitoring (Visa & Marqeta)
- ✅ Automatic spike detection (2 standard deviations)
- ✅ 5-minute data caching
- ✅ RESTful API endpoints
- ✅ Optional API key authentication
- ✅ CORS support for frontend

## Quick Start

### 1. Install Dependencies

```bash
cd cash_card_dashboard_backend
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your Snowflake credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```env
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=APP_DATAMART_CCO
SNOWFLAKE_SCHEMA=SFDC_CFONE
SNOWFLAKE_ROLE=your_role
```

### 3. Run the Server

```bash
python app.py
```

Or with uvicorn directly:
```bash
uvicorn app:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### 4. Test the API

Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI)

Or test with curl:
```bash
# Health check
curl http://localhost:8000/

# Queue volumes
curl http://localhost:8000/api/queue-volumes

# Network rejects
curl http://localhost:8000/api/network-rejects

# Dashboard summary
curl http://localhost:8000/api/dashboard-summary
```

## API Endpoints

### `GET /`
Health check endpoint
- Returns: `{ "status": "healthy", "timestamp": "...", "snowflake_connected": true }`

### `GET /api/queue-volumes`
Get queue volumes with spike detection for last 14 days
- Returns: Array of queue metrics with baseline and spike alerts

### `GET /api/network-rejects`
Get network rejects by source (Visa/Marqeta) for last 14 days
- Returns: Array of reject metrics with baseline and spike alerts

### `GET /api/dashboard-summary`
Get summarized dashboard data (today's metrics)
- Returns: Single object with all key metrics for dashboard display

## Authentication

Optional API key authentication. Set in `.env`:
```env
API_KEY=your_secret_api_key
```

Then include in requests:
```bash
curl -H "X-API-Key: your_secret_api_key" http://localhost:8000/api/dashboard-summary
```

## Caching

- Data is cached for 5 minutes (configurable via `CACHE_TTL_SECONDS`)
- Reduces Snowflake query load
- Automatic cache invalidation

## Deployment

### Option 1: Docker (Recommended)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "app.py"]
```

Build and run:
```bash
docker build -t cash-card-dashboard-api .
docker run -p 8000:8000 --env-file .env cash-card-dashboard-api
```

### Option 2: Internal Platform

Deploy to your company's internal platform (Kubernetes, Cloud Run, etc.)

Key requirements:
- Python 3.11+
- Access to Snowflake from deployment environment
- Environment variables configured

### Option 3: Local/Development

Run directly with Python:
```bash
python app.py
```

## Connecting the Frontend

Update your dashboard app to fetch from this API instead of using mock data.

Replace the mock data section with:

```javascript
async function fetchDashboardData() {
    const response = await fetch('http://localhost:8000/api/dashboard-summary', {
        headers: {
            'X-API-Key': 'your_api_key' // if authentication enabled
        }
    });
    return await response.json();
}
```

## Monitoring

- Check `/` endpoint for health status
- Monitor Snowflake query performance
- Set up alerts for API errors

## Troubleshooting

### Connection Issues
- Verify Snowflake credentials in `.env`
- Check network access to Snowflake
- Verify warehouse is running

### Query Errors
- Check table permissions in Snowflake
- Verify table names match your environment
- Review query logs in Snowflake

### Performance
- Adjust `CACHE_TTL_SECONDS` if needed
- Consider using a larger Snowflake warehouse
- Monitor query execution times

## Security Notes

- **Never commit `.env` file** - it contains credentials
- Use API key authentication in production
- Restrict CORS origins in production
- Use HTTPS in production
- Consider using Snowflake key-pair authentication instead of password

## Support

For issues or questions, contact your data team or check internal documentation.
