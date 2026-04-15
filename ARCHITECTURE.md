# Architecture Documentation

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                             │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │         Cash Card Analytics Dashboard (Frontend)        │    │
│  │                                                          │    │
│  │  • Queue Volume Metrics                                 │    │
│  │  • Network Reject Tracking                              │    │
│  │  • Spike Alert Banner                                   │    │
│  │  • 7-Day Trend Chart                                    │    │
│  │  • Settings Configuration                               │    │
│  │  • Auto-refresh (5 min)                                 │    │
│  └────────────────────────────────────────────────────────┘    │
│                           │                                       │
│                           │ HTTP/REST API                         │
│                           │ (JSON)                                │
└───────────────────────────┼───────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND API SERVER                            │
│                     (FastAPI / Python)                           │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Endpoints                          │  │
│  │  • GET /                     (Health Check)              │  │
│  │  • GET /api/queue-volumes    (14 days data)             │  │
│  │  • GET /api/network-rejects  (14 days data)             │  │
│  │  • GET /api/dashboard-summary (Today's summary)         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  Business Logic Layer                     │  │
│  │  • Spike Detection (2σ threshold)                        │  │
│  │  • 7-day Rolling Average Calculation                     │  │
│  │  • Network Source Mapping (Visa/Marqeta)                │  │
│  │  • Data Aggregation & Formatting                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Caching Layer                           │  │
│  │  • TTL Cache (5 minutes)                                 │  │
│  │  • In-Memory Storage                                     │  │
│  │  • Automatic Invalidation                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Snowflake Connection Pool                    │  │
│  │  • Connection Management                                  │  │
│  │  • Query Execution                                        │  │
│  │  • Error Handling                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                       │
└───────────────────────────┼───────────────────────────────────────┘
                            │
                            │ SQL Queries
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SNOWFLAKE DATABASE                            │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         APP_DATAMART_CCO.SFDC_CFONE                       │  │
│  │                                                            │  │
│  │  DISPUTE_VOLUME_BY_QUEUE_DRILL_DOWN                      │  │
│  │  ├─ DATE                                                  │  │
│  │  ├─ QUEUE_NAME                                            │  │
│  │  ├─ ENTERED (cases)                                       │  │
│  │  ├─ HANDLED (cases)                                       │  │
│  │  └─ HANDLE_TIME_HOURS                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         CASH_DISPUTES.PUBLIC                              │  │
│  │                                                            │  │
│  │  CC_DISPUTES_CLAIM_DETAILS                               │  │
│  │  ├─ SALESFORCE_CASE_NUMBER                               │  │
│  │  ├─ IDS_REJECTED_BY_NETWORK_REASON                       │  │
│  │  ├─ SPONSORING_BANK (Visa/Marqeta)                       │  │
│  │  ├─ DISPUTRON_DISPUTED_AMOUNT_DOLLARS                    │  │
│  │  └─ CASE_CREATION_DATE_TIME_UTC                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Dashboard Load
```
User opens dashboard
    ↓
Dashboard checks localStorage for API config
    ↓
If configured: Fetch data from API
If not: Show settings modal
```

### 2. Data Fetch Cycle
```
Dashboard → GET /api/dashboard-summary
    ↓
Backend checks cache
    ↓
Cache HIT → Return cached data (fast)
    ↓
Cache MISS → Query Snowflake
    ↓
Execute SQL queries:
    • Queue volumes (with rolling avg)
    • Network rejects (with spike detection)
    ↓
Process results:
    • Calculate baselines
    • Detect spikes
    • Format response
    ↓
Store in cache (5 min TTL)
    ↓
Return JSON to dashboard
    ↓
Dashboard updates UI
```

### 3. Spike Detection Algorithm
```
For each queue/metric:
    ↓
Calculate 7-day rolling average (μ)
    ↓
Calculate standard deviation (σ)
    ↓
Check: current_value > (μ + 2σ) ?
    ↓
YES → Flag as SPIKE ⚠️
NO  → Normal ✓
    ↓
Calculate % change from baseline
    ↓
Return to dashboard
```

## Component Details

### Frontend (Dashboard)
- **Technology**: HTML5, CSS3, JavaScript
- **Framework**: Vanilla JS (no dependencies)
- **Storage**: localStorage for API config
- **Refresh**: Auto-refresh every 5 minutes
- **Features**:
  - Responsive design
  - Real-time updates
  - Error handling
  - Settings modal
  - Loading states

### Backend (API)
- **Framework**: FastAPI (Python 3.11+)
- **Database**: Snowflake Connector
- **Caching**: cachetools (TTLCache)
- **Authentication**: Optional API key
- **CORS**: Configurable origins
- **Features**:
  - RESTful API
  - Automatic caching
  - Health checks
  - Error handling
  - Swagger docs

### Database (Snowflake)
- **Warehouse**: Configurable (X-Small recommended)
- **Tables**: 2 main tables
- **Query Optimization**: CTEs, window functions
- **Data Window**: 30 days (backend), 14 days (frontend)

## Security Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTPS (Production)
       │ API Key Header (Optional)
       ▼
┌─────────────┐
│  API Server │
└──────┬──────┘
       │ Verify API Key
       │ CORS Check
       ▼
┌─────────────┐
│   Backend   │
└──────┬──────┘
       │ Snowflake Auth
       │ (Password or Key-Pair)
       ▼
┌─────────────┐
│  Snowflake  │
└─────────────┘
```

### Security Layers
1. **Transport**: HTTPS in production
2. **Authentication**: Optional API key
3. **Authorization**: Snowflake role-based access
4. **CORS**: Restricted origins in production
5. **Rate Limiting**: Can be added via middleware
6. **Secrets**: Environment variables, never in code

## Deployment Architectures

### Development (Local)
```
Developer Machine
├── Backend (localhost:8000)
└── Dashboard (browser)
```

### Production (Docker)
```
Docker Host
├── Container: cash-card-api
│   ├── FastAPI app
│   ├── Snowflake connector
│   └── Health checks
└── Load Balancer (optional)
    └── HTTPS termination
```

### Production (Kubernetes)
```
Kubernetes Cluster
├── Deployment: cash-card-api
│   ├── Replicas: 2-3
│   ├── ConfigMap: API config
│   ├── Secret: Snowflake creds
│   └── Health/Readiness probes
├── Service: cash-card-api-svc
│   └── LoadBalancer
└── Ingress: HTTPS + domain
```

### Production (Cloud Run / Serverless)
```
Cloud Provider
├── Cloud Run Service
│   ├── Auto-scaling
│   ├── HTTPS endpoint
│   └── Environment secrets
└── Cloud SQL / Secrets Manager
    └── Snowflake credentials
```

## Performance Characteristics

### Response Times
- **Cache Hit**: < 50ms
- **Cache Miss**: 1-3 seconds (Snowflake query)
- **Dashboard Load**: < 500ms

### Throughput
- **Concurrent Users**: 100+ (with caching)
- **Requests/Second**: 50+ (cached)
- **Snowflake Queries**: ~12/hour (with 5-min cache)

### Resource Usage
- **Backend Memory**: ~100-200 MB
- **Backend CPU**: < 5% (idle), < 20% (active)
- **Snowflake Warehouse**: X-Small sufficient
- **Network**: < 1 MB/request

## Scalability

### Horizontal Scaling
```
Load Balancer
    ├── API Instance 1 (cache)
    ├── API Instance 2 (cache)
    └── API Instance 3 (cache)
         ↓
    Snowflake (shared)
```

**Note**: Each instance has its own cache. For shared cache, use Redis.

### Vertical Scaling
- Increase Snowflake warehouse size
- Add more API server resources
- Optimize SQL queries

## Monitoring Points

### Application Metrics
- API response times
- Cache hit/miss ratio
- Error rates
- Request counts

### Database Metrics
- Query execution time
- Warehouse utilization
- Query queue depth
- Credit usage

### Infrastructure Metrics
- CPU/Memory usage
- Network I/O
- Container health
- Pod restarts (K8s)

## Disaster Recovery

### Backup Strategy
- **Code**: Git repository
- **Configuration**: Environment variables
- **Data**: Snowflake (managed backups)

### Recovery Procedures
1. **API Failure**: Auto-restart (Docker/K8s)
2. **Snowflake Outage**: Cached data continues serving
3. **Complete Failure**: Redeploy from Git + restore config

### High Availability
- Multiple API replicas
- Health checks
- Auto-restart policies
- Snowflake built-in HA

## Data Freshness

```
Snowflake ETL → Tables Updated (varies by table)
                     ↓
Backend Query → Cache (5 min TTL)
                     ↓
Dashboard → Auto-refresh (5 min)
                     ↓
User sees data (max 10 min old)
```

## Cost Optimization

### Snowflake
- **Warehouse**: X-Small (2 credits/hour)
- **Auto-suspend**: 1 minute
- **Query caching**: Enabled
- **Estimated cost**: ~$2-5/day

### API Hosting
- **Docker**: $5-20/month (VPS)
- **Kubernetes**: $50-100/month (managed)
- **Serverless**: $0-10/month (low traffic)

### Total Estimated Cost
- **Development**: ~$5/month
- **Production**: ~$50-150/month

## Maintenance Windows

### Recommended Schedule
- **Backend updates**: Off-peak hours
- **Snowflake maintenance**: Automatic
- **Dashboard updates**: Zero-downtime

### Update Procedure
1. Deploy new backend version
2. Health check verification
3. Update dashboard (if needed)
4. Monitor for errors
5. Rollback if issues

## Technology Stack Summary

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | HTML/CSS/JS | ES6+ |
| Backend | FastAPI | 0.104+ |
| Language | Python | 3.11+ |
| Database | Snowflake | Current |
| Cache | cachetools | 5.3+ |
| Container | Docker | 20+ |
| Orchestration | Kubernetes | 1.25+ |

## API Contract

### Request Format
```http
GET /api/dashboard-summary HTTP/1.1
Host: localhost:8000
X-API-Key: optional_key_here
Accept: application/json
```

### Response Format
```json
{
  "cash_card_today": 245,
  "cash_card_baseline": 220.5,
  "cash_card_pct_change": 11.1,
  "cash_card_spike": true,
  "service_claims_today": 89,
  "service_claims_baseline": 85.0,
  "service_claims_pct_change": 4.7,
  "service_claims_spike": false,
  "visa_rejects_24h": 12,
  "marqeta_rejects_24h": 5,
  "last_updated": "2026-01-15T10:30:00.000000"
}
```

## Error Handling

### Error Response Format
```json
{
  "detail": "Error message here"
}
```

### HTTP Status Codes
- `200`: Success
- `403`: Invalid API key
- `500`: Server error (Snowflake connection, query error)

### Frontend Error Handling
1. Display error banner
2. Show "N/A" for metrics
3. Provide retry button
4. Log to console

## Configuration Management

### Environment Variables
```
Backend: .env file
Dashboard: localStorage (browser)
```

### Configuration Hierarchy
1. Environment variables (highest priority)
2. .env file
3. Default values (lowest priority)

## Version Control

### Git Strategy
- **Main branch**: Production-ready code
- **Feature branches**: New features
- **Tags**: Version releases

### Deployment Pipeline
```
Git Push → CI/CD → Build → Test → Deploy
```

## Documentation

### Available Docs
- `README.md`: Quick start
- `DEPLOYMENT.md`: Deployment guide
- `ARCHITECTURE.md`: This file
- `QUICKSTART.md`: 5-minute setup
- API Docs: `/docs` endpoint (Swagger)

## Support & Troubleshooting

### Debug Mode
Set in `.env`:
```env
LOG_LEVEL=DEBUG
```

### Logging
- Backend: stdout/stderr
- Snowflake: Query history
- Browser: Console logs

### Common Issues
See `DEPLOYMENT.md` troubleshooting section.
