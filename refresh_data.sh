#!/bin/bash
# Refresh Dashboard Data from Snowflake
# Run this script whenever you want to update the dashboard with fresh data

echo "🔄 Refreshing Cash Card Dashboard Data..."
echo "=========================================="
echo ""

# Note: This script is a template. To actually refresh data:
# 1. Open Goose
# 2. Ask: "Run the Cash Card dashboard queries and update the JSON files"
# 3. Or manually run the queries and save to data/ directory

echo "To refresh data, you need to:"
echo "1. Run the Snowflake queries (see queries below)"
echo "2. Save results to JSON files in data/ directory"
echo ""
echo "📝 Query 1: Queue Volumes"
echo "   Save to: data/queue_volumes.json"
echo ""
echo "📝 Query 2: Network Rejects"
echo "   Save to: data/network_rejects.json"
echo ""
echo "Or ask Goose to run the queries for you!"
echo ""
echo "Once updated, the dashboard will show new data on next refresh."
