# Contributing to Enterprise Network Simulation Lab

Thank you for your interest in contributing to this project! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues

1. **Check existing issues** first to avoid duplicates
2. **Use the issue template** if available
3. **Provide detailed information** including:
   - Operating system and version
   - Docker and containerlab versions
   - Steps to reproduce the issue
   - Expected vs actual behavior
   - Relevant logs or screenshots

### Submitting Changes

1. **Fork the repository**
2. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** following the coding standards
4. **Test thoroughly** with existing topologies
5. **Commit with clear messages**:
   ```bash
   git commit -m "feat: add new monitoring dashboard"
   ```
6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Create a Pull Request**

## 📋 Development Setup

### Prerequisites

```bash
# Install dependencies
sudo apt-get update
sudo apt-get install docker.io docker-compose
pip install ansible containerlab

# Install containerlab
bash -c "$(curl -sL https://get.containerlab.dev)"
```

### Local Development

```bash
# Clone your fork
git clone https://github.com/your-username/enterprise-network-lab.git
cd enterprise-network-lab

# Test with a simple topology
sudo containerlab deploy -t topologies/enterprise-testbed.yml

# Clean up after testing
sudo containerlab destroy -t topologies/enterprise-testbed.yml
```

## 🧪 Testing Guidelines

### Before Submitting

1. **Test all modified topologies**:
   ```bash
   sudo containerlab deploy -t topologies/your-modified-topology.yml
   ```

2. **Verify monitoring integration**:
   ```bash
   curl http://localhost:3000  # Grafana
   curl http://localhost:9090  # Prometheus
   ```

3. **Test Ansible integration**:
   ```bash
   cd ansible/
   ansible-playbook -i inventory.yml --check your-playbook.yml
   ```

4. **Check scripts functionality**:
   ```bash
   chmod +x scripts/your-script.sh
   ./scripts/your-script.sh --dry-run
   ```

### Testing Checklist

- [ ] Topology deploys successfully
- [ ] All containers start properly
- [ ] Network connectivity works
- [ ] Monitoring agents deploy correctly
- [ ] Grafana dashboards load
- [ ] Ansible playbooks execute
- [ ] Scripts run without errors
- [ ] Documentation is updated

## 📝 Coding Standards

### Containerlab Topologies

```yaml
# Use consistent naming
name: descriptive-topology-name

topology:
  nodes:
    # Use descriptive node names
    core-router-01:
      kind: linux
      image: alpine:latest
      # Group related exec commands
      exec:
        - sysctl -w net.ipv4.ip_forward=1
        - apk add --no-cache iptables
        
  links:
    # Use clear endpoint descriptions
    - endpoints: ["core-router-01:eth0", "dist-switch-01:eth1"]
```

### Shell Scripts

```bash
#!/bin/bash
set -euo pipefail  # Fail fast and handle errors

# Use clear function names
deploy_agents() {
    local topology_name="$1"
    echo "🤖 Deploying agents to ${topology_name}..."
    
    # Handle errors gracefully
    if ! docker ps | grep -q "${topology_name}"; then
        echo "❌ Topology ${topology_name} not running"
        return 1
    fi
}

# Use main function
main() {
    deploy_agents "$@"
}

# Call main if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### Ansible

```yaml
---
- name: Configure network device
  hosts: network_devices
  gather_facts: false
  
  tasks:
    - name: Install required packages
      apk:
        name:
          - iptables
          - quagga
        state: present
      become: true
      
    - name: Enable IP forwarding
      sysctl:
        name: net.ipv4.ip_forward
        value: '1'
        state: present
      become: true
```

### Python (ASNA Agents)

```python
#!/usr/bin/env python3
"""ASNA Agent for network monitoring and analysis."""

import logging
import os
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ASNAAgent:
    """Main ASNA Agent class."""
    
    def __init__(self, device_name: str, device_ip: str) -> None:
        self.device_name = device_name
        self.device_ip = device_ip
        logger.info(f"Initializing ASNA Agent for {device_name}")
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect device metrics."""
        # Implementation here
        pass

if __name__ == "__main__":
    agent = ASNAAgent(
        device_name=os.getenv('DEVICE_NAME', 'unknown'),
        device_ip=os.getenv('DEVICE_IP', '127.0.0.1')
    )
    agent.run()
```

## 📚 Documentation

### Update Documentation

When making changes, please update:

- **README.md**: For new features or usage changes
- **Topology comments**: Inline documentation in YAML files
- **Script comments**: Function and usage documentation
- **This CONTRIBUTING.md**: For process changes

### Documentation Style

- Use **clear, concise language**
- Include **code examples** where helpful
- Use **emoji sparingly** but consistently
- Follow **Markdown best practices**
- Test all **command examples**

## 🏷️ Commit Message Format

Use conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Test additions or modifications
- `chore`: Maintenance tasks

### Examples
```bash
git commit -m "feat(topology): add DMZ network segment"
git commit -m "fix(monitoring): resolve Prometheus target discovery"
git commit -m "docs(readme): update quick start guide"
```

## 🐛 Debugging

### Common Issues

1. **Containerlab Permission Issues**:
   ```bash
   sudo chown -R $USER:$USER /etc/containerlab
   ```

2. **Docker Socket Issues**:
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```

3. **Port Conflicts**:
   ```bash
   sudo netstat -tulpn | grep :3000  # Check for conflicts
   ```

### Debug Commands

```bash
# Check containerlab status
sudo containerlab inspect --all

# Debug specific container
docker exec -it clab-topology-node-name /bin/sh

# Check logs
docker logs clab-topology-node-name

# Monitor resources
docker stats
```

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check README.md and inline comments

## 📜 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the technical aspects
- Help others learn and contribute

Thank you for contributing! 🎉
