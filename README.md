# Enterprise Network Simulation Lab

A comprehensive containerlab-based enterprise network simulation environment with integrated monitoring, automation, and network analysis capabilities using Prometheus, Grafana, and custom ASNA (Automated Security and Network Analysis) agents.

## 🏗️ Architecture

This project simulates a multi-tier enterprise network architecture including:

- **Core Layer**: Enterprise routers, firewalls, and core services
- **Distribution Layer**: Distribution switches and services
- **Access Layer**: Access switches and endpoint devices
- **DMZ**: Web servers and external-facing services
- **Monitoring Stack**: Prometheus + Grafana + Node Exporters
- **Automation**: Ansible playbooks and custom ASNA agents

## 📁 Project Structure

```
.
├── ansible/                    # Ansible configuration and playbooks
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

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Containerlab (`containerlab install`)
- Ansible (`pip install ansible`)
- Python 3.x

### 1. Deploy the Network

Choose from available topologies:

```bash
# Deploy the main enterprise topology
sudo containerlab deploy -t topologies/enterprise-final.yml

# Or deploy the comprehensive version
sudo containerlab deploy -t topologies/enterprise-comprehensive.yml
```

### 2. Start Monitoring Stack

```bash
# Deploy Prometheus and Grafana
sudo containerlab deploy -t topologies/monitoring-stack.yml
```

### 3. Deploy ASNA Agents

```bash
# Install and deploy network monitoring agents
chmod +x scripts/deploy-asna-agents.sh
./scripts/deploy-asna-agents.sh
```

### 4. Install Node Exporters

```bash
# Deploy Prometheus node exporters to all devices
chmod +x scripts/install_node_exporters.sh
./scripts/install_node_exporters.sh
```

## 📊 Available Topologies

| Topology | Description | Use Case |
|----------|-------------|----------|
| `enterprise-final.yml` | Complete enterprise network | Production simulation |
| `enterprise-comprehensive.yml` | Extended enterprise with additional services | Advanced testing |
| `enterprise-network.yml` | Core network components | Network testing |
| `enterprise-testbed.yml` | Minimal test environment | Development |
| `monitoring-stack.yml` | Prometheus + Grafana | Monitoring only |

## 🔧 Configuration

### Ansible Configuration

The project uses Ansible for automation and configuration management:

- **Config**: `ansible/ansible.cfg`
- **Inventory**: `ansible/inventory.yml`
- **Agents**: Custom ASNA agents in `ansible/asna-agents/`

### Monitoring

#### Prometheus
- Configuration: `monitoring/prometheus/prometheus.yml`
- Targets: Auto-discovered from containerlab inventory
- Metrics: Node metrics, custom ASNA metrics

#### Grafana
- Dashboards: Pre-configured enterprise network dashboards
- Data Sources: Prometheus integration
- Location: `monitoring/grafana/grafana-provisioning/`

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

## 📈 Monitoring & Dashboards

Access the monitoring stack:

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

### Available Dashboards
- ASNA Agent Metrics
- ASNA Comprehensive Dashboard
- ASNA Device Details
- ASNA MTTR Tracking
- ASNA Network Topology

## 🛠️ Management Commands

### Lab Management

```bash
# List running labs
sudo containerlab inspect --all

# Stop a specific lab
sudo containerlab destroy -t topologies/enterprise-final.yml

# Stop all labs
sudo containerlab destroy --all
```

### Monitoring

```bash
# Check ASNA agent status
docker exec -it clab-enterprise-final-core-router ps aux | grep asna_agent

# View agent logs
docker exec -it clab-enterprise-final-core-router tail -f /var/log/asna_agent.log
```

### Traffic Generation

```bash
# Generate network traffic for testing
sudo containerlab deploy -t topologies/network-traffic-generator.yml
```

## 🧪 Testing

Run quick network tests:

```bash
# Deploy quick test topology
sudo containerlab deploy -t topologies/quick-traffic-test.yml

# Test connectivity
docker exec -it clab-enterprise-final-core-router ping 172.20.20.9
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

## 🐛 Troubleshooting

### Common Issues

1. **Permission Denied**: Run containerlab commands with `sudo`
2. **Port Conflicts**: Check for conflicting services on monitoring ports
3. **Agent Failures**: Check Docker logs and container status
4. **Network Issues**: Verify containerlab network creation

### Logs

```bash
# Containerlab logs
sudo containerlab logs -t topologies/enterprise-final.yml

# Docker container logs
docker logs clab-enterprise-final-core-router

# ASNA agent logs
docker exec clab-enterprise-final-core-router tail -f /var/log/asna_agent.log
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with the provided topologies
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Containerlab community for the excellent network simulation platform
- Prometheus and Grafana teams for monitoring tools
- Ansible community for automation capabilities
