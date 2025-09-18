#!/bin/bash

# List of all containerlab devices
DEVICES=(
  "core-router" "core-firewall" 
  "dist-eng" "dist-sales" "dist-servers"
  "access-eng" "access-sales"
  "eng-dev" "file-server" "db-server"
)

echo "Deploying node-exporter to network devices..."

for device in "${DEVICES[@]}"; do
  echo "Setting up monitoring on $device..."
  
  # Install monitoring tools
  docker exec clab-enterprise-final-$device sh -c "
    apk add --no-cache wget curl netcat-openbsd || true
    
    # Download and install node-exporter
    wget -q https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz -O /tmp/node_exporter.tar.gz 2>/dev/null || true
    
    if [ -f /tmp/node_exporter.tar.gz ]; then
      cd /tmp && tar xzf node_exporter.tar.gz
      cp node_exporter-*/node_exporter /usr/local/bin/ 2>/dev/null || true
      chmod +x /usr/local/bin/node_exporter
      
      # Start node-exporter in background
      nohup /usr/local/bin/node_exporter --web.listen-address=:9100 > /dev/null 2>&1 &
      echo 'Node exporter started on $device'
    fi
  " 2>/dev/null &
done

wait
echo "Monitoring agents deployment completed!"
