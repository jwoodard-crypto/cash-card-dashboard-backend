"""
Simplified Cash Card Dashboard Backend
Uses local query execution instead of direct Snowflake connection
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from datetime import datetime
import subprocess
import json
import os

app = FastAPI(title="Cash Card Dashboard API - Simple")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response models
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

def run_snowflake_query(query: str):
    """Execute query using goose's snowflake connection"""
    # This will use the MCP snowflake extension that's already configured
    # We'll save queries to temp files and execute them
    import tempfile
    
    query_file = tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False)
    query_file.write(query)
    query_file.close()
    
    try:
        # Note: This is a placeholder - in reality we'd need to integrate with MCP
        # For now, let's return mock data structure
        return {"error": "Need to integrate with MCP"}
    finally:
        os.unlink(query_file.name)

@app.get("/")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "note": "Using simplified version - integrate with MCP for real data"
    }

@app.get("/api/dashboard-summary", response_model=DashboardSummary)
async def get_dashboard_summary():
    """Get dashboard summary with mock data for now"""
    
    # TODO: Replace with real queries through MCP
    # For now, return realistic mock data
    import random
    
    cash_card_baseline = 220.0
    service_claims_baseline = 85.0
    
    cash_card_today = int(cash_card_baseline + random.uniform(-30, 50))
    service_claims_today = int(service_claims_baseline + random.uniform(-15, 25))
    
    cash_card_pct = ((cash_card_today - cash_card_baseline) / cash_card_baseline) * 100
    service_claims_pct = ((service_claims_today - service_claims_baseline) / service_claims_baseline) * 100
    
    return DashboardSummary(
        cash_card_today=cash_card_today,
        cash_card_baseline=cash_card_baseline,
        cash_card_pct_change=round(cash_card_pct, 1),
        cash_card_spike=cash_card_pct > 20,
        service_claims_today=service_claims_today,
        service_claims_baseline=service_claims_baseline,
        service_claims_pct_change=round(service_claims_pct, 1),
        service_claims_spike=service_claims_pct > 20,
        visa_rejects_24h=random.randint(5, 15),
        marqeta_rejects_24h=random.randint(2, 8),
        last_updated=datetime.utcnow().isoformat()
    )

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting simplified Cash Card Dashboard API...")
    print("📊 Note: Using mock data - will integrate with real Snowflake next")
    print("🌐 API will be at: http://localhost:8000")
    print("📖 Docs at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
