#!/bin/bash

echo "🚂 Cash Card Dashboard - Railway Deployment Helper"
echo "=================================================="
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "📦 Railway CLI not found. Installing..."
    npm install -g @railway/cli
    echo "✅ Railway CLI installed!"
    echo ""
fi

echo "🔐 Step 1: Login to Railway"
railway login

echo ""
echo "📁 Step 2: Initialize Railway project"
railway init

echo ""
echo "🚀 Step 3: Deploy!"
railway up

echo ""
echo "⚙️  Step 4: Set environment variables"
echo "Run these commands to set your Snowflake credentials:"
echo ""
echo "railway variables set SNOWFLAKE_ACCOUNT=SQUARE"
echo "railway variables set SNOWFLAKE_USER=svc_cash_card_dashboard"
echo "railway variables set SNOWFLAKE_PASSWORD=<your_service_account_password>"
echo "railway variables set SNOWFLAKE_WAREHOUSE=ADHOC__LARGE"
echo "railway variables set SNOWFLAKE_DATABASE=APP_DATAMART_CCO"
echo "railway variables set SNOWFLAKE_SCHEMA=PUBLIC"
echo "railway variables set SNOWFLAKE_ROLE=svc_cash_card_dashboard"
echo ""
echo "Or set them in the Railway dashboard: https://railway.app/dashboard"
echo ""
echo "🎉 Deployment complete!"
echo "Your API will be available at the URL shown above."
echo ""
echo "📝 Next steps:"
echo "1. Copy your Railway URL"
echo "2. Update the dashboard app to use that URL"
echo "3. Share with your team!"
