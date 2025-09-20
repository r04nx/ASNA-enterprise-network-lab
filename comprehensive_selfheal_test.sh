#!/bin/bash

# Comprehensive Self-Healing Agent Test Script
# Tests agent performance with real-time monitoring integration

set -e

CONTAINER_NAME="clab-enterprise-final-eng-gui"
LOG_FILE="/tmp/selfheal.log"
RESULTS_DIR="test_results_$(date +%Y%m%d_%H%M%S)"
GRAFANA_URL="http://localhost:3000"
PROMETHEUS_URL="http://localhost:9090"

echo "🧪 Comprehensive Self-Healing Agent Performance Test"
echo "===================================================="
echo "Target Container: $CONTAINER_NAME"
echo "Test Results Dir: $RESULTS_DIR"
echo "Grafana Dashboard: $GRAFANA_URL"
echo "Prometheus Metrics: $PROMETHEUS_URL"
echo ""

# Create results directory
mkdir -p "$RESULTS_DIR"

# Function to get high-precision timestamp
get_timestamp() {
    date -u +"%Y-%m-%dT%H:%M:%S.%6NZ"
}

# Function to get epoch timestamp in milliseconds
get_epoch_ms() {
    date +%s%3N
}

# Function to log with timestamp
log_event() {
    local event="$1"
    local timestamp=$(get_timestamp)
    local epoch_ms=$(get_epoch_ms)
    echo "[$timestamp] $event" | tee -a "$RESULTS_DIR/timeline.log"
    echo "$epoch_ms,$event" >> "$RESULTS_DIR/events.csv"
}

# Function to check agent health from logs
check_agent_health() {
    local recent_logs=$(docker exec $CONTAINER_NAME tail -20 $LOG_FILE 2>/dev/null || echo "")
    if echo "$recent_logs" | tail -5 | grep -q "✅ HEALTHY"; then
        return 0
    else
        return 1
    fi
}

# Function to monitor network connectivity
monitor_connectivity() {
    local scenario="$1"
    local max_duration="$2"  # seconds
    local output_file="$RESULTS_DIR/connectivity_${scenario}.csv"
    
    echo "timestamp_ms,scenario,ping_success,agent_healthy" > "$output_file"
    
    local start_time=$(get_epoch_ms)
    local end_time=$((start_time + max_duration * 1000))
    
    while [ $(get_epoch_ms) -lt $end_time ]; do
        local current_time=$(get_epoch_ms)
        
        # Test ping to gateway
        local ping_result="false"
        if docker exec $CONTAINER_NAME timeout 1 ping -c 1 172.20.20.1 >/dev/null 2>&1; then
            ping_result="true"
        fi
        
        # Check agent health
        local agent_healthy="false"
        if check_agent_health; then
            agent_healthy="true"
        fi
        
        echo "$current_time,$scenario,$ping_result,$agent_healthy" >> "$output_file"
        sleep 0.5
    done
}

# Function to create network scenarios
create_scenario() {
    local scenario="$1"
    log_event "SCENARIO_START: $scenario"
    
    case "$scenario" in
        "tc_netem_delay")
            log_event "ACTION: Adding TC netem delay 500ms"
            docker exec $CONTAINER_NAME tc qdisc add dev eth0 root netem delay 500ms 100ms
            ;;
        "remove_default_route")
            log_event "ACTION: Removing default route"
            docker exec $CONTAINER_NAME ip route del default
            ;;
        "interface_down")
            log_event "ACTION: Bringing interface down"
            docker exec $CONTAINER_NAME ip link set eth0 down
            ;;
        "tc_packet_loss")
            log_event "ACTION: Adding 50% packet loss"
            docker exec $CONTAINER_NAME tc qdisc add dev eth0 root netem loss 50%
            ;;
        "wrong_gateway")
            log_event "ACTION: Changing to wrong gateway"
            docker exec $CONTAINER_NAME ip route del default
            docker exec $CONTAINER_NAME ip route add default via 192.168.99.1
            ;;
        *)
            log_event "ERROR: Unknown scenario $scenario"
            return 1
            ;;
    esac
    
    log_event "SCENARIO_CREATED: $scenario"
}

# Function to clear all network issues
clear_network_issues() {
    log_event "ACTION: Clearing all network issues"
    
    # Remove TC rules
    docker exec $CONTAINER_NAME tc qdisc del dev eth0 root 2>/dev/null || true
    
    # Bring interface up
    docker exec $CONTAINER_NAME ip link set eth0 up 2>/dev/null || true
    
    # Restore correct default route
    docker exec $CONTAINER_NAME ip route del default 2>/dev/null || true
    docker exec $CONTAINER_NAME ip route add default via 172.20.20.1 dev eth0 2>/dev/null || true
    
    sleep 2
    log_event "ACTION: Network issues cleared"
}

