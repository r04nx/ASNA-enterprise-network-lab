#!/bin/bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

header() {
    echo -e "\n${PURPLE}========================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}========================================${NC}\n"
}

# Check if running as root for containerlab commands
check_sudo() {
    if ! sudo -n true 2>/dev/null; then
        warning "This script requires sudo access for containerlab commands"
        echo "Please enter your password when prompted"
    fi
}

# Check prerequisites
check_prerequisites() {
    header "🔍 Checking Prerequisites"
    
    local missing_deps=0
    
    # Check Docker
    if command -v docker &> /dev/null; then
        success "Docker found: $(docker --version | cut -d' ' -f3 | cut -d',' -f1)"
    else
        error "Docker not found. Please install Docker first."
        ((missing_deps++))
    fi
    
    # Check Docker Compose
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        success "Docker Compose found"
    else
        error "Docker Compose not found. Please install Docker Compose first."
        ((missing_deps++))
    fi
    
    # Check Containerlab
    if command -v containerlab &> /dev/null; then
        success "Containerlab found: $(containerlab version | grep version | cut -d' ' -f2)"
    else
        error "Containerlab not found. Please install containerlab first."
        echo "Installation: bash -c \"\$(curl -sL https://get.containerlab.dev)\""
        ((missing_deps++))
    fi
    
    # Check jq
    if command -v jq &> /dev/null; then
        success "jq found"
    else
        warning "jq not found. Installing jq..."
        sudo apt-get update && sudo apt-get install -y jq
    fi
    
    # Check curl
    if command -v curl &> /dev/null; then
        success "curl found"
    else
        error "curl not found. Please install curl first."
        ((missing_deps++))
    fi
    
    if [ $missing_deps -gt 0 ]; then
        error "Please install missing dependencies before continuing."
        exit 1
    fi
    
    success "All prerequisites satisfied!"
}

# Clean up existing deployment
cleanup_existing() {
    header "🧹 Cleaning Up Existing Deployment"
    
    # Stop containerlab topologies
    log "Stopping existing containerlab topologies..."
    sudo containerlab destroy --all &>/dev/null || true
    
    # Stop monitoring containers
    log "Stopping monitoring containers..."
    docker stop asna-prometheus asna-grafana asna-cadvisor asna-node-exporter 2>/dev/null || true
    docker rm asna-prometheus asna-grafana asna-cadvisor asna-node-exporter 2>/dev/null || true
    
    success "Cleanup completed"
}

# Deploy enterprise network topology
deploy_network() {
    header "🌐 Deploying Enterprise Network Topology"
    
    if [ ! -f "topologies/enterprise-final.yml" ]; then
        error "Enterprise topology file not found: topologies/enterprise-final.yml"
        exit 1
    fi
    
    log "Deploying enterprise network..."
    sudo containerlab deploy -t topologies/enterprise-final.yml
    
    # Wait for all containers to be fully up
    log "Waiting for network to stabilize..."
    sleep 10
    
    # Verify deployment
    local container_count=$(docker ps --format "{{.Names}}" | grep clab-enterprise-final | wc -l)
    success "Enterprise network deployed with $container_count devices"
}

