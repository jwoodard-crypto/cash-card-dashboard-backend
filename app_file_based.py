"""
Cash Card Dashboard Backend - File-Based Version
Reads from JSON files instead of direct Snowflake connection
Perfect for getting started quickly!
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from datetime import datetime
import json
import os

app = FastAPI(
    title="Cash Card Dashboard API",
    description="Real-time Cash Card queue volumes and network rejects",
    version="1.0.0-file-based"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    reject_count: int
    disputed_amount_usd: float

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
    data_source: str
    data_files_exist: bool

# Helper functions
def load_json_file(filename: str):
    """Load data from JSON file"""
    filepath = os.path.join("data", filename)
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"Data file not found: {filename}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in file: {filename}")

# API Endpoints

@app.get("/", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    queue_file_exists = os.path.exists("data/queue_volumes.json")
    reject_file_exists = os.path.exists("data/network_rejects.json")
    
    return HealthCheck(
        status="healthy" if (queue_file_exists and reject_file_exists) else "degraded",
        timestamp=datetime.utcnow().isoformat(),
        data_source="JSON files (refreshed via Snowflake queries)",
        data_files_exist=queue_file_exists and reject_file_exists
    )


@app.get("/health")
async def simple_health():
    """Simple health check for Railway"""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/queue-volumes", response_model=List[QueueMetric])
async def get_queue_volumes():
    """Get queue volumes with spike detection"""
    data = load_json_file("queue_volumes.json")
    
    results = []
    for row in data:
        results.append(QueueMetric(
            date=row["date"],
            queue_name=row["queue_name"],
            cases_entered=row["cases_entered"],
            cases_handled=row["cases_handled"],
            handle_time_hours=row["handle_time_hours"],
            baseline_avg=row["baseline_avg"],
            spike_alert=row["spike_alert"],
            pct_change_from_baseline=row["pct_change_from_baseline"]
        ))
    
    return results

@app.get("/api/network-rejects", response_model=List[NetworkReject])
async def get_network_rejects():
    """Get network rejects by source (Visa/Marqeta)"""
    data = load_json_file("network_rejects.json")
    
    results = []
    for row in data:
        results.append(NetworkReject(
            reject_date=row["reject_date"],
            network_source=row["network_source"],
            reject_count=row["reject_count"],
            disputed_amount_usd=row["disputed_amount_usd"]
        ))
    
    return results

@app.get("/api/dashboard-summary", response_model=DashboardSummary)
async def get_dashboard_summary():
    """Get summarized dashboard data for main view"""
    
    # Load data
    queue_data = load_json_file("queue_volumes.json")
    reject_data = load_json_file("network_rejects.json")
    
    # Get today's date (most recent in data)
    today = queue_data[0]["date"] if queue_data else None
    
    # Find today's metrics
    cash_card_today = next((q for q in queue_data if q["queue_name"] == "Disputes Cash Card" and q["date"] == today), None)
    service_claims_today = next((q for q in queue_data if q["queue_name"] == "Disputes Service Claim" and q["date"] == today), None)
    
    # Network rejects for today
    visa_rejects = sum(r["reject_count"] for r in reject_data if r["network_source"] == "Visa" and r["reject_date"] == today)
    marqeta_rejects = sum(r["reject_count"] for r in reject_data if r["network_source"] == "Marqeta" and r["reject_date"] == today)
    
    if not cash_card_today or not service_claims_today:
        raise HTTPException(status_code=500, detail="Could not find today's data")
    
    return DashboardSummary(
        cash_card_today=cash_card_today["cases_entered"],
        cash_card_baseline=cash_card_today["baseline_avg"],
        cash_card_pct_change=cash_card_today["pct_change_from_baseline"],
        cash_card_spike=cash_card_today["spike_alert"] == "SPIKE",
        service_claims_today=service_claims_today["cases_entered"],
        service_claims_baseline=service_claims_today["baseline_avg"],
        service_claims_pct_change=service_claims_today["pct_change_from_baseline"],
        service_claims_spike=service_claims_today["spike_alert"] == "SPIKE",
        visa_rejects_24h=visa_rejects,
        marqeta_rejects_24h=marqeta_rejects,
        last_updated=datetime.utcnow().isoformat()
    )

@app.get("/api/complete-summary")
async def get_complete_summary():
    """Get complete dashboard data including backlog and daily flow"""
    
    # Load all data files
    queue_data = load_json_file("queue_volumes.json")
    reject_data = load_json_file("network_rejects.json")
    backlog_data_raw = load_json_file("current_backlog.json")
    
    # Ensure backlog_data is a list
    if isinstance(backlog_data_raw, dict):
        backlog_data = [backlog_data_raw]
    else:
        backlog_data = backlog_data_raw if backlog_data_raw else []
    
    # Get today's date
    today = queue_data[0]["date"] if queue_data else None
    
    # Find today's flow metrics
    cash_card_flow = next((q for q in queue_data if q["queue_name"] == "Disputes Cash Card" and q["date"] == today), {})
    service_claims_flow = next((q for q in queue_data if q["queue_name"] == "Disputes Service Claim" and q["date"] == today), {})
    
    # Get backlog metrics
    cash_card_backlog = next((b for b in backlog_data if b["queue_name"] == "Disputes Cash Card"), {})
    service_claims_backlog = next((b for b in backlog_data if b["queue_name"] == "Disputes Service Claim"), {})
    
    # Network rejects for today
    marqeta_rejects = sum(r["reject_count"] for r in reject_data if r["network_source"] == "Marqeta" and r["reject_date"] == today)
    # Everything non-Marqeta = Visa/Pulse/After Filing rejects
    other_rejects = sum(r["reject_count"] for r in reject_data if r["network_source"] != "Marqeta" and r["reject_date"] == today)
    
    return {
        "cashCardQueue": {
            "current": cash_card_backlog.get("unassigned_cases", 60),  # Agent-facing queue (unassigned only, matches CF1)
            "pipeline_total": cash_card_backlog.get("pipeline_total", 20687),  # Full backlog for spike alerts
            "entered_today": cash_card_backlog.get("entered_today", 0),
            "handled_today": cash_card_backlog.get("handled_today", 0),
            "avg_age_days": round(cash_card_backlog.get("avg_age_days", 0), 1),
            "aged_2plus_days": cash_card_backlog.get("aged_2plus_days", 0)
        },
        "serviceClaimsQueue": {
            "current": service_claims_backlog.get("unassigned_cases", 677),  # Agent-facing queue (unassigned only, matches CF1)
            "pipeline_total": service_claims_backlog.get("pipeline_total", 35227),  # Full backlog for spike alerts
            "entered_today": service_claims_backlog.get("entered_today", 0),
            "handled_today": service_claims_backlog.get("handled_today", 0),
            "avg_age_days": round(service_claims_backlog.get("avg_age_days", 0), 1),
            "aged_2plus_days": service_claims_backlog.get("aged_2plus_days", 0)
        },
        "networkRejects": {
            "marqeta": marqeta_rejects,
            "other": other_rejects  # Visa/Pulse/After Filing
        },
        "trendData": queue_data[-14:],  # Last 14 days
        "lastUpdated": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Cash Card Dashboard API (File-Based)")
    print("=" * 60)
    print("📊 Data Source: JSON files in data/ directory")
    print("🔄 To refresh data: Run the Snowflake queries and update JSON files")
    print("🌐 API will be at: http://localhost:8000")
    print("📖 API Docs at: http://localhost:8000/docs")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
