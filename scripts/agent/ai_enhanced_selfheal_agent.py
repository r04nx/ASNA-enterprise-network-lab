#!/usr/bin/env python3
"""
AI-Enhanced Self-Healing Network Agent with Machine Learning Capabilities
Advanced implementation with RL-based decision making and comprehensive network management
"""

import os
import subprocess
import time
import json
import socket
import logging
import sys
import threading
import pickle
import hashlib
import ipaddress
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from collections import defaultdict, deque
import statistics
import math
import numpy as np

# Configuration from environment
DEVICE_NAME = os.environ.get("DEVICE_NAME", socket.gethostname())
DEVICE_ROLE = os.environ.get("DEVICE_ROLE", "unknown")
DEVICE_IP = os.environ.get("DEVICE_IP", "unknown")
EXPECTED_SUBNET = os.environ.get("EXPECTED_SUBNET", "172.20.20.0/24")
IFACE = os.environ.get("AGENT_IFACE", "eth0")
GATEWAY = os.environ.get("AGENT_GATEWAY", "172.20.20.1")
CHECK_HOST = os.environ.get("AGENT_CHECK_HOST", "172.20.20.7")
CHECK_PORT = int(os.environ.get("AGENT_CHECK_PORT", "80"))
SLEEP_INTERVAL = int(os.environ.get("AGENT_SLEEP", "2"))
LOG_LEVEL = os.environ.get("AGENT_LOG_LEVEL", "INFO")
METRICS_PORT = int(os.environ.get("METRICS_PORT", "9200"))
LEARNING_RATE = float(os.environ.get("AI_LEARNING_RATE", "0.1"))
EXPLORATION_RATE = float(os.environ.get("AI_EXPLORATION_RATE", "0.2"))

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - AI-SelfHeal[%(device)s] - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)
logger = logging.LoggerAdapter(logger, {'device': DEVICE_NAME})

class NetworkState:
    """Represents the current network state for ML analysis"""
    
    def __init__(self):
        self.interface_status = None
        self.ip_config = None
        self.routing_table = None
        self.tc_rules = None
        self.connectivity = None
        self.dns_resolution = None
        self.timestamp = None
        
    def get_state_hash(self):
        """Generate unique hash for this network state"""
        state_str = f"{self.interface_status}_{self.ip_config}_{self.routing_table}_{self.tc_rules}_{self.connectivity}"
        return hashlib.md5(state_str.encode()).hexdigest()[:8]
    
    def to_feature_vector(self):
        """Convert network state to ML feature vector"""
        features = []
        
        # Interface features
        features.append(1 if self.interface_status == 'UP' else 0)
        
        # IP configuration features
        features.append(1 if self.ip_config and self.is_ip_in_expected_subnet() else 0)
        features.append(1 if self.ip_config else 0)
        
        # Routing features
        features.append(1 if self.has_valid_default_route() else 0)
        features.append(len(self.routing_table) if self.routing_table else 0)
        
        # TC features
        features.append(1 if self.tc_rules and 'netem' in str(self.tc_rules) else 0)
        features.append(len(self.tc_rules) if self.tc_rules else 0)
        
        # Connectivity features
        features.append(1 if self.connectivity else 0)
        
        return np.array(features, dtype=np.float32)
    
    def is_ip_in_expected_subnet(self):
        """Check if current IP is in expected subnet"""
        try:
            if not self.ip_config:
                return False
            current_ip = ipaddress.ip_address(self.ip_config.split('/')[0])
            expected_network = ipaddress.ip_network(EXPECTED_SUBNET, strict=False)
            return current_ip in expected_network
        except:
            return False
    
    def has_valid_default_route(self):
        """Check if default route points to expected gateway"""
        if not self.routing_table:
            return False
        for route in self.routing_table:
            if 'default' in route and GATEWAY in route:
                return True
        return False

