#!/bin/bash

echo "🚀 Installing node_exporter on all network devices..."

# Get all container names for enterprise-final
containers=$(docker ps --format "{{.Names}}" | grep clab-enterprise-final)

for container in $containers; do
    echo "📦 Installing on $container..."
    
    # Install node-exporter and start it
    docker exec $container sh -c "
        # Kill any existing node_exporter processes
        pkill -f node_exporter 2>/dev/null || true
        
        # Install if not already installed
        if ! command -v node_exporter >/dev/null 2>&1; then
            apk add --no-cache prometheus-node-exporter
        fi
        
        # Start node_exporter in background
        nohup node_exporter --web.listen-address=:9100 > /tmp/node_exporter.log 2>&1 &
        
        # Wait a moment for startup
        sleep 2
        
        # Check if it's running
        if pgrep -f node_exporter > /dev/null; then
            echo '✅ node_exporter started successfully'
        else
            echo '❌ Failed to start node_exporter'
            cat /tmp/node_exporter.log
        fi
    " &
done

# Wait for all background jobs to complete
wait

echo "⏳ Waiting 10 seconds for all exporters to fully start..."
sleep 10

echo "🔍 Checking status of all node exporters..."
for container in $containers; do
    ip=$(docker inspect $container | jq -r '.[0].NetworkSettings.Networks[].IPAddress')
    container_short=$(echo $container | sed 's/clab-enterprise-final-//')
    
    if curl -s --connect-timeout 3 http://$ip:9100/metrics > /dev/null; then
        echo "✅ $container_short ($ip): UP"
    else
        echo "❌ $container_short ($ip): DOWN"
    fi
done

echo "✨ Installation complete!"
