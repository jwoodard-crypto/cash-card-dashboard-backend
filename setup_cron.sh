#!/bin/bash
# Setup cron job for automatic dashboard data refresh

echo "⏰ Setting up automatic data refresh..."
echo "========================================"
echo ""

# Get the current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REFRESH_SCRIPT="$SCRIPT_DIR/auto_refresh_data.py"
LOG_DIR="$SCRIPT_DIR/logs"

# Create logs directory
mkdir -p "$LOG_DIR"

# Create wrapper script that handles environment
WRAPPER_SCRIPT="$SCRIPT_DIR/cron_wrapper.sh"
cat > "$WRAPPER_SCRIPT" << EOF
#!/bin/bash
cd "$SCRIPT_DIR"
source venv/bin/activate 2>/dev/null || true
python3 "$REFRESH_SCRIPT" >> "$LOG_DIR/refresh.log" 2>&1
EOF

chmod +x "$WRAPPER_SCRIPT"

echo "📝 Cron job options:"
echo ""
echo "1. Every day at 6:00 AM"
echo "   0 6 * * * $WRAPPER_SCRIPT"
echo ""
echo "2. Every day at 6:00 AM and 6:00 PM"
echo "   0 6,18 * * * $WRAPPER_SCRIPT"
echo ""
echo "3. Every 4 hours"
echo "   0 */4 * * * $WRAPPER_SCRIPT"
echo ""
echo "4. Every hour during business hours (8 AM - 6 PM, Mon-Fri)"
echo "   0 8-18 * * 1-5 $WRAPPER_SCRIPT"
echo ""

read -p "Which option would you like? (1-4): " choice

case $choice in
    1)
        CRON_SCHEDULE="0 6 * * *"
        DESCRIPTION="daily at 6:00 AM"
        ;;
    2)
        CRON_SCHEDULE="0 6,18 * * *"
        DESCRIPTION="twice daily (6 AM and 6 PM)"
        ;;
    3)
        CRON_SCHEDULE="0 */4 * * *"
        DESCRIPTION="every 4 hours"
        ;;
    4)
        CRON_SCHEDULE="0 8-18 * * 1-5"
        DESCRIPTION="hourly during business hours (Mon-Fri, 8 AM-6 PM)"
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac

echo ""
echo "Setting up cron job to run $DESCRIPTION..."

# Add to crontab
(crontab -l 2>/dev/null | grep -v "cash_card_dashboard"; echo "$CRON_SCHEDULE $WRAPPER_SCRIPT") | crontab -

echo "✅ Cron job installed!"
echo ""
echo "📋 Current crontab:"
crontab -l | grep cash_card_dashboard
echo ""
echo "📁 Logs will be saved to: $LOG_DIR/refresh.log"
echo ""
echo "To view logs:"
echo "  tail -f $LOG_DIR/refresh.log"
echo ""
echo "To remove cron job:"
echo "  crontab -l | grep -v cash_card_dashboard | crontab -"
echo ""
