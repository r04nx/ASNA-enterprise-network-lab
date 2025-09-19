# Enterprise Network Simulation Lab

A comprehensive containerlab-based enterprise network simulation environment with integrated monitoring, automation, and network analysis capabilities using Prometheus, Grafana, and custom ASNA (Automated Security and Network Analysis) agents.

## 🚀 Quick Start

### One-Command Setup

```bash
# Deploy the complete lab with monitoring
./setup.sh
```

This will automatically:
- Deploy 15-device enterprise network topology
- Set up Prometheus + Grafana monitoring stack
- Install node exporters on all network devices
- Configure dashboards with real-time metrics
- Verify end-to-end monitoring pipeline

### Prerequisites

- Docker & Docker Compose
- Containerlab (`bash -c "$(curl -sL https://get.containerlab.dev)"`)
- sudo access
- 8GB+ RAM recommended

## 🏗️ Architecture

This project simulates a multi-tier enterprise network architecture including:

- **Core Layer**: Enterprise routers, firewalls, and core services
- **Distribution Layer**: Distribution switches and services
- **Access Layer**: Access switches and endpoint devices
- **DMZ**: Web servers and external-facing services
- **Monitoring Stack**: Prometheus + Grafana + Node Exporters + cAdvisor
- **Automation**: Ansible playbooks and custom ASNA agents

## 📁 Project Structure

```
.
├── setup.sh                   # 🚀 One-command deployment script
├── cleanup.sh                 # 🧹 Complete lab teardown script  
├── status.sh                  # 📊 Status checker script
├── ansible/                   # Ansible configuration and playbooks
│   ├── ansible.cfg            # Ansible configuration
│   ├── inventory.yml          # Ansible inventory
│   └── asna-agents/           # Custom ASNA agent code
├── docs/                      # Documentation
├── labs/                      # Generated lab data (clab-*)
├── monitoring/                # Monitoring configuration
│   ├── grafana/               # Grafana dashboards and provisioning
│   └── prometheus/            # Prometheus configuration
├── scripts/                   # Deployment and automation scripts
└── topologies/                # Containerlab topology definitions
```

## 📊 Available Topologies

| Topology | Description | Use Case |
|----------|-------------|----------|
| `enterprise-final.yml` | Complete 15-device enterprise network | Production simulation |
| `enterprise-comprehensive.yml` | Extended enterprise with additional services | Advanced testing |
| `enterprise-network.yml` | Core network components | Network testing |
| `enterprise-testbed.yml` | Minimal test environment | Development |
| `monitoring-stack.yml` | Prometheus + Grafana | Monitoring only |

## 🛠️ Management Commands

### Quick Operations

```bash
# Deploy complete lab
./setup.sh

# Check lab status  
./status.sh

# Clean up everything
./cleanup.sh
```

### Manual Operations

```bash
# Deploy specific topology
sudo containerlab deploy -t topologies/enterprise-final.yml

# List running labs
sudo containerlab inspect --all

# Stop specific lab
sudo containerlab destroy -t topologies/enterprise-final.yml

# Install node exporters manually
./scripts/install_node_exporters.sh

# Deploy ASNA agents
./scripts/deploy-asna-agents.sh
```

## 📈 Monitoring & Dashboards

### Access URLs
- **Grafana**: http://localhost:3000 (admin/asna123)
- **Prometheus**: http://localhost:9090
- **cAdvisor**: http://localhost:8081
- **Node Exporter**: http://localhost:9100

### Available Dashboards
- 🚀 **ASNA - Enterprise Network Monitor** - Main overview dashboard
- 🏗️ **ASNA - Network Topology Overview** - Network topology visualization
- ⏱️ **ASNA - MTTR & Recovery Analytics** - Recovery time analysis
- 📊 **ASNA - Agent Performance Metrics** - Agent performance monitoring
- 🔍 **ASNA - Individual Device Details** - Per-device detailed metrics

## 🤖 ASNA Agents

Custom network analysis agents that provide:

- **Device Monitoring**: Real-time device status and metrics
- **Network Topology**: Dynamic topology discovery
- **MTTR Tracking**: Mean Time To Recovery analysis
- **Security Analysis**: Automated security assessment

