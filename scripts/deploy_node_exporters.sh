#!/bin/bash

echo "🧹 Cleaning up existing node_exporter processes..."

# Get all container names for enterprise-final
containers=$(docker ps --format "{{.Names}}" | grep clab-enterprise-final)

# Kill all existing node_exporter processes
for container in $containers; do
    echo "🔄 Cleaning $container..."
    docker exec $container sh -c "pkill -f node_exporter 2>/dev/null || true"
done

sleep 3

echo "📦 Installing and starting node_exporter on all devices..."

for container in $containers; do
    echo "⚡ Setting up $container..."
    
    # Install and run node-exporter
    docker exec $container sh -c "
        # Install node-exporter if not present
        if ! command -v node_exporter >/dev/null 2>&1; then
            apk add --no-cache prometheus-node-exporter >/dev/null 2>&1
        fi
        
        # Start node_exporter in background with custom collectors
        nohup node_exporter \
            --web.listen-address=:9100 \
            --collector.disable-defaults \
            --collector.cpu \
            --collector.meminfo \
            --collector.diskstats \
            --collector.filesystem \
            --collector.netdev \
            --collector.loadavg \
            --collector.uname \
            > /tmp/node_exporter.log 2>&1 &
        
        # Give it a moment to start
        sleep 1
    "
done

echo "⏳ Waiting for all exporters to initialize..."
sleep 5

echo "🔍 Testing all node exporters..."
success_count=0
total_count=0

for container in $containers; do
    ip=$(docker inspect $container | jq -r '.[0].NetworkSettings.Networks[].IPAddress')
    container_short=$(echo $container | sed 's/clab-enterprise-final-//')
    total_count=$((total_count + 1))
    
    if timeout 5 curl -s http://$ip:9100/metrics | head -1 | grep -q "#"; then
        echo "✅ $container_short ($ip): UP"
        success_count=$((success_count + 1))
    else
        echo "❌ $container_short ($ip): DOWN"
    fi
done

echo ""
echo "📊 Summary: $success_count/$total_count exporters are running"

# Wait a moment for Prometheus to scrape
echo "⏳ Waiting for Prometheus to discover targets..."
sleep 10

# Check Prometheus targets
echo "🎯 Checking Prometheus targets..."
curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | select(.labels.job == "network-devices") | "\(.labels.instance): \(.health)"' | sort

echo "✨ Deployment complete! Check Grafana at http://localhost:3000 (admin/asna123)"