class ReinforcementLearner:
    """Simple Q-Learning agent for network remediation decisions"""
    
    def __init__(self, learning_rate=0.1, discount_factor=0.9, exploration_rate=0.2):
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        self.q_table = defaultdict(lambda: defaultdict(float))
        self.state_action_history = deque(maxlen=1000)
        self.success_memory = defaultdict(int)  # Track successful actions per state
        self.failure_memory = defaultdict(int)  # Track failed actions per state
        
    def get_action(self, state_hash, available_actions):
        """Select action using epsilon-greedy policy"""
        if np.random.random() < self.exploration_rate:
            # Exploration: random action
            action = np.random.choice(available_actions)
            logger.info(f"🎯 AI: Exploring with action '{action}' (exploration_rate={self.exploration_rate:.2f})")
            return action
        else:
            # Exploitation: best known action
            q_values = {action: self.q_table[state_hash][action] for action in available_actions}
            best_action = max(q_values, key=q_values.get)
            logger.info(f"🧠 AI: Exploiting with action '{best_action}' (Q={q_values[best_action]:.3f})")
            return best_action
    
    def update_q_value(self, state_hash, action, reward, next_state_hash, available_next_actions):
        """Update Q-value using Q-learning formula"""
        current_q = self.q_table[state_hash][action]
        
        if available_next_actions:
            max_next_q = max([self.q_table[next_state_hash][a] for a in available_next_actions])
        else:
            max_next_q = 0
        
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)
        self.q_table[state_hash][action] = new_q
        
        logger.info(f"📚 AI: Updated Q({state_hash[:6]}..., {action}) = {new_q:.3f} (was {current_q:.3f}, reward={reward})")
    
    def record_outcome(self, state_hash, action, success):
        """Record action outcome for learning"""
        if success:
            self.success_memory[f"{state_hash}_{action}"] += 1
        else:
            self.failure_memory[f"{state_hash}_{action}"] += 1
    
    def get_action_confidence(self, state_hash, action):
        """Get confidence score for an action based on historical success"""
        key = f"{state_hash}_{action}"
        successes = self.success_memory[key]
        failures = self.failure_memory[key]
        total = successes + failures
        
        if total == 0:
            return 0.5  # Unknown action
        return successes / total

class AIMetricsStore:
    """Enhanced metrics storage with AI capabilities tracking"""
    
    def __init__(self):
        self.lock = threading.Lock()
        self.reset_metrics()
        
    def reset_metrics(self):
        with self.lock:
            # Basic metrics
            self.agent_health_status = 1
            self.network_connectivity = 1
            self.interface_status = 1
            self.default_route_status = 1
            self.tc_drift_detected = 0
            self.ip_config_correct = 1
            
            # AI-specific metrics
            self.ai_decisions_total = 0
            self.ai_successful_decisions = 0
            self.ai_exploration_decisions = 0
            self.ai_exploitation_decisions = 0
            self.ai_learning_updates = 0
            self.ai_confidence_score = 0.5
            
            # Enhanced remediation metrics
            self.complex_ip_fixes = 0
            self.gateway_validations = 0
            self.subnet_corrections = 0
            self.multi_fault_recoveries = 0
            
            # MTTR and performance
            self.failure_count = 0
            self.recovery_count = 0
            self.current_failure_start = 0
            self.mttr_samples = []
            self.mttr_current = 0
            self.mttr_avg = 0
            self.mttr_p50 = 0
            self.mttr_p95 = 0
            self.mttr_p99 = 0
            
            self.remediation_attempts = 0
            self.remediation_successes = 0
            self.remediation_tc_clears = 0
            self.remediation_route_fixes = 0
            self.remediation_interface_fixes = 0
            
            self.check_duration_ms = 0
            self.last_check_timestamp = time.time()
            self.uptime_seconds = time.time()

# Global instances
metrics = AIMetricsStore()
ai_learner = ReinforcementLearner(LEARNING_RATE, 0.9, EXPLORATION_RATE)

def run_cmd(cmd, timeout=10):
    """Execute shell command with timeout and return result"""
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
            text=True, timeout=timeout
        )
        duration_ms = (time.time() - start_time) * 1000
        return result, duration_ms
    except subprocess.TimeoutExpired:
        logger.warning(f"Command timeout: {cmd}")
        return None, (time.time() - start_time) * 1000
    except Exception as e:
        logger.error(f"Command failed: {cmd} - {e}")
        return None, (time.time() - start_time) * 1000

