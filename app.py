"""
Cash Card Dashboard Backend API
Connects to Snowflake and serves dashboard data
"""
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from cachetools import TTLCache
import snowflake.connector
from contextlib import contextmanager

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Cash Card Dashboard API",
    description="Real-time Cash Card queue volumes and network rejects",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache configuration (5-minute TTL)
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", 300))
cache = TTLCache(maxsize=100, ttl=CACHE_TTL)

# Snowflake configuration
SNOWFLAKE_CONFIG = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "user": os.getenv("SNOWFLAKE_USER"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
    "database": os.getenv("SNOWFLAKE_DATABASE"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA"),
    "role": os.getenv("SNOWFLAKE_ROLE"),
}

# Add authenticator if specified (for SSO)
if os.getenv("SNOWFLAKE_AUTHENTICATOR"):
    SNOWFLAKE_CONFIG["authenticator"] = os.getenv("SNOWFLAKE_AUTHENTICATOR")
elif os.getenv("SNOWFLAKE_PASSWORD"):
    SNOWFLAKE_CONFIG["password"] = os.getenv("SNOWFLAKE_PASSWORD")

# Response models
class QueueMetric(BaseModel):
    date: str
    queue_name: str
    cases_entered: int
    cases_handled: int
    handle_time_hours: float
    baseline_avg: float
    spike_alert: str
    pct_change_from_baseline: float

class NetworkReject(BaseModel):
    reject_date: str
    network_source: str
    daily_rejects: int
    disputed_amount_usd: float
    baseline_avg: float
    spike_alert: str
    pct_change_from_baseline: float

class DashboardSummary(BaseModel):
    cash_card_today: int
    cash_card_baseline: float
    cash_card_pct_change: float
    cash_card_spike: bool
    service_claims_today: int
    service_claims_baseline: float
    service_claims_pct_change: float
    service_claims_spike: bool
    visa_rejects_24h: int
    marqeta_rejects_24h: int
    last_updated: str

class HealthCheck(BaseModel):
    status: str
    timestamp: str
    snowflake_connected: bool

# Snowflake connection manager
@contextmanager
def get_snowflake_connection():
    """Context manager for Snowflake connections"""
    conn = None
    try:
        conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
        yield conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Snowflake connection error: {str(e)}")
    finally:
        if conn:
            conn.close()

# Optional API key authentication
async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key if configured"""
    required_key = os.getenv("API_KEY")
    if required_key and x_api_key != required_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True

# SQL Queries
QUEUE_VOLUMES_QUERY = """
WITH daily_volumes AS (
    SELECT 
        DATE,
        QUEUE_NAME,
        ENTERED as cases_entered,
        HANDLED as cases_handled,
        HANDLE_TIME_HOURS
    FROM APP_DATAMART_CCO.SFDC_CFONE.DISPUTE_VOLUME_BY_QUEUE_DRILL_DOWN
    WHERE QUEUE_NAME IN ('Disputes Cash Card', 'Disputes Service Claim')
        AND DATE >= DATEADD('day', -30, CURRENT_DATE())
    ORDER BY DATE DESC, QUEUE_NAME
),
rolling_avg AS (
    SELECT 
        DATE,
        QUEUE_NAME,
        cases_entered,
        cases_handled,
        HANDLE_TIME_HOURS,
        AVG(cases_entered) OVER (
            PARTITION BY QUEUE_NAME 
            ORDER BY DATE 
            ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
        ) as avg_7day_entered,
        STDDEV(cases_entered) OVER (
            PARTITION BY QUEUE_NAME 
            ORDER BY DATE 
            ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
        ) as stddev_7day_entered
    FROM daily_volumes
)
SELECT 
    TO_CHAR(DATE, 'YYYY-MM-DD') as date,
    QUEUE_NAME as queue_name,
    cases_entered,
    cases_handled,
    HANDLE_TIME_HOURS as handle_time_hours,
    ROUND(avg_7day_entered, 1) as baseline_avg,
    CASE 
        WHEN cases_entered > (avg_7day_entered + (2 * stddev_7day_entered)) 
        THEN '⚠️ SPIKE'
        ELSE '✓'
    END as spike_alert,
    ROUND(((cases_entered - avg_7day_entered) / NULLIF(avg_7day_entered, 0)) * 100, 1) as pct_change_from_baseline
FROM rolling_avg
WHERE DATE >= DATEADD('day', -14, CURRENT_DATE())
ORDER BY DATE DESC, QUEUE_NAME
"""

NETWORK_REJECTS_QUERY = """
WITH network_rejects AS (
    SELECT 
        DATE_TRUNC('day', CASE_CREATION_DATE_TIME_UTC) as reject_date,
        SPONSORING_BANK,
        IDS_REJECTED_BY_NETWORK_REASON,
        COUNT(DISTINCT SALESFORCE_CASE_NUMBER) as reject_count,
        SUM(DISPUTRON_DISPUTED_AMOUNT_DOLLARS) as total_disputed_amount
    FROM CASH_DISPUTES.PUBLIC.CC_DISPUTES_CLAIM_DETAILS
    WHERE IDS_REJECTED_BY_NETWORK_REASON IS NOT NULL
        AND CASE_CREATION_DATE_TIME_UTC >= DATEADD('day', -30, CURRENT_DATE())
    GROUP BY 1, 2, 3
),
daily_totals AS (
    SELECT 
        reject_date,
        SPONSORING_BANK,
        SUM(reject_count) as daily_rejects,
        SUM(total_disputed_amount) as daily_amount,
        AVG(SUM(reject_count)) OVER (
            PARTITION BY SPONSORING_BANK 
            ORDER BY reject_date 
            ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
        ) as avg_7day_rejects,
        STDDEV(SUM(reject_count)) OVER (
            PARTITION BY SPONSORING_BANK 
            ORDER BY reject_date 
            ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
        ) as stddev_7day_rejects
    FROM network_rejects
    GROUP BY reject_date, SPONSORING_BANK
)
SELECT 
    TO_CHAR(reject_date, 'YYYY-MM-DD') as reject_date,
    CASE 
        WHEN SPONSORING_BANK = 'SUTTON' THEN 'Marqeta'
        WHEN SPONSORING_BANK IS NULL THEN 'Unknown'
        ELSE SPONSORING_BANK
    END as network_source,
    daily_rejects,
    ROUND(daily_amount, 2) as disputed_amount_usd,
    ROUND(avg_7day_rejects, 1) as baseline_avg,
    CASE 
        WHEN daily_rejects > (avg_7day_rejects + (2 * stddev_7day_rejects)) 
        THEN '⚠️ SPIKE'
        ELSE '✓'
    END as spike_alert,
    ROUND(((daily_rejects - avg_7day_rejects) / NULLIF(avg_7day_rejects, 0)) * 100, 1) as pct_change_from_baseline
FROM daily_totals
WHERE reject_date >= DATEADD('day', -14, CURRENT_DATE())
ORDER BY reject_date DESC, network_source
"""

# API Endpoints

@app.get("/", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    try:
        with get_snowflake_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            snowflake_connected = True
    except:
        snowflake_connected = False
    
    return HealthCheck(
        status="healthy" if snowflake_connected else "degraded",
        timestamp=datetime.utcnow().isoformat(),
        snowflake_connected=snowflake_connected
    )

@app.get("/api/queue-volumes", response_model=List[QueueMetric])
async def get_queue_volumes(authenticated: bool = Depends(verify_api_key)):
    """Get queue volumes with spike detection"""
    cache_key = "queue_volumes"
    
    # Check cache
    if cache_key in cache:
        return cache[cache_key]
    
    try:
        with get_snowflake_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(QUEUE_VOLUMES_QUERY)
            
            results = []
            for row in cursor.fetchall():
                results.append(QueueMetric(
                    date=row[0],
                    queue_name=row[1],
                    cases_entered=row[2],
                    cases_handled=row[3],
                    handle_time_hours=row[4],
                    baseline_avg=row[5],
                    spike_alert=row[6],
                    pct_change_from_baseline=row[7]
                ))
            
            # Cache results
            cache[cache_key] = results
            return results
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")

@app.get("/api/network-rejects", response_model=List[NetworkReject])
async def get_network_rejects(authenticated: bool = Depends(verify_api_key)):
    """Get network rejects by source (Visa/Marqeta)"""
    cache_key = "network_rejects"
    
    # Check cache
    if cache_key in cache:
        return cache[cache_key]
    
    try:
        with get_snowflake_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(NETWORK_REJECTS_QUERY)
            
            results = []
            for row in cursor.fetchall():
                results.append(NetworkReject(
                    reject_date=row[0],
                    network_source=row[1],
                    daily_rejects=row[2],
                    disputed_amount_usd=row[3],
                    baseline_avg=row[4],
                    spike_alert=row[5],
                    pct_change_from_baseline=row[6]
                ))
            
            # Cache results
            cache[cache_key] = results
            return results
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")

@app.get("/api/dashboard-summary", response_model=DashboardSummary)
async def get_dashboard_summary(authenticated: bool = Depends(verify_api_key)):
    """Get summarized dashboard data for main view"""
    cache_key = "dashboard_summary"
    
    # Check cache
    if cache_key in cache:
        return cache[cache_key]
    
    try:
        # Get queue volumes
        queue_data = await get_queue_volumes(authenticated=True)
        
        # Get network rejects
        reject_data = await get_network_rejects(authenticated=True)
        
        # Extract today's data
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Cash Card metrics
        cash_card_today_data = [q for q in queue_data if q.queue_name == "Disputes Cash Card" and q.date == today]
        cash_card_today = cash_card_today_data[0] if cash_card_today_data else None
        
        # Service Claims metrics
        service_claims_today_data = [q for q in queue_data if q.queue_name == "Disputes Service Claim" and q.date == today]
        service_claims_today = service_claims_today_data[0] if service_claims_today_data else None
        
        # Network rejects (last 24 hours)
        visa_rejects = sum(r.daily_rejects for r in reject_data if r.network_source == "Visa" and r.reject_date == today)
        marqeta_rejects = sum(r.daily_rejects for r in reject_data if r.network_source == "Marqeta" and r.reject_date == today)
        
        summary = DashboardSummary(
            cash_card_today=cash_card_today.cases_entered if cash_card_today else 0,
            cash_card_baseline=cash_card_today.baseline_avg if cash_card_today else 0,
            cash_card_pct_change=cash_card_today.pct_change_from_baseline if cash_card_today else 0,
            cash_card_spike=cash_card_today.spike_alert == "⚠️ SPIKE" if cash_card_today else False,
            service_claims_today=service_claims_today.cases_entered if service_claims_today else 0,
            service_claims_baseline=service_claims_today.baseline_avg if service_claims_today else 0,
            service_claims_pct_change=service_claims_today.pct_change_from_baseline if service_claims_today else 0,
            service_claims_spike=service_claims_today.spike_alert == "⚠️ SPIKE" if service_claims_today else False,
            visa_rejects_24h=visa_rejects,
            marqeta_rejects_24h=marqeta_rejects,
            last_updated=datetime.utcnow().isoformat()
        )
        
        # Cache results
        cache[cache_key] = summary
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
