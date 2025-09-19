#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

header() {
    echo -e "\n${PURPLE}========================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}========================================${NC}\n"
}

status_check() {
    local service=$1
    local url=$2
    local expected=$3
    
    if curl -s "$url" | grep -q "$expected" 2>/dev/null; then
        echo -e "   ${GREEN}✅ $service: UP${NC}"
        return 0
    else
        echo -e "   ${RED}❌ $service: DOWN${NC}"
        return 1
    fi
}

main() {
    header "📊 Enterprise Network Monitoring Lab Status"
    
    # Check containerlab network devices
    network_count=$(docker ps --filter "name=clab-enterprise-final" --format "{{.Names}}" | wc -l)
    if [ $network_count -gt 0 ]; then
        echo -e "   ${GREEN}✅ Enterprise Network: $network_count devices running${NC}"
    else
        echo -e "   ${RED}❌ Enterprise Network: No devices running${NC}"
    fi
    
    # Check monitoring services
    echo ""
    echo "🔍 Monitoring Services:"
    status_check "Prometheus" "http://localhost:9090/-/healthy" "Prometheus Server is Healthy"
    status_check "Grafana" "http://localhost:3000/api/health" '"database":"ok"'
    status_check "cAdvisor" "http://localhost:8081/healthz" "ok"
    status_check "Node Exporter" "http://localhost:9100/metrics" "node_"
    
    # Check Prometheus targets if Prometheus is up
    if curl -s http://localhost:9090/-/healthy >/dev/null 2>&1; then
        echo ""
        echo "🎯 Prometheus Targets:"
        targets_up=$(curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health=="up")' | jq -s length 2>/dev/null || echo 0)
        targets_total=$(curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length' 2>/dev/null || echo 0)
        echo "   📈 Active Targets: $targets_up/$targets_total UP"
        
        # Show targets by job
        if [ $targets_up -gt 0 ]; then
            echo ""
            echo "📋 Targets by Job:"
            curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets | group_by(.labels.job) | .[] | "   • " + .[0].labels.job + ": " + (map(select(.health=="up")) | length | tostring) + "/" + (length | tostring) + " UP"' 2>/dev/null || echo "   Unable to fetch target details"
        fi
    fi
    
    # Show access URLs
    echo ""
    echo "🌐 Access URLs:"
    echo "   • Grafana:      http://localhost:3000 (admin/asna123)"
    echo "   • Prometheus:   http://localhost:9090"
    echo "   • cAdvisor:     http://localhost:8081"
    echo "   • Node Export:  http://localhost:9100"
    
    # Show quick management commands
    echo ""
    echo "⚡ Quick Commands:"
    echo "   • Full status:    sudo containerlab inspect --all"
    echo "   • Stop lab:       ./cleanup.sh"
    echo "   • Restart setup:  ./setup.sh"
    
    echo ""
}

# Run main function
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
