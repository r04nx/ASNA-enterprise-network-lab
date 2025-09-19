#!/bin/bash
set -euo pipefail

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

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

main() {
    header "🧹 Enterprise Network Monitoring Lab Cleanup"
    echo "This script will completely remove the enterprise network lab"
    echo "including all containers, volumes, and networks."
    echo ""
    warning "This action cannot be undone!"
    echo ""
    
    read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cleanup cancelled."
        exit 0
    fi
    
    # Stop and destroy containerlab topologies
    log "Stopping containerlab topologies..."
    sudo containerlab destroy --all 2>/dev/null || true
    success "Containerlab topologies stopped"
    
    # Stop and remove monitoring containers
    log "Stopping monitoring containers..."
    docker stop asna-prometheus asna-grafana asna-cadvisor asna-node-exporter 2>/dev/null || true
    docker rm asna-prometheus asna-grafana asna-cadvisor asna-node-exporter 2>/dev/null || true
    success "Monitoring containers removed"
    
    # Remove volumes (optional)
    read -p "Do you want to remove persistent data volumes? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Removing data volumes..."
        docker volume rm prometheus_data grafana_data containerlab_grafana_data topologies_prometheus_data topologies_grafana_data 2>/dev/null || true
        success "Data volumes removed"
    else
        warning "Data volumes preserved"
    fi
    
    # Clean up unused Docker resources
    log "Cleaning up unused Docker resources..."
    docker system prune -f >/dev/null 2>&1 || true
    
    success "Cleanup completed successfully! 🎉"
    echo ""
    echo "To redeploy the lab, run: ./setup.sh"
}

# Handle script interruption
trap 'echo -e "\n${RED}Cleanup interrupted.${NC}"; exit 130' INT

# Run main function
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