def get_network_state():
    """Gather comprehensive network state information"""
    state = NetworkState()
    state.timestamp = time.time()
    
    # Interface status
    result, _ = run_cmd(f"ip link show {IFACE}")
    if result and result.returncode == 0:
        state.interface_status = 'UP' if 'state UP' in result.stdout else 'DOWN'
    
    # IP configuration
    result, _ = run_cmd(f"ip addr show {IFACE}")
    if result and result.returncode == 0:
        lines = result.stdout.split('\n')
        for line in lines:
            if 'inet ' in line and not '127.0.0.1' in line:
                state.ip_config = line.split()[1]
                break
    
    # Routing table
    result, _ = run_cmd("ip route")
    if result and result.returncode == 0:
        state.routing_table = result.stdout.strip().split('\n')
    
    # TC rules
    result, _ = run_cmd(f"tc qdisc show dev {IFACE}")
    if result and result.returncode == 0:
        state.tc_rules = result.stdout.strip()
    
    # Connectivity test
    result, _ = run_cmd(f"timeout 3 ping -c 1 {CHECK_HOST}")
    state.connectivity = result and result.returncode == 0
    
    return state

def validate_and_fix_ip_configuration(current_state):
    """AI-enhanced IP configuration validation and repair"""
    logger.info("🔍 AI: Analyzing IP configuration...")
    
    actions_taken = []
    
    if not current_state.ip_config:
        logger.warning("🚨 No IP configuration detected!")
        # Try DHCP first
        result, _ = run_cmd(f"dhclient -v {IFACE}")
        if result and result.returncode == 0:
            actions_taken.append("dhcp_renewal")
            logger.info("✅ DHCP renewal successful")
        else:
            # Fallback to static IP
            expected_ip = DEVICE_IP if DEVICE_IP != "unknown" else "172.20.20.14"
            result, _ = run_cmd(f"ip addr add {expected_ip}/24 dev {IFACE}")
            if result and result.returncode == 0:
                actions_taken.append("static_ip_assignment")
                logger.info(f"✅ Static IP {expected_ip}/24 assigned")
    
    elif not current_state.is_ip_in_expected_subnet():
        logger.warning(f"🚨 IP {current_state.ip_config} not in expected subnet {EXPECTED_SUBNET}")
        # Remove wrong IP and set correct one
        run_cmd(f"ip addr flush dev {IFACE}")
        expected_ip = DEVICE_IP if DEVICE_IP != "unknown" else "172.20.20.14"
        result, _ = run_cmd(f"ip addr add {expected_ip}/24 dev {IFACE}")
        if result and result.returncode == 0:
            actions_taken.append("ip_subnet_correction")
            logger.info(f"✅ IP corrected to {expected_ip}/24")
            metrics.subnet_corrections += 1
    
    return actions_taken

def validate_and_fix_gateway_configuration(current_state):
    """AI-enhanced gateway validation and repair"""
    logger.info("🔍 AI: Analyzing gateway configuration...")
    
    actions_taken = []
    
    # Check if default route exists and is correct
    has_correct_route = current_state.has_valid_default_route()
    
    if not has_correct_route:
        logger.warning("🚨 Invalid or missing default gateway!")
        
        # Remove all default routes first
        run_cmd("ip route del default", timeout=5)
        
        # Test gateway reachability
        result, _ = run_cmd(f"ping -c 1 -W 2 {GATEWAY}")
        if result and result.returncode == 0:
            # Gateway is reachable, add route
            result, _ = run_cmd(f"ip route add default via {GATEWAY} dev {IFACE}")
            if result and result.returncode == 0:
                actions_taken.append("gateway_route_fixed")
                logger.info(f"✅ Default gateway {GATEWAY} added")
                metrics.gateway_validations += 1
        else:
            logger.warning(f"⚠️ Gateway {GATEWAY} not reachable, trying route anyway")
            result, _ = run_cmd(f"ip route add default via {GATEWAY} dev {IFACE}")
            if result and result.returncode == 0:
                actions_taken.append("gateway_route_forced")
    
    return actions_taken

