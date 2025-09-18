#!/bin/bash

echo "🤖 Deploying ASNA Agents to Network Devices..."

# Deploy to core layer
echo "Deploying to Core Layer..."
docker cp asna-agents/asna_agent.py clab-enterprise-final-core-router:/usr/local/bin/
docker exec -d -e DEVICE_NAME=core-router -e DEVICE_IP=172.20.20.8 -e DEVICE_ROLE=core -e AGENT_TYPE=brute_force \
    clab-enterprise-final-core-router python3 /usr/local/bin/asna_agent.py

docker cp asna-agents/asna_agent.py clab-enterprise-final-core-firewall:/usr/local/bin/
docker exec -d -e DEVICE_NAME=core-firewall -e DEVICE_IP=172.20.20.11 -e DEVICE_ROLE=core -e AGENT_TYPE=tiny_llm \
    clab-enterprise-final-core-firewall python3 /usr/local/bin/asna_agent.py

# Deploy to distribution layer
echo "Deploying to Distribution Layer..."
docker cp asna-agents/asna_agent.py clab-enterprise-final-dist-eng:/usr/local/bin/
docker exec -d -e DEVICE_NAME=dist-eng -e DEVICE_IP=172.20.20.3 -e DEVICE_ROLE=distribution -e AGENT_TYPE=rl \
    clab-enterprise-final-dist-eng python3 /usr/local/bin/asna_agent.py

docker cp asna-agents/asna_agent.py clab-enterprise-final-dist-sales:/usr/local/bin/
docker exec -d -e DEVICE_NAME=dist-sales -e DEVICE_IP=172.20.20.12 -e DEVICE_ROLE=distribution -e AGENT_TYPE=fl \
    clab-enterprise-final-dist-sales python3 /usr/local/bin/asna_agent.py

# Deploy to access layer
echo "Deploying to Access Layer..."
docker cp asna-agents/asna_agent.py clab-enterprise-final-access-eng:/usr/local/bin/
docker exec -d -e DEVICE_NAME=access-eng -e DEVICE_IP=172.20.20.2 -e DEVICE_ROLE=access -e AGENT_TYPE=brute_force \
    clab-enterprise-final-access-eng python3 /usr/local/bin/asna_agent.py

docker cp asna-agents/asna_agent.py clab-enterprise-final-access-sales:/usr/local/bin/
docker exec -d -e DEVICE_NAME=access-sales -e DEVICE_IP=172.20.20.7 -e DEVICE_ROLE=access -e AGENT_TYPE=rl \
    clab-enterprise-final-access-sales python3 /usr/local/bin/asna_agent.py

echo "✅ ASNA Agents deployed successfully!"
echo ""
echo "🔍 Check agent logs with:"
echo "docker logs clab-enterprise-final-<device-name>"
echo ""
echo "📊 Monitor performance at:"
echo "http://10.10.51.140:3000"
