#!/bin/bash
set -euo pipefail

# AI-Enhanced Self-Healing Agents Deployment Script with Complete Network Tooling
# Deploys AI agents with Reinforcement Learning capabilities across network topology
# Ensures robust environment provisioning with all essential network tools

echo "🤖 Deploying AI-Enhanced Self-Healing Agents with Full Network Tooling"
echo "======================================================================"

AGENT_FILE="scripts/agent/ai_enhanced_selfheal_agent.py"
AGENT_TARGET="/usr/local/bin/ai_enhanced_selfheal_agent.py"
WEB_SERVER_IP="172.20.20.7"

# Comprehensive list of essential networking tools
ESSENTIAL_NETWORK_PACKAGES=(
    "iputils-ping"           # ping command
    "netcat-openbsd"         # nc command  
    "net-tools"              # netstat, ifconfig, route
    "iproute2"               # ip command
    "dnsutils"               # nslookup, dig
    "traceroute"             # traceroute command
    "telnet"                 # telnet for port testing
    "wget"                   # wget for HTTP testing
    "curl"                   # curl for HTTP/API testing
    "tcpdump"                # packet capture
    "nmap"                   # network mapping and port scanning
    "iperf3"                 # network performance testing
    "mtr-tiny"               # network diagnostics
    "bridge-utils"           # bridge utilities
    "vlan"                   # VLAN utilities
    "ethtool"                # ethernet tool
    "arp-scan"               # ARP scanning
    "fping"                  # fast ping
    "hping3"                 # advanced ping
)

# Python packages for enhanced AI capabilities
PYTHON_PACKAGES=(
    "python3-numpy"
    "python3-pip"
    "python3-requests"
    "python3-psutil"
    "python3-netifaces"
    "python3-netaddr"
)

# Function to install comprehensive network tooling in container
install_network_tools() {
    local container=$1
    local device_name=$2
    
    echo "🛠️  Installing comprehensive network tools in $device_name ($container)..."
    
    # Update package repositories
    echo "   📦 Updating package repositories..."
    docker exec "$container" bash -c "apt-get update >/dev/null 2>&1 || echo 'Warning: apt update had issues'"
    
    # Install essential networking tools
    echo "   🔧 Installing essential network utilities..."
    local package_string=$(printf "%s " "${ESSENTIAL_NETWORK_PACKAGES[@]}")
    docker exec "$container" bash -c "DEBIAN_FRONTEND=noninteractive apt-get install -y $package_string >/dev/null 2>&1" || {
        echo "   ⚠️  Some network packages failed to install, trying individual installation..."
        
        # Try installing packages individually for better error handling
        for package in "${ESSENTIAL_NETWORK_PACKAGES[@]}"; do
            docker exec "$container" bash -c "DEBIAN_FRONTEND=noninteractive apt-get install -y $package >/dev/null 2>&1" || {
                echo "   ⚠️  Failed to install $package (continuing...)"
            }
        done
    }
    
    # Install Python packages
    echo "   🐍 Installing Python packages..."
    local python_packages_string=$(printf "%s " "${PYTHON_PACKAGES[@]}")
    docker exec "$container" bash -c "DEBIAN_FRONTEND=noninteractive apt-get install -y $python_packages_string >/dev/null 2>&1" || {
        echo "   ⚠️  Some Python packages failed to install (continuing...)"
    }
    
    # Install additional Python packages via pip if needed
    docker exec "$container" bash -c "pip3 install requests psutil netifaces netaddr 2>/dev/null || true"
    
    # Verify critical tools are available
    local critical_tools=("ping" "nc" "ip" "curl" "wget")
    for tool in "${critical_tools[@]}"; do
        if docker exec "$container" which "$tool" >/dev/null 2>&1; then
            echo "   ✅ $tool: Available"
        else
            echo "   ❌ $tool: NOT FOUND"
            return 1
        fi
    done
    
    echo "   ✅ Network tooling installation completed for $device_name"
    return 0
}

