#!/bin/bash

# Enhanced Self-Healing Agents Deployment Script
# Deploys agents across all containerlab topology nodes with proper configuration

set -e

echo "🚀 Deploying Enhanced Self-Healing Agents Across Network Topology"
echo "=================================================================="

AGENT_FILE="scripts/agent/enhanced_selfheal_agent.py"
AGENT_TARGET="/usr/local/bin/enhanced_selfheal_agent.py"
WEB_SERVER_IP="172.20.20.7"

# Function to deploy agent to a container
deploy_agent() {
    local container=$1
    local device_name=$2
    local device_role=$3
    local device_ip=$4
    local metrics_port=$5
    
    echo "📦 Deploying to $device_name ($container)..."
    
    # Copy agent file
    docker cp "$AGENT_FILE" "$container:$AGENT_TARGET" || {
        echo "   ❌ Failed to copy agent to $container"
        return 1
    }
    
    # Make executable
    docker exec "$container" chmod +x "$AGENT_TARGET" || {
        echo "   ❌ Failed to make agent executable in $container"
        return 1
    }
    
    # Kill existing agent if running
    docker exec "$container" pkill -f "enhanced_selfheal_agent" 2>/dev/null || true
    
    # Start agent with proper environment
    docker exec -d \
        -e DEVICE_NAME="$device_name" \
        -e DEVICE_ROLE="$device_role" \
        -e DEVICE_IP="$device_ip" \
        -e AGENT_IFACE="eth0" \
        -e AGENT_GATEWAY="172.20.20.1" \
        -e AGENT_CHECK_HOST="$WEB_SERVER_IP" \
        -e AGENT_CHECK_PORT="80" \
        -e AGENT_SLEEP="3" \
        -e AGENT_LOG_LEVEL="INFO" \
        -e METRICS_PORT="$metrics_port" \
        "$container" \
        python3 "$AGENT_TARGET" || {
        echo "   ❌ Failed to start agent in $container"
        return 1
    }
    
    # Brief wait to check if agent started
    sleep 2
    if docker exec "$container" pgrep -f "enhanced_selfheal_agent" >/dev/null; then
        echo "   ✅ Agent deployed and running on $device_name"
        return 0
    else
        echo "   ⚠️  Agent deployed but may not be running on $device_name"
        return 1
    fi
}

# Deployment configuration: container_name:device_name:role:ip:metrics_port
DEPLOYMENTS=(
    # Core Layer
    "clab-enterprise-final-core-router:core-router:core:172.20.20.10:9200"
    "clab-enterprise-final-core-firewall:core-firewall:core:172.20.20.2:9200"
    
    # Distribution Layer
    "clab-enterprise-final-dist-eng:dist-eng:distribution:172.20.20.11:9200"
    "clab-enterprise-final-dist-sales:dist-sales:distribution:172.20.20.16:9200"
    "clab-enterprise-final-dist-servers:dist-servers:distribution:172.20.20.8:9200"
    
    # Access Layer
    "clab-enterprise-final-access-eng:access-eng:access:172.20.20.15:9200"
    "clab-enterprise-final-access-sales:access-sales:access:172.20.20.12:9200"
    
    # Client Devices
    "clab-enterprise-final-eng-gui:eng-gui:client:172.20.20.14:9200"
    "clab-enterprise-final-eng-dev:eng-dev:client:172.20.20.3:9200"
    "clab-enterprise-final-sales-gui:sales-gui:client:172.20.20.4:9200"
    "clab-enterprise-final-sales-mobile:sales-mobile:client:172.20.20.13:9200"
    
    # Servers
    "clab-enterprise-final-web-server:web-server:server:172.20.20.7:9200"
    "clab-enterprise-final-db-server:db-server:server:172.20.20.9:9200"
    "clab-enterprise-final-file-server:file-server:server:172.20.20.6:9200"
    "clab-enterprise-final-public-web:public-web:server:172.20.20.5:9200"
)

successful_deployments=0
failed_deployments=0

echo ""
echo "🎯 Starting Agent Deployments..."
echo ""

for deployment in "${DEPLOYMENTS[@]}"; do
    IFS=':' read -r container device_name role ip metrics_port <<< "$deployment"
    
    if deploy_agent "$container" "$device_name" "$role" "$ip" "$metrics_port"; then
        successful_deployments=$((successful_deployments + 1))
    else
        failed_deployments=$((failed_deployments + 1))
    fi
    
    echo ""
done

echo "📊 Deployment Summary:"
echo "===================="
echo "✅ Successful: $successful_deployments"
echo "❌ Failed: $failed_deployments"
echo "📈 Total: $((successful_deployments + failed_deployments))"

if [ $failed_deployments -eq 0 ]; then
    echo ""
    echo "🎉 All agents deployed successfully!"
    echo ""
    echo "📊 Monitor metrics at:"
    echo "   • Prometheus: http://localhost:9090"
    echo "   • Grafana: http://localhost:3000"
    echo ""
    echo "🔍 Check agent status:"
    echo "   docker exec <container-name> pgrep -f enhanced_selfheal_agent"
    echo ""
    echo "📜 View agent logs:"
    echo "   docker logs <container-name> 2>&1 | grep SelfHeal"
else
    echo ""
    echo "⚠️  Some deployments failed. Check individual container logs."
fi
