#!/bin/bash
# Test script for Cash Card Dashboard API

API_URL="${1:-http://localhost:8000}"
API_KEY="${2:-}"

echo "🧪 Testing Cash Card Dashboard API"
echo "=================================="
echo "API URL: $API_URL"
echo ""

# Set headers
if [ -n "$API_KEY" ]; then
    HEADERS="-H X-API-Key:$API_KEY"
    echo "Using API Key: ${API_KEY:0:8}..."
else
    HEADERS=""
fi
echo ""

# Test 1: Health Check
echo "Test 1: Health Check"
echo "--------------------"
response=$(curl -s $HEADERS "$API_URL/")
echo "$response" | jq '.'
status=$(echo "$response" | jq -r '.status')
if [ "$status" = "healthy" ]; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi
echo ""

# Test 2: Queue Volumes
echo "Test 2: Queue Volumes"
echo "--------------------"
response=$(curl -s $HEADERS "$API_URL/api/queue-volumes")
count=$(echo "$response" | jq '. | length')
echo "Returned $count records"
if [ "$count" -gt 0 ]; then
    echo "Sample record:"
    echo "$response" | jq '.[0]'
    echo "✅ Queue volumes endpoint working"
else
    echo "❌ No queue volume data returned"
fi
echo ""

# Test 3: Network Rejects
echo "Test 3: Network Rejects"
echo "----------------------"
response=$(curl -s $HEADERS "$API_URL/api/network-rejects")
count=$(echo "$response" | jq '. | length')
echo "Returned $count records"
if [ "$count" -gt 0 ]; then
    echo "Sample record:"
    echo "$response" | jq '.[0]'
    echo "✅ Network rejects endpoint working"
else
    echo "⚠️  No network reject data (may be normal if no rejects recently)"
fi
echo ""

# Test 4: Dashboard Summary
echo "Test 4: Dashboard Summary"
echo "------------------------"
response=$(curl -s $HEADERS "$API_URL/api/dashboard-summary")
echo "$response" | jq '.'
cash_card=$(echo "$response" | jq -r '.cash_card_today')
if [ "$cash_card" != "null" ]; then
    echo "✅ Dashboard summary endpoint working"
    echo ""
    echo "Current Metrics:"
    echo "  Cash Card Cases: $cash_card"
    echo "  Service Claims: $(echo "$response" | jq -r '.service_claims_today')"
    echo "  Visa Rejects: $(echo "$response" | jq -r '.visa_rejects_24h')"
    echo "  Marqeta Rejects: $(echo "$response" | jq -r '.marqeta_rejects_24h')"
    
    # Check for spikes
    if [ "$(echo "$response" | jq -r '.cash_card_spike')" = "true" ]; then
        echo "  ⚠️  CASH CARD SPIKE DETECTED!"
    fi
    if [ "$(echo "$response" | jq -r '.service_claims_spike')" = "true" ]; then
        echo "  ⚠️  SERVICE CLAIMS SPIKE DETECTED!"
    fi
else
    echo "❌ Dashboard summary failed"
fi
echo ""

# Test 5: Response Time
echo "Test 5: Response Time"
echo "--------------------"
start=$(date +%s%N)
curl -s $HEADERS "$API_URL/api/dashboard-summary" > /dev/null
end=$(date +%s%N)
duration=$(( (end - start) / 1000000 ))
echo "Response time: ${duration}ms"
if [ "$duration" -lt 5000 ]; then
    echo "✅ Response time acceptable"
else
    echo "⚠️  Response time slow (>5s)"
fi
echo ""

# Summary
echo "=================================="
echo "✅ All tests completed!"
echo ""
echo "Next steps:"
echo "1. Open dashboard app"
echo "2. Configure API URL: $API_URL"
if [ -n "$API_KEY" ]; then
    echo "3. Configure API Key: $API_KEY"
fi
echo "4. Verify real data displays"
echo ""
