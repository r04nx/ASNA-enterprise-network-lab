#!/bin/bash
set -euo pipefail

# AI-Enhanced Self-Healing Agents Deployment Script
# Deploys AI agents with Reinforcement Learning capabilities across network topology

echo "🤖 Deploying AI-Enhanced Self-Healing Agents"
echo "=============================================="

AGENT_FILE="scripts/agent/ai_enhanced_selfheal_agent.py"
AGENT_TARGET="/usr/local/bin/ai_enhanced_selfheal_agent.py"
WEB_SERVER_IP="172.20.20.7"

# Function to deploy AI agent to a container
deploy_ai_agent() {
    local container=$1
    local device_name=$2
    local device_role=$3
    local device_ip=$4
    local metrics_port=$5
    
    echo "🚀 Deploying AI agent to $device_name ($container)..."
    
    # Install Python dependencies
    docker exec "$container" apt-get update >/dev/null 2>&1 || true
    docker exec "$container" apt-get install -y python3-numpy >/dev/null 2>&1 || echo "   Warning: Could not install numpy"
    
    # Copy agent file
    docker cp "$AGENT_FILE" "$container:$AGENT_TARGET" || {
        echo "   ❌ Failed to copy AI agent to $container"
        return 1
    }
    
    # Make executable
    docker exec "$container" chmod +x "$AGENT_TARGET" || {
        echo "   ❌ Failed to make agent executable in $container"
        return 1
    }
    
    # Kill existing agent if running
    docker exec "$container" pkill -f "ai_enhanced_selfheal_agent\|enhanced_selfheal_agent" 2>/dev/null || true
    
    # Start AI agent with enhanced environment
    docker exec -d \
        -e DEVICE_NAME="$device_name" \
        -e DEVICE_ROLE="$device_role" \
        -e DEVICE_IP="$device_ip" \
        -e EXPECTED_SUBNET="172.20.20.0/24" \
        -e AGENT_IFACE="eth0" \
        -e AGENT_GATEWAY="172.20.20.1" \
        -e AGENT_CHECK_HOST="$WEB_SERVER_IP" \
        -e AGENT_CHECK_PORT="80" \
        -e AGENT_SLEEP="3" \
        -e AGENT_LOG_LEVEL="INFO" \
        -e METRICS_PORT="$metrics_port" \
        -e AI_LEARNING_RATE="0.15" \
        -e AI_EXPLORATION_RATE="0.3" \
        "$container" \
        python3 "$AGENT_TARGET" || {
        echo "   ❌ Failed to start AI agent in $container"
        return 1
    }
    
    # Brief wait to check if agent started
    sleep 2
    if docker exec "$container" pgrep -f "ai_enhanced_selfheal_agent" >/dev/null; then
        echo "   ✅ AI agent deployed and running on $device_name"
        return 0
    else
        echo "   ⚠️  AI agent deployed but may not be running on $device_name"
        return 1
    fi
}

# AI Agent deployment configuration
DEPLOYMENTS=(
    # Priority deployment - test device
    "clab-enterprise-final-eng-gui:eng-gui:client:172.20.20.14:9200"
    
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
    
    # Additional Client Devices
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
echo "🎯 Starting AI Agent Deployments..."
echo ""

for deployment in "${DEPLOYMENTS[@]}"; do
    IFS=':' read -r container device_name role ip metrics_port <<< "$deployment"
    
    if deploy_ai_agent "$container" "$device_name" "$role" "$ip" "$metrics_port"; then
        successful_deployments=$((successful_deployments + 1))
    else
        failed_deployments=$((failed_deployments + 1))
    fi
    
    echo ""
done

echo "📊 AI Agent Deployment Summary:"
echo "==============================="
echo "✅ Successful: $successful_deployments"
echo "❌ Failed: $failed_deployments"
echo "📈 Total: $((successful_deployments + failed_deployments))"

if [ $failed_deployments -eq 0 ]; then
    echo ""
    echo "🎉 All AI agents deployed successfully!"
    echo ""
    echo "🧠 AI Features Available:"
    echo "   • Reinforcement Learning decision making"
    echo "   • IP subnet validation and correction"
    echo "   • Gateway reachability testing"
    echo "   • Multi-fault compound recovery"
    echo "   • Continuous learning and adaptation"
    echo ""
    echo "📊 Monitor AI metrics at:"
    echo "   • Prometheus: http://localhost:9090"
    echo "   • Grafana: http://localhost:3000"
    echo ""
    echo "🔍 Check AI agent status:"
    echo "   docker exec <container-name> pgrep -f ai_enhanced_selfheal_agent"
    echo ""
    echo "📈 View AI agent metrics:"
    echo "   curl http://172.20.20.14:9200/metrics | grep ai_"
else
    echo ""
    echo "⚠️  Some AI agent deployments failed. Check individual container logs."
    echo "🔧 Troubleshooting tips:"
    echo "   • Ensure containers are running: docker ps"
    echo "   • Check container logs: docker logs <container-name>"
    echo "   • Verify Python3 availability in containers"
fi

echo ""
echo "🚀 AI-Enhanced Self-Healing Network is ready!"