# Function to wait for recovery and measure MTTR
measure_mttr() {
    local scenario="$1"
    local start_epoch_ms=$(get_epoch_ms)
    local max_wait_ms=$((300 * 1000))  # 5 minutes in milliseconds
    local end_time_ms=$((start_epoch_ms + max_wait_ms))
    
    log_event "MTTR_MEASUREMENT_START: $scenario"
    echo "⏱️  Measuring MTTR for $scenario (max 300s)..."
    
    while [ $(get_epoch_ms) -lt $end_time_ms ]; do
        if check_agent_health; then
            local recovery_time_ms=$(get_epoch_ms)
            local mttr_ms=$((recovery_time_ms - start_epoch_ms))
            local mttr_seconds=$(echo "scale=3; $mttr_ms / 1000" | bc)
            
            log_event "RECOVERY_DETECTED: $scenario after ${mttr_seconds}s"
            echo "✅ Recovery detected after ${mttr_seconds}s"
            
            # Save MTTR result
            echo "$scenario,$start_epoch_ms,$recovery_time_ms,$mttr_ms,$mttr_seconds,recovered" >> "$RESULTS_DIR/mttr_results.csv"
            return 0
        fi
        
        sleep 0.5
    done
    
    # Timeout
    local timeout_time_ms=$(get_epoch_ms)
    log_event "RECOVERY_TIMEOUT: $scenario after 300s"
    echo "❌ Recovery timeout after 300s"
    echo "$scenario,$start_epoch_ms,$timeout_time_ms,300000,300.000,timeout" >> "$RESULTS_DIR/mttr_results.csv"
    return 1
}

# Function to capture agent logs
capture_agent_logs() {
    local scenario="$1"
    local log_file="$RESULTS_DIR/agent_logs_${scenario}.log"
    docker exec $CONTAINER_NAME cat $LOG_FILE > "$log_file"
}

# Function to run single test scenario
run_test_scenario() {
    local scenario="$1"
    
    echo ""
    echo "🚨 Testing Scenario: $scenario"
    echo "================================"
    
    # Clear any existing issues first
    clear_network_issues
    
    # Wait for baseline stability
    log_event "BASELINE_WAIT_START: $scenario"
    echo "   Waiting for baseline stability..."
    sleep 5
    
    # Verify healthy baseline
    if ! check_agent_health; then
        echo "   ⚠️  Agent not healthy at baseline - waiting longer..."
        sleep 10
    fi
    
    log_event "BASELINE_CONFIRMED: $scenario"
    
    # Start connectivity monitoring in background
    monitor_connectivity "$scenario" 120 &
    local monitor_pid=$!
    
    # Create the network issue
    create_scenario "$scenario"
    local scenario_start_ms=$(get_epoch_ms)
    
    # Measure MTTR
    measure_mttr "$scenario"
    local recovery_result=$?
    
    # Stop connectivity monitoring
    kill $monitor_pid 2>/dev/null || true
    wait $monitor_pid 2>/dev/null || true
    
    # Capture agent logs
    capture_agent_logs "$scenario"
    
    # Clear issues for next test
    clear_network_issues
    
    log_event "SCENARIO_COMPLETE: $scenario"
    echo "   ✅ Scenario $scenario completed"
    
    # Wait between tests
    echo "   ⏳ Cooling down before next test..."
    sleep 10
    
    return $recovery_result
}

# Initialize results files
echo "scenario,start_epoch_ms,end_epoch_ms,mttr_ms,mttr_seconds,status" > "$RESULTS_DIR/mttr_results.csv"
echo "timestamp,event" > "$RESULTS_DIR/events.csv"

# Check initial agent status
echo "🔍 Initial Agent Health Check"
echo "=============================="
sleep 3
if check_agent_health; then
    echo "✅ Agent is healthy and ready for testing"
    log_event "INITIAL_STATUS: Agent healthy"
else
    echo "⚠️  Agent appears unhealthy - may impact test results"
    log_event "INITIAL_STATUS: Agent unhealthy"
fi

echo ""
echo "🎯 Starting Test Scenarios"
echo "=========================="

# Test scenarios in order of increasing severity
test_scenarios=(
    "tc_netem_delay"
    "tc_packet_loss" 
    "wrong_gateway"
    "remove_default_route"
    "interface_down"
)

successful_tests=0
total_tests=${#test_scenarios[@]}

for scenario in "${test_scenarios[@]}"; do
    if run_test_scenario "$scenario"; then
        successful_tests=$((successful_tests + 1))
    fi
done

# Generate final report
echo ""
echo "📊 Test Results Summary"
echo "======================"
echo "Total Tests: $total_tests"
echo "Successful Recoveries: $successful_tests"
echo "Success Rate: $(echo "scale=1; $successful_tests * 100 / $total_tests" | bc)%"
echo ""

# Display MTTR statistics if any recoveries occurred
if [ $successful_tests -gt 0 ]; then
    echo "MTTR Statistics:"
    python3 -c "
import pandas as pd
import numpy as np

df = pd.read_csv('$RESULTS_DIR/mttr_results.csv')
recovered = df[df['status'] == 'recovered']

if len(recovered) > 0:
    print(f'  Average MTTR: {recovered[\"mttr_seconds\"].mean():.3f}s')
    print(f'  Median MTTR:  {recovered[\"mttr_seconds\"].median():.3f}s')
    print(f'  Min MTTR:     {recovered[\"mttr_seconds\"].min():.3f}s')
    print(f'  Max MTTR:     {recovered[\"mttr_seconds\"].max():.3f}s')
    print(f'  Std Dev:      {recovered[\"mttr_seconds\"].std():.3f}s')
else:
    print('  No successful recoveries to analyze')
" 2>/dev/null || echo "  (Install pandas for detailed statistics)"
fi

echo ""
echo "📁 Detailed Results Location: $RESULTS_DIR/"
echo "🔍 View agent logs: docker exec $CONTAINER_NAME cat $LOG_FILE"
echo "📊 Grafana Dashboard: $GRAFANA_URL"
echo "📈 Prometheus Metrics: $PROMETHEUS_URL"
echo ""
echo "🎉 Testing Complete!"