def ai_remediation_decision(current_state):
    """AI-powered remediation decision making"""
    state_hash = current_state.get_state_hash()
    
    # Define available remediation actions
    available_actions = [
        "fix_interface",
        "fix_ip_config", 
        "fix_gateway",
        "clear_tc_rules",
        "full_network_reset",
        "wait_and_retry"
    ]
    
    # Get AI decision
    with metrics.lock:
        metrics.ai_decisions_total += 1
        
    action = ai_learner.get_action(state_hash, available_actions)
    
    # Track exploration vs exploitation
    if np.random.random() < EXPLORATION_RATE:
        with metrics.lock:
            metrics.ai_exploration_decisions += 1
    else:
        with metrics.lock:
            metrics.ai_exploitation_decisions += 1
    
    return action, state_hash

def execute_ai_remediation(action, current_state):
    """Execute AI-selected remediation action"""
    logger.info(f"🤖 AI: Executing remediation action '{action}'")
    
    actions_taken = []
    success = False
    
    try:
        if action == "fix_interface":
            if current_state.interface_status != 'UP':
                result, _ = run_cmd(f"ip link set {IFACE} up")
                if result and result.returncode == 0:
                    actions_taken.append("interface_up")
                    success = True
                    metrics.remediation_interface_fixes += 1
        
        elif action == "fix_ip_config":
            ip_actions = validate_and_fix_ip_configuration(current_state)
            actions_taken.extend(ip_actions)
            success = len(ip_actions) > 0
            if success:
                metrics.complex_ip_fixes += 1
        
        elif action == "fix_gateway":
            gw_actions = validate_and_fix_gateway_configuration(current_state)
            actions_taken.extend(gw_actions)
            success = len(gw_actions) > 0
            if success:
                metrics.remediation_route_fixes += 1
        
        elif action == "clear_tc_rules":
            if 'netem' in str(current_state.tc_rules):
                result, _ = run_cmd(f"tc qdisc del dev {IFACE} root")
                if result and result.returncode == 0:
                    actions_taken.append("tc_cleared")
                    success = True
                    metrics.remediation_tc_clears += 1
        
        elif action == "full_network_reset":
            # Comprehensive network reset
            reset_actions = []
            
            # Clear TC rules
            run_cmd(f"tc qdisc del dev {IFACE} root")
            reset_actions.append("tc_reset")
            
            # Reset interface
            run_cmd(f"ip link set {IFACE} down")
            time.sleep(1)
            run_cmd(f"ip link set {IFACE} up")
            reset_actions.append("interface_reset")
            
            # Fix IP and gateway
            ip_actions = validate_and_fix_ip_configuration(current_state)
            gw_actions = validate_and_fix_gateway_configuration(current_state)
            
            reset_actions.extend(ip_actions)
            reset_actions.extend(gw_actions)
            
            actions_taken = reset_actions
            success = len(reset_actions) > 2
            if success:
                metrics.multi_fault_recoveries += 1
        
        elif action == "wait_and_retry":
            logger.info("🕐 AI: Waiting before retry...")
            time.sleep(5)
            actions_taken.append("wait_strategy")
            success = True  # Waiting is always "successful"
    
    except Exception as e:
        logger.error(f"❌ AI remediation failed: {e}")
        success = False
    
    return actions_taken, success

