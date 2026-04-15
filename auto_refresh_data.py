#!/usr/bin/env python3
"""
Automatic Data Refresh Script
Runs Snowflake queries and updates JSON files for the dashboard
"""
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path to import snowflake
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

# Import snowflake connector
try:
    import snowflake.connector
except ImportError:
    print("❌ Error: snowflake-connector-python not installed")
    print("Run: pip install snowflake-connector-python")
    sys.exit(1)

# Snowflake queries
QUEUE_VOLUMES_QUERY = """
-- Cash Card & Service Claims Queue Volumes with Spike Detection
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
    ROUND(HANDLE_TIME_HOURS, 2) as handle_time_hours,
    ROUND(avg_7day_entered, 1) as baseline_avg,
    CASE 
        WHEN cases_entered > (avg_7day_entered + (2 * stddev_7day_entered)) 
        THEN 'SPIKE'
        ELSE 'NORMAL'
    END as spike_alert,
    ROUND(((cases_entered - avg_7day_entered) / NULLIF(avg_7day_entered, 0)) * 100, 1) as pct_change_from_baseline
FROM rolling_avg
WHERE DATE >= DATEADD('day', -14, CURRENT_DATE())
ORDER BY DATE DESC, QUEUE_NAME;
"""

NETWORK_REJECTS_QUERY = """
-- Network Rejects by Visa and Marqeta
WITH network_rejects AS (
    SELECT 
        TO_CHAR(DATE_TRUNC('day', CASE_CREATION_DATE_TIME_UTC), 'YYYY-MM-DD') as reject_date,
        CASE 
            WHEN SPONSORING_BANK = 'SUTTON' THEN 'Marqeta'
            WHEN SPONSORING_BANK IS NULL THEN 'Unknown'
            ELSE SPONSORING_BANK
        END as network_source,
        COUNT(DISTINCT SALESFORCE_CASE_NUMBER) as reject_count,
        ROUND(SUM(DISPUTRON_DISPUTED_AMOUNT_DOLLARS), 2) as disputed_amount_usd
    FROM CASH_DISPUTES.PUBLIC.CC_DISPUTES_CLAIM_DETAILS
    WHERE IDS_REJECTED_BY_NETWORK_REASON IS NOT NULL
        AND CASE_CREATION_DATE_TIME_UTC >= DATEADD('day', -14, CURRENT_DATE())
    GROUP BY 1, 2
)
SELECT 
    reject_date,
    network_source,
    reject_count,
    disputed_amount_usd
FROM network_rejects
ORDER BY reject_date DESC, network_source;
"""

def get_snowflake_connection():
    """Create Snowflake connection"""
    config = {
        "account": os.getenv('SNOWFLAKE_ACCOUNT'),
        "user": os.getenv('SNOWFLAKE_USER'),
        "warehouse": os.getenv('SNOWFLAKE_WAREHOUSE'),
        "database": "APP_DATAMART_CCO",
        "schema": "SFDC_CFONE",
        "role": os.getenv('SNOWFLAKE_ROLE'),
    }
    
    # Add authenticator if specified
    if os.getenv("SNOWFLAKE_AUTHENTICATOR"):
        config["authenticator"] = os.getenv("SNOWFLAKE_AUTHENTICATOR")
    elif os.getenv("SNOWFLAKE_PASSWORD"):
        config["password"] = os.getenv("SNOWFLAKE_PASSWORD")
    
    return snowflake.connector.connect(**config)

def run_query(conn, query):
    """Execute query and return results as list of dicts"""
    cursor = conn.cursor()
    cursor.execute(query)
    columns = [col[0] for col in cursor.description]
    results = []
    for row in cursor:
        results.append(dict(zip(columns, row)))
    cursor.close()
    return results

def save_json(data, filename):
    """Save data to JSON file"""
    filepath = os.path.join("data", filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"✅ Saved {len(data)} records to {filepath}")

def check_for_spikes(queue_data):
    """Check for volume spikes > 20K"""
    alerts = []
    today = queue_data[0]["date"] if queue_data else None
    
    for record in queue_data:
        if record["date"] == today and record["cases_entered"] > 20000:
            alerts.append({
                "queue": record["queue_name"],
                "volume": record["cases_entered"],
                "baseline": record["baseline_avg"],
                "pct_change": record["pct_change_from_baseline"]
            })
    
    return alerts

def main():
    print("=" * 60)
    print("🔄 Cash Card Dashboard - Automatic Data Refresh")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Connect to Snowflake
        print("📡 Connecting to Snowflake...")
        conn = get_snowflake_connection()
        print("✅ Connected successfully")
        print()
        
        # Run queue volumes query
        print("📊 Fetching queue volumes...")
        queue_data = run_query(conn, QUEUE_VOLUMES_QUERY)
        save_json(queue_data, "queue_volumes.json")
        print()
        
        # Run network rejects query
        print("🔌 Fetching network rejects...")
        reject_data = run_query(conn, NETWORK_REJECTS_QUERY)
        save_json(reject_data, "network_rejects.json")
        print()
        
        # Check for spikes
        print("⚠️  Checking for volume spikes (>20K)...")
        spikes = check_for_spikes(queue_data)
        if spikes:
            print("🚨 ALERT: High volume detected!")
            for spike in spikes:
                print(f"   • {spike['queue']}: {spike['volume']:,} cases")
                print(f"     (Baseline: {spike['baseline']:,.0f}, Change: {spike['pct_change']:+.1f}%)")
            
            # Save spike alert
            alert_data = {
                "timestamp": datetime.now().isoformat(),
                "spikes": spikes
            }
            save_json([alert_data], "spike_alerts.json")
        else:
            print("✅ No high-volume spikes detected")
        print()
        
        # Close connection
        conn.close()
        
        print("=" * 60)
        print("✅ Data refresh completed successfully!")
        print(f"⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
