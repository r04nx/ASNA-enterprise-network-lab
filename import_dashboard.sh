#!/bin/bash

echo "📊 Importing Self-Healing Network Dashboard into Grafana..."

# Wait for Grafana to be fully ready
sleep 5

# Import the dashboard via API
curl -X POST \
  -H "Content-Type: application/json" \
  -d @monitoring/grafana/grafana-provisioning/dashboards/selfheal-network-dashboard.json \
  -u admin:asna123 \
  http://localhost:3000/api/dashboards/db

echo ""
echo "✅ Dashboard import attempted!"
echo "🌐 Access the dashboard at: http://localhost:3000"
echo "📊 Look for 'Self-Healing Network Analytics - Journal Quality' dashboard"