def comprehensive_network_health_check():
    """AI-enhanced comprehensive network health assessment"""
    start_time = time.time()
    
    # Get detailed network state
    current_state = get_network_state()
    
    # Evaluate health conditions
    health = {
        'interface_up': current_state.interface_status == 'UP',
        'ip_configured': current_state.ip_config is not None,
        'ip_subnet_correct': current_state.is_ip_in_expected_subnet(),
        'default_route': current_state.has_valid_default_route(),
        'tcp_connectivity': current_state.connectivity,
        'tc_drift': 'netem' in str(current_state.tc_rules) if current_state.tc_rules else False,
        'timestamp': datetime.utcnow().isoformat(),
        'state_hash': current_state.get_state_hash()
    }
    
    # Overall health: all critical checks must pass
    health['healthy'] = (
        health['interface_up'] and 
        health['ip_configured'] and
        health['ip_subnet_correct'] and
        health['default_route'] and 
        health['tcp_connectivity'] and
        not health['tc_drift']
    )
    
    # Update metrics
    check_duration = (time.time() - start_time) * 1000
    
    with metrics.lock:
        metrics.agent_health_status = 1 if health['healthy'] else 0
        metrics.network_connectivity = 1 if health['tcp_connectivity'] else 0
        metrics.interface_status = 1 if health['interface_up'] else 0
        metrics.default_route_status = 1 if health['default_route'] else 0
        metrics.tc_drift_detected = 1 if health['tc_drift'] else 0
        metrics.ip_config_correct = 1 if health['ip_subnet_correct'] else 0
        metrics.check_duration_ms = check_duration
        metrics.last_check_timestamp = time.time()
        
        # MTTR tracking
        if not health['healthy'] and metrics.current_failure_start == 0:
            metrics.failure_count += 1
            metrics.current_failure_start = time.time()
            logger.info(f"🔴 AI: Failure #{metrics.failure_count} detected")
        elif health['healthy'] and metrics.current_failure_start > 0:
            recovery_time = time.time() - metrics.current_failure_start
            metrics.recovery_count += 1
            metrics.mttr_samples.append(recovery_time)
            metrics.mttr_current = recovery_time
            
            if len(metrics.mttr_samples) > 100:
                metrics.mttr_samples = metrics.mttr_samples[-100:]
            
            if metrics.mttr_samples:
                metrics.mttr_avg = statistics.mean(metrics.mttr_samples)
                metrics.mttr_p50 = statistics.median(metrics.mttr_samples)
                if len(metrics.mttr_samples) > 10:
                    metrics.mttr_p95 = statistics.quantiles(metrics.mttr_samples, n=20)[18]
                if len(metrics.mttr_samples) > 20:
                    metrics.mttr_p99 = statistics.quantiles(metrics.mttr_samples, n=100)[98]
            
            metrics.current_failure_start = 0
            logger.info(f"🟢 AI: Recovery #{metrics.recovery_count} completed in {recovery_time:.3f}s")
    
    return health, current_state

