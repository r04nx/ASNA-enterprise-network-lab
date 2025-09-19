# Dashboard Fix #2 Applied
Fixed incorrect 'Devices DOWN/Isolated' count in Grafana dashboard

Problem: Dashboard showed '15 Isolated' devices when all 15 devices are actually UP
Cause: Prometheus query 'count(up{job="network-devices"} == 0)' returns empty result when no devices are down
Fix: Added 'or vector(0)' to return 0 instead of empty result
Result: Dashboard now correctly shows 15 Operational, 0 Isolated