### Agent Types
- `brute_force`: Comprehensive device analysis
- `lightweight`: Basic monitoring
- `security_focused`: Security-specific analysis

## 🔧 Configuration

### Monitoring Configuration
- **Prometheus Config**: `monitoring/prometheus/prometheus.yml`
- **Grafana Dashboards**: `monitoring/grafana/grafana-provisioning/dashboards/`
- **Data Sources**: `monitoring/grafana/grafana-provisioning/datasources/`

### Network Configuration
- **Main Topology**: `topologies/enterprise-final.yml`
- **Ansible Inventory**: `ansible/inventory.yml`
- **Device Scripts**: `scripts/`

## 🧪 Testing & Verification

### Automated Verification
The setup script includes comprehensive verification:
- Network connectivity between devices
- Metric collection from all devices
- Prometheus target discovery
- Grafana dashboard functionality
- Real-time data flow

### Manual Testing
```bash
# Test network connectivity
docker exec clab-enterprise-final-core-router ping 172.20.20.14

# Check node exporter metrics
curl http://172.20.20.7:9100/metrics

# Verify Prometheus targets
curl http://localhost:9090/api/v1/targets

# Test Grafana API
curl http://localhost:3000/api/health
```

## 📚 Advanced Usage

### Custom Topologies

Create new topologies by copying and modifying existing ones:

```yaml
name: my-custom-topology
topology:
  nodes:
    my-router:
      kind: linux
      image: alpine:latest
      exec:
        - sysctl -w net.ipv4.ip_forward=1
  links:
    - endpoints: ["my-router:eth0", "another-device:eth1"]
```

### Ansible Automation

Run Ansible playbooks against the lab:

```bash
cd ansible/
ansible-playbook -i inventory.yml my-playbook.yml
```

### Traffic Generation

```bash
# Generate network traffic for testing
sudo containerlab deploy -t topologies/network-traffic-generator.yml
```

## 🐛 Troubleshooting

### Common Issues

1. **Permission Denied**: Run containerlab commands with `sudo`
2. **Port Conflicts**: Check for conflicting services on monitoring ports
3. **Node Exporters Not Starting**: Use `./status.sh` to check status
4. **Grafana No Data**: Verify Prometheus data source connectivity

### Diagnostic Commands

```bash
# Check overall status
./status.sh

# Check containerlab status
sudo containerlab inspect --all

# Check Docker containers
docker ps | grep -E "(asna|clab)"

# Check logs
docker logs asna-prometheus
docker logs asna-grafana

# Test connectivity
curl http://localhost:9090/-/healthy
curl http://localhost:3000/api/health
```

### Reset Everything

```bash
# Complete cleanup and restart
./cleanup.sh
./setup.sh
```

## 🚀 What's Included

After running `./setup.sh`, you'll have:

✅ **15-device enterprise network** (routers, switches, servers, workstations)
✅ **Complete monitoring stack** (Prometheus + Grafana + cAdvisor + Node Exporters)  
✅ **Real-time metrics collection** from all network devices
✅ **7 pre-configured Grafana dashboards** with live data
✅ **Network connectivity** between all devices
✅ **Automated health checking** and verification
✅ **Easy management scripts** for start/stop/status

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test with `./setup.sh`
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

See `CONTRIBUTING.md` for detailed guidelines.

## 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## 🙏 Acknowledgments

- [Containerlab](https://containerlab.dev/) - Excellent network simulation platform
- [Prometheus](https://prometheus.io/) - Monitoring and alerting toolkit
- [Grafana](https://grafana.com/) - Analytics and interactive visualization platform
- [cAdvisor](https://github.com/google/cadvisor) - Container monitoring
- [Node Exporter](https://github.com/prometheus/node_exporter) - Hardware and OS metrics

---

## 🎯 Quick Reference

| Command | Purpose |
|---------|---------|
| `./setup.sh` | Deploy complete lab |
| `./status.sh` | Check lab status |
| `./cleanup.sh` | Remove everything |
| `sudo containerlab inspect --all` | Show all running labs |
| `docker ps \| grep asna` | Show monitoring containers |

**Access Grafana**: http://localhost:3000 (admin/asna123)
**Access Prometheus**: http://localhost:9090

---

**🎉 Ready to explore enterprise network monitoring? Run `./setup.sh` to get started!**
