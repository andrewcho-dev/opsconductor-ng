#!/bin/bash

# Import OpsConductor dashboards into Grafana

GRAFANA_URL="http://localhost:3200"
GRAFANA_USER="admin"
GRAFANA_PASS="admin123"
DASHBOARD_DIR="/home/opsconductor/opsconductor-ng/monitoring/grafana/dashboards"

import_dashboard() {
    local dashboard_file="$1"
    local dashboard_name=$(basename "$dashboard_file" .json)
    
    echo "Importing dashboard: $dashboard_name"
    
    # Create the import payload
    local payload=$(jq -n --argjson dashboard "$(cat "$dashboard_file")" '{
        dashboard: $dashboard,
        overwrite: true
    }')
    
    # Import the dashboard
    local response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -u "$GRAFANA_USER:$GRAFANA_PASS" \
        "$GRAFANA_URL/api/dashboards/db" \
        -d "$payload")
    
    echo "Response: $response"
    echo "---"
}

# Import all dashboard files
for dashboard in "$DASHBOARD_DIR"/*.json; do
    if [ -f "$dashboard" ]; then
        import_dashboard "$dashboard"
    fi
done

echo "Dashboard import completed!"