def perform_ai_remediation():
    """Execute AI-powered remediation with learning"""
    logger.info("🤖 AI: Starting intelligent remediation...")
    
    # Get current network state
    _, current_state = comprehensive_network_health_check()
    
    # Get AI decision
    action, state_hash = ai_remediation_decision(current_state)
    
    # Execute remediation
    actions_taken, success = execute_ai_remediation(action, current_state)
    
    # Wait and assess results
    time.sleep(3)
    post_health, post_state = comprehensive_network_health_check()
    
    # Calculate reward for learning
    if post_health['healthy']:
        reward = 10.0  # High reward for successful recovery
    elif len(actions_taken) > 0:
        reward = 2.0   # Small reward for taking action
    else:
        reward = -1.0  # Penalty for doing nothing
    
    # Update AI learning
    post_state_hash = post_state.get_state_hash()
    available_actions = ["fix_interface", "fix_ip_config", "fix_gateway", "clear_tc_rules", "full_network_reset", "wait_and_retry"]
    
    ai_learner.update_q_value(state_hash, action, reward, post_state_hash, available_actions)
    ai_learner.record_outcome(state_hash, action, success)
    
    with metrics.lock:
        metrics.ai_learning_updates += 1
        metrics.ai_confidence_score = ai_learner.get_action_confidence(state_hash, action)
        metrics.remediation_attempts += 1
        if success:
            metrics.remediation_successes += 1
    
    result = {
        'ai_action': action,
        'actions_taken': actions_taken,
        'success': success,
        'reward': reward,
        'pre_state': state_hash,
        'post_state': post_state_hash,
        'post_healthy': post_health['healthy'],
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return result

class AIMetricsHandler(BaseHTTPRequestHandler):
    """Enhanced HTTP handler for AI metrics"""
    
    def do_GET(self):
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            
            metrics_text = self.generate_ai_metrics()
            self.wfile.write(metrics_text.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def generate_ai_metrics(self):
        """Generate comprehensive AI-enhanced Prometheus metrics"""
        uptime = time.time() - metrics.uptime_seconds
        
        return f"""# HELP selfheal_agent_health Current health status (1=healthy, 0=unhealthy)
# TYPE selfheal_agent_health gauge
selfheal_agent_health{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.agent_health_status}

# HELP selfheal_network_connectivity Network connectivity status (1=connected, 0=disconnected)
# TYPE selfheal_network_connectivity gauge
selfheal_network_connectivity{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.network_connectivity}

# HELP selfheal_interface_status Network interface status (1=up, 0=down)
# TYPE selfheal_interface_status gauge
selfheal_interface_status{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}",interface="{IFACE}"}} {metrics.interface_status}

# HELP selfheal_default_route_status Default route status (1=correct, 0=missing/wrong)
# TYPE selfheal_default_route_status gauge
selfheal_default_route_status{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.default_route_status}

# HELP selfheal_ip_config_correct IP configuration correctness (1=correct, 0=wrong)
# TYPE selfheal_ip_config_correct gauge
selfheal_ip_config_correct{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.ip_config_correct}

# HELP selfheal_tc_drift_detected Traffic control drift detection (1=drift, 0=clean)
# TYPE selfheal_tc_drift_detected gauge
selfheal_tc_drift_detected{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}",interface="{IFACE}"}} {metrics.tc_drift_detected}

# HELP selfheal_ai_decisions_total Total AI decisions made
# TYPE selfheal_ai_decisions_total counter
selfheal_ai_decisions_total{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.ai_decisions_total}

# HELP selfheal_ai_successful_decisions_total Total successful AI decisions
# TYPE selfheal_ai_successful_decisions_total counter
selfheal_ai_successful_decisions_total{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.ai_successful_decisions}

# HELP selfheal_ai_exploration_decisions_total AI exploration decisions
# TYPE selfheal_ai_exploration_decisions_total counter
selfheal_ai_exploration_decisions_total{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.ai_exploration_decisions}

# HELP selfheal_ai_exploitation_decisions_total AI exploitation decisions
# TYPE selfheal_ai_exploitation_decisions_total counter
selfheal_ai_exploitation_decisions_total{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.ai_exploitation_decisions}

# HELP selfheal_ai_learning_updates_total AI learning updates performed
# TYPE selfheal_ai_learning_updates_total counter
selfheal_ai_learning_updates_total{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.ai_learning_updates}

# HELP selfheal_ai_confidence_score AI confidence score (0-1)
# TYPE selfheal_ai_confidence_score gauge
selfheal_ai_confidence_score{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.ai_confidence_score}

# HELP selfheal_complex_ip_fixes_total Complex IP configuration fixes
# TYPE selfheal_complex_ip_fixes_total counter
selfheal_complex_ip_fixes_total{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.complex_ip_fixes}

# HELP selfheal_gateway_validations_total Gateway validations performed
# TYPE selfheal_gateway_validations_total counter
selfheal_gateway_validations_total{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.gateway_validations}

# HELP selfheal_subnet_corrections_total Subnet corrections performed
# TYPE selfheal_subnet_corrections_total counter
selfheal_subnet_corrections_total{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.subnet_corrections}

# HELP selfheal_multi_fault_recoveries_total Multi-fault recoveries performed
# TYPE selfheal_multi_fault_recoveries_total counter
selfheal_multi_fault_recoveries_total{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.multi_fault_recoveries}

# HELP selfheal_mttr_current_seconds Current MTTR in seconds
# TYPE selfheal_mttr_current_seconds gauge
selfheal_mttr_current_seconds{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.mttr_current}

# HELP selfheal_mttr_average_seconds Average MTTR in seconds
# TYPE selfheal_mttr_average_seconds gauge
selfheal_mttr_average_seconds{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.mttr_avg}

# HELP selfheal_failure_count_total Total failures detected
# TYPE selfheal_failure_count_total counter
selfheal_failure_count_total{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.failure_count}

# HELP selfheal_recovery_count_total Total recoveries completed
# TYPE selfheal_recovery_count_total counter
selfheal_recovery_count_total{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.recovery_count}

# HELP selfheal_remediation_attempts_total Total remediation attempts
# TYPE selfheal_remediation_attempts_total counter
selfheal_remediation_attempts_total{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.remediation_attempts}

# HELP selfheal_remediation_successes_total Total successful remediations
# TYPE selfheal_remediation_successes_total counter
selfheal_remediation_successes_total{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.remediation_successes}

# HELP selfheal_uptime_seconds Agent uptime in seconds
# TYPE selfheal_uptime_seconds gauge
selfheal_uptime_seconds{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {uptime}
"""
    
    def log_message(self, format, *args):
        pass

def start_metrics_server():
    """Start AI-enhanced metrics HTTP server"""
    try:
        server = HTTPServer(('0.0.0.0', METRICS_PORT), AIMetricsHandler)
        logger.info(f"🚀 AI Metrics server started on port {METRICS_PORT}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")

def main():
    """Main AI-enhanced agent loop"""
    logger.info("🤖 AI-Enhanced Self-Healing Network Agent Starting")
    logger.info(f"Configuration: Device={DEVICE_NAME}, Role={DEVICE_ROLE}, IP={DEVICE_IP}")
    logger.info(f"Network: Interface={IFACE}, Gateway={GATEWAY}, Expected_Subnet={EXPECTED_SUBNET}")
    logger.info(f"AI: LR={LEARNING_RATE}, Exploration={EXPLORATION_RATE}")
    logger.info(f"Metrics: Port={METRICS_PORT}")
    
    # Start metrics server
    metrics_thread = threading.Thread(target=start_metrics_server, daemon=True)
    metrics_thread.start()
    
    consecutive_failures = 0
    backoff_sleep = SLEEP_INTERVAL
    max_backoff = 60
    
    while True:
        try:
            # Comprehensive health check
            health, _ = comprehensive_network_health_check()
            
            if health['healthy']:
                status_msg = f"Health: 🟢 HEALTHY (State: {health['state_hash'][:6]}...)"
                logger.info(status_msg)
                consecutive_failures = 0
                backoff_sleep = SLEEP_INTERVAL
            else:
                status_msg = f"Health: 🔴 UNHEALTHY (State: {health['state_hash'][:6]}...)"
                logger.warning(status_msg)
                logger.warning(f"Issues: Interface={health['interface_up']}, IP_Config={health['ip_configured']}, "
                             f"IP_Subnet={health['ip_subnet_correct']}, Route={health['default_route']}, "
                             f"Connectivity={health['tcp_connectivity']}, TC_Drift={health['tc_drift']}")
                
                # Perform AI-powered remediation
                remediation = perform_ai_remediation()
                logger.info(f"AI Remediation: {json.dumps(remediation, default=str)}")
                
                if remediation['post_healthy']:
                    logger.info("🟢 AI: Network connectivity restored!")
                    consecutive_failures = 0
                    backoff_sleep = SLEEP_INTERVAL
                else:
                    consecutive_failures += 1
                    logger.error(f"🔴 AI: Remediation incomplete. Consecutive failures: {consecutive_failures}")
                    
                    if consecutive_failures > 1:
                        backoff_sleep = min(backoff_sleep * 1.5, max_backoff)
                        logger.warning(f"AI: Using backoff sleep: {backoff_sleep:.1f}s")
            
        except KeyboardInterrupt:
            logger.info("🛑 AI Agent stopped by user")
            break
        except Exception as e:
            logger.error(f"AI Agent error: {e}")
            consecutive_failures += 1
        
        time.sleep(backoff_sleep)

if __name__ == "__main__":
    main()