# Deploy monitoring stack
deploy_monitoring() {
    header "📊 Deploying Monitoring Stack"
    
    # Ensure network exists
    if ! docker network ls | grep -q "^[a-f0-9].*clab"; then
        error "Containerlab network not found. Make sure enterprise network is deployed first."
        exit 1
    fi
    
    log "Starting Prometheus..."
    docker run -d \
        --name asna-prometheus \
        --network clab \
        -p 9090:9090 \
        -v $(pwd)/monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml \
        -v prometheus_data:/prometheus \
        prom/prometheus:latest \
        --config.file=/etc/prometheus/prometheus.yml \
        --storage.tsdb.path=/prometheus \
        --web.console.libraries=/etc/prometheus/console_libraries \
        --web.console.templates=/etc/prometheus/consoles \
        --storage.tsdb.retention.time=200h \
        --web.enable-lifecycle
    
    log "Starting Grafana..."
    docker run -d \
        --name asna-grafana \
        --network clab \
        -p 3000:3000 \
        -v grafana_data:/var/lib/grafana \
        -v $(pwd)/monitoring/grafana/grafana-provisioning:/etc/grafana/provisioning \
        -e GF_SECURITY_ADMIN_PASSWORD=asna123 \
        -e GF_USERS_ALLOW_SIGN_UP=false \
        grafana/grafana:latest
    
    log "Starting cAdvisor..."
    docker run -d \
        --name asna-cadvisor \
        --network clab \
        -p 8081:8080 \
        -v /:/rootfs:ro \
        -v /var/run:/var/run:ro \
        -v /sys:/sys:ro \
        -v /var/lib/docker:/var/lib/docker:ro \
        -v /dev/disk:/dev/disk:ro \
        --privileged \
        gcr.io/cadvisor/cadvisor:latest
    
    log "Starting Node Exporter (host)..."
    docker run -d \
        --name asna-node-exporter \
        --network clab \
        -p 9100:9100 \
        -v /proc:/host/proc:ro \
        -v /sys:/host/sys:ro \
        -v /:/rootfs:ro \
        prom/node-exporter:latest \
        --path.procfs=/host/proc \
        --path.rootfs=/rootfs \
        --path.sysfs=/host/sys \
        --collector.filesystem.mount-points-exclude='^/(sys|proc|dev|host|etc)($|/)'
    
    log "Waiting for monitoring stack to initialize..."
    sleep 15
    
    success "Monitoring stack deployed"
}

# Install node exporters on network devices
install_node_exporters() {
    header "🤖 Installing Node Exporters on Network Devices"
    
    local containers=$(docker ps --format "{{.Names}}" | grep clab-enterprise-final)
    local total_containers=$(echo "$containers" | wc -l)
    local installed=0
    
    log "Installing node exporters on $total_containers network devices..."
    
    for container in $containers; do
        log "Installing on $container..."
        
        # Install node exporter and start it in detached mode
        docker exec $container sh -c "
            apk add --no-cache prometheus-node-exporter 2>/dev/null || true
        " &>/dev/null || true
        
        # Start node exporter in detached mode
        docker exec -d $container node_exporter --web.listen-address=0.0.0.0:9100
        ((installed++))
        
        # Small delay to prevent overwhelming the system
        sleep 0.5
    done
    
    log "Waiting for node exporters to start..."
    sleep 10
    
    # Verify installations
    local working=0
    log "Verifying node exporter installations..."
    for container in $containers; do
        local ip=$(docker inspect $container | jq -r '.[0].NetworkSettings.Networks[].IPAddress')
        if timeout 3 curl -s http://$ip:9100/metrics > /dev/null; then
            ((working++))
        fi
    done
    
    success "Node exporters installed: $working/$total_containers responding"
    
    if [ $working -lt $total_containers ]; then
        warning "Some node exporters may need more time to start"
    fi
}

# Wait for all services to be ready
wait_for_services() {
    header "⏳ Waiting for Services to be Ready"
    
    local max_attempts=30
    local attempt=0
    
    # Wait for Prometheus
    log "Waiting for Prometheus to be ready..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:9090/-/ready &>/dev/null; then
            success "Prometheus is ready"
            break
        fi
        ((attempt++))
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        warning "Prometheus may not be fully ready yet"
    fi
    
    # Wait for Grafana
    attempt=0
    log "Waiting for Grafana to be ready..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:3000/api/health | jq -e '.database == "ok"' &>/dev/null; then
            success "Grafana is ready"
            break
        fi
        ((attempt++))
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        warning "Grafana may not be fully ready yet"
    fi
    
    # Wait for targets to be discovered
    log "Waiting for Prometheus target discovery..."
    sleep 10
    
    # Reload Prometheus config to ensure all targets are discovered
    curl -X POST http://localhost:9090/-/reload &>/dev/null || true
    sleep 5
}

