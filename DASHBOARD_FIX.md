# Critical Fix Applied
Fixed Grafana dashboards to display all 15 network devices by changing job name from 'node-exporter' to 'network-devices'

Changes made:
- Updated all dashboard JSON files to use job='network-devices' instead of job='node-exporter'
- This allows Grafana to properly query metrics from all 15 containerlab network devices
- Restarted Grafana container to reload dashboard configurations
