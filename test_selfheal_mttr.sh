#!/bin/bash

# MTTR Testing Script for Self-Healing Agent
# Tests the eng-gui container's self-healing capabilities

set -e

ANSIBLE_DIR="./ansible"
CONTAINER_NAME="clab-enterprise-final-eng-gui"
LOG_FILE="/tmp/selfheal.log"
RESULTS_FILE="mttr_results_$(date +%Y%m%d_%H%M%S).json"

echo "🧪 Starting MTTR Testing for Self-Healing Agent"
echo "Target Container: $CONTAINER_NAME"
echo "Results will be saved to: $RESULTS_FILE"
echo ""

# Function to get timestamp
get_timestamp() {
    date -u +"%Y-%m-%dT%H:%M:%S.%3NZ"
}

# Function to check if agent is healthy
check_agent_health() {
    local log_content=$(docker exec $CONTAINER_NAME cat $LOG_FILE 2>/dev/null || echo "")
    if echo "$log_content" | grep -q "✅ HEALTHY" | tail -1; then
        return 0
    else
        return 1
    fi
}

# Function to wait for recovery and measure MTTR
measure_mttr() {
    local scenario=$1
    local start_time=$2
    local max_wait=300  # 5 minutes max wait
    local check_interval=2
    local elapsed=0
    
    echo "⏱️  Waiting for recovery (max ${max_wait}s)..."
    
    while [ $elapsed -lt $max_wait ]; do
        sleep $check_interval
        elapsed=$((elapsed + check_interval))
        
        # Check if agent reports healthy
        if check_agent_health; then
            local end_time=$(get_timestamp)
            local mttr=$elapsed
            echo "✅ Recovery detected after ${mttr}s"
            
            # Record result
            echo "{
                \"scenario\": \"$scenario\",
                \"start_time\": \"$start_time\",
                \"end_time\": \"$end_time\",
                \"mttr_seconds\": $mttr,
                \"status\": \"recovered\"
            }," >> $RESULTS_FILE
            return 0
        fi
        
        echo "   Still unhealthy... ${elapsed}s elapsed"
    done
    
    echo "❌ Recovery timeout after ${max_wait}s"
    local end_time=$(get_timestamp)
    echo "{
        \"scenario\": \"$scenario\",
        \"start_time\": \"$start_time\",
        \"end_time\": \"$end_time\",
        \"mttr_seconds\": null,
        \"status\": \"timeout\"
    }," >> $RESULTS_FILE
    return 1
}

# Initialize results file
echo "[" > $RESULTS_FILE

# Clear any existing drift first
echo "🧹 Clearing existing network drift..."
cd $ANSIBLE_DIR
ansible-playbook -i inventory.yml network_drift_scenarios.yml --limit eng-gui -e restore_routes=true >/dev/null 2>&1 || true

# Wait for baseline health
echo "⏳ Waiting for baseline health..."
sleep 10

# Test scenarios
scenarios=("netem_delay" "remove_default_route" "interface_down" "packet_loss")

for scenario in "${scenarios[@]}"; do
    echo ""
    echo "🚨 Testing scenario: $scenario"
    
    # Introduce drift
    echo "   Introducing drift..."
    start_time=$(get_timestamp)
    
    ansible-playbook -i inventory.yml network_drift_scenarios.yml --limit eng-gui \
        -e "drift_scenario=$scenario" >/dev/null 2>&1
    
    # Measure MTTR
    measure_mttr "$scenario" "$start_time"
    
    # Clear drift for next test
    echo "   Clearing drift..."
    ansible-playbook -i inventory.yml network_drift_scenarios.yml --limit eng-gui \
        -e restore_routes=true >/dev/null 2>&1 || true
    
    # Wait between tests
    echo "   Waiting for stabilization..."
    sleep 15
done

# Finalize results file
sed -i '$ s/,$//' $RESULTS_FILE  # Remove trailing comma
echo "]" >> $RESULTS_FILE

echo ""
echo "📊 MTTR Test Results Summary:"
echo "=============================="

# Parse and display results
python3 -c "
import json
import sys

try:
    with open('$RESULTS_FILE', 'r') as f:
        results = json.load(f)
    
    total_tests = len(results)
    successful_recoveries = len([r for r in results if r['status'] == 'recovered'])
    
    print(f'Total Tests: {total_tests}')
    print(f'Successful Recoveries: {successful_recoveries}')
    print(f'Success Rate: {successful_recoveries/total_tests*100:.1f}%')
    print('')
    
    if successful_recoveries > 0:
        mttrs = [r['mttr_seconds'] for r in results if r['mttr_seconds'] is not None]
        avg_mttr = sum(mttrs) / len(mttrs)
        min_mttr = min(mttrs)
        max_mttr = max(mttrs)
        
        print(f'Average MTTR: {avg_mttr:.1f}s')
        print(f'Min MTTR: {min_mttr}s')
        print(f'Max MTTR: {max_mttr}s')
        print('')
    
    print('Individual Results:')
    for result in results:
        mttr_str = f\"{result['mttr_seconds']}s\" if result['mttr_seconds'] else \"TIMEOUT\"
        print(f\"  {result['scenario']}: {mttr_str} ({result['status']})\" )

except Exception as e:
    print(f'Error parsing results: {e}')
    sys.exit(1)
"

echo ""
echo "📄 Full results saved to: $RESULTS_FILE"
echo "🔍 View agent logs: docker exec $CONTAINER_NAME cat $LOG_FILE"