# Verify deployment
verify_deployment() {
    header "✅ Verifying Deployment"
    
    # Check enterprise network
    local network_devices=$(docker ps --format "{{.Names}}" | grep clab-enterprise-final | wc -l)
    log "Enterprise network devices: $network_devices"
    
    # Check monitoring containers
    local prometheus_status="DOWN"
    local grafana_status="DOWN"
    local cadvisor_status="DOWN"
    local node_exporter_status="DOWN"
    
    if curl -s http://localhost:9090/-/healthy &>/dev/null; then
        prometheus_status="UP"
    fi
    
    if curl -s http://localhost:3000/api/health | jq -e '.database == "ok"' &>/dev/null; then
        grafana_status="UP"
    fi
    
    if curl -s http://localhost:8081/healthz &>/dev/null; then
        cadvisor_status="UP"
    fi
    
    if curl -s http://localhost:9100/metrics &>/dev/null; then
        node_exporter_status="UP"
    fi
    
    # Check Prometheus targets
    local targets_up=0
    if [ "$prometheus_status" = "UP" ]; then
        targets_up=$(curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health=="up")' | jq -s length 2>/dev/null || echo 0)
    fi
    
    # Display results
    echo ""
    echo "📊 Deployment Status:"
    echo "   Enterprise Network: $network_devices devices"
    echo "   Prometheus:         $prometheus_status"
    echo "   Grafana:           $grafana_status"
    echo "   cAdvisor:          $cadvisor_status"
    echo "   Node Exporter:     $node_exporter_status"
    echo "   Prometheus Targets: $targets_up UP"
    echo ""
    
    if [ "$prometheus_status" = "UP" ] && [ "$grafana_status" = "UP" ] && [ $targets_up -gt 0 ]; then
        success "Deployment verification successful!"
        return 0
    else
        warning "Some components may need more time to start up"
        return 1
    fi
}

# Display access information
show_access_info() {
    header "🌐 Access Information"
    
    echo "Your Enterprise Network Monitoring Lab is ready!"
    echo ""
    echo "🎯 Access URLs:"
    echo "   • Grafana Dashboard: http://localhost:3000"
    echo "     └─ Username: admin"
    echo "     └─ Password: asna123"
    echo ""
    echo "   • Prometheus:        http://localhost:9090"
    echo "   • cAdvisor:          http://localhost:8081"
    echo "   • Node Exporter:     http://localhost:9100"
    echo ""
    echo "📊 Available Grafana Dashboards:"
    echo "   • 🚀 ASNA - Enterprise Network Monitor"
    echo "   • 🏗️ ASNA - Network Topology Overview"  
    echo "   • ⏱️ ASNA - MTTR & Recovery Analytics"
    echo "   • ASNA - Agent Performance Metrics"
    echo "   • ASNA - Individual Device Details"
    echo ""
    echo "🔧 Management Commands:"
    echo "   • List running labs:     sudo containerlab inspect --all"
    echo "   • Stop enterprise lab:   sudo containerlab destroy -t topologies/enterprise-final.yml"
    echo "   • Stop monitoring:       docker stop asna-prometheus asna-grafana asna-cadvisor asna-node-exporter"
    echo "   • View container logs:   docker logs <container-name>"
    echo ""
    echo "📚 Documentation:"
    echo "   • README.md - Complete project documentation"
    echo "   • CONTRIBUTING.md - Development guidelines"
    echo ""
    success "Setup completed successfully! 🎉"
}

# Main setup function
main() {
    header "🚀 Enterprise Network Monitoring Lab Setup"
    echo "This script will deploy a complete containerlab enterprise network"
    echo "with Prometheus, Grafana, and comprehensive monitoring."
    echo ""
    
    # Confirm with user
    read -p "Do you want to proceed? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
    
    # Run setup steps
    check_sudo
    check_prerequisites
    cleanup_existing
    deploy_network
    deploy_monitoring  
    install_node_exporters
    wait_for_services
    
    if verify_deployment; then
        show_access_info
    else
        warning "Setup completed but some services may need more time to fully initialize."
        echo "You can check the status later by running:"
        echo "  curl http://localhost:9090/-/healthy"
        echo "  curl http://localhost:3000/api/health"
        show_access_info
    fi
}

# Handle script interruption
trap 'echo -e "\n${RED}Script interrupted. You may need to clean up manually.${NC}"; exit 130' INT

# Run main function
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