# Function to deploy AI agent to a container
deploy_ai_agent() {
    local container=$1
    local device_name=$2
    local device_role=$3
    local device_ip=$4
    local metrics_port=$5
    
    echo "🚀 Deploying AI agent to $device_name ($container)..."
    
    # Install comprehensive network tools first
    if ! install_network_tools "$container" "$device_name"; then
        echo "   ❌ Failed to install network tools in $container"
        return 1
    fi
    
    # Copy enhanced agent file
    docker cp "$AGENT_FILE" "$container:$AGENT_TARGET" || {
        echo "   ❌ Failed to copy AI agent to $container"
        return 1
    }
    
    # Make executable
    docker exec "$container" chmod +x "$AGENT_TARGET" || {
        echo "   ❌ Failed to make agent executable in $container"
        return 1
    }
    
    # Kill existing agents if running
    docker exec "$container" pkill -f "ai_enhanced_selfheal_agent|enhanced_selfheal_agent|selfheal_agent" 2>/dev/null || true
    sleep 1
    
    # Start AI agent with enhanced environment and network tool validation
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
        -e NETWORK_TOOLS_VALIDATED="true" \
        "$container" \
        python3 "$AGENT_TARGET" || {
        echo "   ❌ Failed to start AI agent in $container"
        return 1
    }
    
    # Verify agent started and is serving metrics
    sleep 3
    if docker exec "$container" pgrep -f "ai_enhanced_selfheal_agent" >/dev/null; then
        # Test metrics endpoint
        if docker exec "$container" curl -s --connect-timeout 2 "http://localhost:$metrics_port/metrics" >/dev/null 2>&1; then
            echo "   ✅ AI agent deployed, running, and serving metrics on $device_name"
            return 0
        else
            echo "   ⚠️  AI agent running but metrics endpoint not responding on $device_name"
            return 1
        fi
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
echo "🎯 Starting Enhanced AI Agent Deployments with Full Network Tooling..."
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

echo "📊 Enhanced AI Agent Deployment Summary:"
echo "========================================"
echo "✅ Successful: $successful_deployments"
echo "❌ Failed: $failed_deployments"
echo "📈 Total: $((successful_deployments + failed_deployments))"

if [ $failed_deployments -eq 0 ]; then
    echo ""
    echo "🎉 All AI agents deployed successfully with full network tooling!"
    echo ""
    echo "🛠️  Network Tools Installed on Each Container:"
    echo "   • ping, fping, hping3 - ICMP testing"
    echo "   • nc, telnet - Port connectivity testing" 
    echo "   • wget, curl - HTTP/HTTPS testing"
    echo "   • nmap, arp-scan - Network discovery"
    echo "   • traceroute, mtr - Path analysis"
    echo "   • tcpdump - Packet capture"
    echo "   • iperf3 - Performance testing"
    echo "   • dig, nslookup - DNS testing"
    echo "   • ip, netstat, ifconfig - Network configuration"
    echo ""
    echo "🧠 AI Features Available:"
    echo "   • Reinforcement Learning decision making"
    echo "   • IP subnet validation and correction"
    echo "   • Gateway reachability testing with multiple methods"
    echo "   • Multi-fault compound recovery"
    echo "   • Continuous learning and adaptation"
    echo "   • Robust connectivity testing with fallbacks"
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
    echo ""
    echo "🧪 Test network tools in any container:"
    echo "   docker exec <container-name> ping -c 2 172.20.20.1"
    echo "   docker exec <container-name> nc -zv 172.20.20.7 80"
    echo "   docker exec <container-name> curl -s http://172.20.20.7"
else
    echo ""
    echo "⚠️  Some AI agent deployments failed. Check individual container logs."
    echo "🔧 Troubleshooting tips:"
    echo "   • Ensure containers are running: docker ps"
    echo "   • Check container logs: docker logs <container-name>"
    echo "   • Verify network connectivity between containers"
    echo "   • Check available disk space and memory"
fi

echo ""
echo "🚀 AI-Enhanced Self-Healing Network with Full Network Tooling is ready!"
echo "🛡️  Agents are now equipped to handle complex network scenarios with confidence!"
