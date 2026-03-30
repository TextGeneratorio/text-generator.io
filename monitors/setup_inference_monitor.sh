#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_FILE="$SCRIPT_DIR/systemd/text-generator-monitor-inference-agent.service"
SERVICE_NAME="text-generator-monitor-inference-agent"

case "${1:-install}" in
    install)
        echo "Installing $SERVICE_NAME..."
        sudo cp "$SERVICE_FILE" /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable "$SERVICE_NAME"
        sudo systemctl start "$SERVICE_NAME"
        echo "Done. Status:"
        sudo systemctl status "$SERVICE_NAME" --no-pager -l
        ;;
    remove)
        echo "Removing $SERVICE_NAME..."
        sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true
        sudo systemctl disable "$SERVICE_NAME" 2>/dev/null || true
        sudo rm -f "/etc/systemd/system/$SERVICE_NAME.service"
        sudo systemctl daemon-reload
        echo "Removed."
        ;;
    status)
        sudo systemctl status "$SERVICE_NAME" --no-pager -l
        echo ""
        echo "Recent log:"
        tail -20 "$SCRIPT_DIR/monitor_inference_agent.log" 2>/dev/null || echo "(no log yet)"
        ;;
    *)
        echo "Usage: $0 {install|remove|status}"
        exit 1
        ;;
esac
