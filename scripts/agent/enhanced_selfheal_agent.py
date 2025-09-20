#!/usr/bin/env python3
"""
Enhanced Smart Autonomous Self-Healing Network Agent with Prometheus Metrics
Journal-quality implementation with comprehensive monitoring and analytics
"""

import os
import subprocess
import time
import json
import socket
import logging
import sys
import threading
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import statistics
import math

# Configuration from environment
DEVICE_NAME = os.environ.get("DEVICE_NAME", socket.gethostname())
DEVICE_ROLE = os.environ.get("DEVICE_ROLE", "unknown")
DEVICE_IP = os.environ.get("DEVICE_IP", "unknown")
IFACE = os.environ.get("AGENT_IFACE", "eth0")
GATEWAY = os.environ.get("AGENT_GATEWAY", "172.20.20.1")
CHECK_HOST = os.environ.get("AGENT_CHECK_HOST", "172.20.20.7")
CHECK_PORT = int(os.environ.get("AGENT_CHECK_PORT", "80"))
SLEEP_INTERVAL = int(os.environ.get("AGENT_SLEEP", "2"))
LOG_LEVEL = os.environ.get("AGENT_LOG_LEVEL", "INFO")
METRICS_PORT = int(os.environ.get("METRICS_PORT", "9200"))

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - SelfHeal[%(device)s] - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)
logger = logging.LoggerAdapter(logger, {'device': DEVICE_NAME})

# Global metrics storage
class MetricsStore:
    def __init__(self):
        self.lock = threading.Lock()
        self.reset_metrics()
        
    def reset_metrics(self):
        with self.lock:
            self.agent_health_status = 1  # 1=healthy, 0=unhealthy
            self.network_connectivity = 1  # 1=connected, 0=disconnected
            self.interface_status = 1      # 1=up, 0=down
            self.default_route_status = 1  # 1=present, 0=missing
            self.tc_drift_detected = 0     # 1=drift detected, 0=clean
            
            # MTTR metrics
            self.failure_count = 0
            self.recovery_count = 0
            self.current_failure_start = 0
            self.mttr_samples = []
            self.mttr_current = 0
            self.mttr_avg = 0
            self.mttr_p50 = 0
            self.mttr_p95 = 0
            self.mttr_p99 = 0
            
            # Remediation metrics
            self.remediation_attempts = 0
            self.remediation_successes = 0
            self.remediation_tc_clears = 0
            self.remediation_route_fixes = 0
            self.remediation_interface_fixes = 0
            
            # Performance metrics
            self.check_duration_ms = 0
            self.last_check_timestamp = time.time()
            self.uptime_seconds = time.time()
            
    def update_health_status(self, health_data):
        with self.lock:
            self.agent_health_status = 1 if health_data['healthy'] else 0
            self.network_connectivity = 1 if health_data['tcp_connectivity'] else 0
            self.interface_status = 1 if health_data['interface_up'] else 0
            self.default_route_status = 1 if health_data['default_route'] else 0
            self.tc_drift_detected = 1 if health_data['tc_drift'] else 0
            self.last_check_timestamp = time.time()
            
            # MTTR tracking
            if not health_data['healthy'] and self.current_failure_start == 0:
                # Failure detected
                self.failure_count += 1
                self.current_failure_start = time.time()
                logger.info(f"🔴 Failure #{self.failure_count} detected at {datetime.now().isoformat()}")
                
            elif health_data['healthy'] and self.current_failure_start > 0:
                # Recovery detected
                recovery_time = time.time() - self.current_failure_start
                self.recovery_count += 1
                self.mttr_samples.append(recovery_time)
                self.mttr_current = recovery_time
                
                # Keep only last 100 samples for statistics
                if len(self.mttr_samples) > 100:
                    self.mttr_samples = self.mttr_samples[-100:]
                
                # Calculate statistics
                self.mttr_avg = statistics.mean(self.mttr_samples)
                self.mttr_p50 = statistics.median(self.mttr_samples)
                self.mttr_p95 = statistics.quantiles(self.mttr_samples, n=20)[18] if len(self.mttr_samples) > 10 else 0
                self.mttr_p99 = statistics.quantiles(self.mttr_samples, n=100)[98] if len(self.mttr_samples) > 20 else 0
                
                self.current_failure_start = 0
                logger.info(f"🟢 Recovery #{self.recovery_count} completed in {recovery_time:.3f}s")
                
    def record_remediation(self, actions_taken):
        with self.lock:
            self.remediation_attempts += 1
            if len(actions_taken) > 0:
                self.remediation_successes += 1
                
            for action in actions_taken:
                if "tc_netem" in action:
                    self.remediation_tc_clears += 1
                elif "route" in action:
                    self.remediation_route_fixes += 1
                elif "interface" in action:
                    self.remediation_interface_fixes += 1
    
    def update_performance(self, duration_ms):
        with self.lock:
            self.check_duration_ms = duration_ms

# Global metrics instance
metrics = MetricsStore()

def run_cmd(cmd, timeout=10):
    """Execute shell command with timeout and return result"""
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            timeout=timeout
        )
        duration_ms = (time.time() - start_time) * 1000
        return result, duration_ms
    except subprocess.TimeoutExpired:
        logger.warning(f"Command timeout: {cmd}")
        return None, (time.time() - start_time) * 1000
    except Exception as e:
        logger.error(f"Command failed: {cmd} - {e}")
        return None, (time.time() - start_time) * 1000

def tcp_connectivity_check(host, port, timeout=3.0):
    """Test TCP connectivity to host:port"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception as e:
        logger.debug(f"TCP check failed to {host}:{port} - {e}")
        return False

def has_tc_netem_drift(iface):
    """Check if traffic control netem is configured (indicates drift)"""
    result, _ = run_cmd(f"tc qdisc show dev {iface}")
    if result and result.returncode == 0:
        output = result.stdout + result.stderr
        return "netem" in output.lower()
    return False

def interface_is_up(iface):
    """Check if network interface is UP"""
    result, _ = run_cmd(f"ip addr show {iface}")
    if result and result.returncode == 0:
        return "state UP" in result.stdout
    return False

def has_default_route():
    """Check if default route exists"""
    result, _ = run_cmd("ip route show default")
    if result and result.returncode == 0:
        return "default" in result.stdout
    return False

def network_health_check():
    """Comprehensive network health assessment"""
    start_time = time.time()
    
    health = {
        'interface_up': interface_is_up(IFACE),
        'default_route': has_default_route(), 
        'tcp_connectivity': tcp_connectivity_check(CHECK_HOST, CHECK_PORT),
        'tc_drift': has_tc_netem_drift(IFACE),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Overall health: all good checks True, all bad checks False
    health['healthy'] = (
        health['interface_up'] and 
        health['default_route'] and 
        health['tcp_connectivity'] and
        not health['tc_drift']
    )
    
    # Update metrics
    check_duration = (time.time() - start_time) * 1000
    metrics.update_health_status(health)
    metrics.update_performance(check_duration)
    
    return health

def remediate_tc_drift(iface):
    """Remove traffic control netem rules"""
    logger.info(f"Removing TC netem drift from {iface}")
    result, _ = run_cmd(f"tc qdisc del dev {iface} root")
    if result and result.returncode == 0:
        logger.info("Successfully removed TC netem rule")
        return True
    else:
        logger.error(f"Failed to remove TC rule: {result.stderr if result else 'Unknown error'}")
        return False

def remediate_interface(iface):
    """Ensure network interface is UP"""
    logger.info(f"Ensuring interface {iface} is UP")
    result, _ = run_cmd(f"ip link set {iface} up")
    if result and result.returncode == 0:
        logger.info(f"Interface {iface} set to UP")
        return True
    else:
        logger.error(f"Failed to set interface UP: {result.stderr if result else 'Unknown error'}")
        return False

def remediate_default_route(gateway, iface):
    """Restore default route"""
    logger.info(f"Restoring default route via {gateway} dev {iface}")
    result, _ = run_cmd(f"ip route replace default via {gateway} dev {iface}")
    if result and result.returncode == 0:
        logger.info("Default route restored")
        return True
    else:
        logger.error(f"Failed to restore route: {result.stderr if result else 'Unknown error'}")
        return False

def perform_remediation():
    """Execute remediation sequence"""
    actions_taken = []
    success_count = 0
    
    # 1. Clear TC netem drift
    if has_tc_netem_drift(IFACE):
        if remediate_tc_drift(IFACE):
            actions_taken.append("cleared_tc_netem")
            success_count += 1
        else:
            actions_taken.append("failed_tc_netem_clear")
    
    # 2. Ensure interface is UP
    if not interface_is_up(IFACE):
        if remediate_interface(IFACE):
            actions_taken.append("interface_restored")
            success_count += 1
        else:
            actions_taken.append("failed_interface_restore")
    
    # 3. Restore default route if missing
    if not has_default_route():
        if remediate_default_route(GATEWAY, IFACE):
            actions_taken.append("route_restored")
            success_count += 1
        else:
            actions_taken.append("failed_route_restore")
    
    result = {
        'actions_taken': actions_taken,
        'success_count': success_count,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Record remediation metrics
    metrics.record_remediation(actions_taken)
    
    return result

class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for Prometheus metrics endpoint"""
    
    def do_GET(self):
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            
            # Generate Prometheus metrics
            metrics_text = self.generate_metrics()
            self.wfile.write(metrics_text.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def generate_metrics(self):
        """Generate Prometheus metrics in text format"""
        uptime = time.time() - metrics.uptime_seconds
        
        prometheus_metrics = f"""# HELP selfheal_agent_health Current health status of the self-healing agent (1=healthy, 0=unhealthy)
# TYPE selfheal_agent_health gauge
selfheal_agent_health{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.agent_health_status}

# HELP selfheal_network_connectivity Network connectivity status (1=connected, 0=disconnected)  
# TYPE selfheal_network_connectivity gauge
selfheal_network_connectivity{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.network_connectivity}

# HELP selfheal_interface_status Network interface status (1=up, 0=down)
# TYPE selfheal_interface_status gauge
selfheal_interface_status{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}",interface="{IFACE}"}} {metrics.interface_status}

# HELP selfheal_default_route_status Default route presence (1=present, 0=missing)
# TYPE selfheal_default_route_status gauge
selfheal_default_route_status{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.default_route_status}

# HELP selfheal_tc_drift_detected Traffic control drift detection (1=drift detected, 0=clean)
# TYPE selfheal_tc_drift_detected gauge
selfheal_tc_drift_detected{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}",interface="{IFACE}"}} {metrics.tc_drift_detected}

# HELP selfheal_failure_count_total Total number of failures detected
# TYPE selfheal_failure_count_total counter
selfheal_failure_count_total{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.failure_count}

# HELP selfheal_recovery_count_total Total number of successful recoveries
# TYPE selfheal_recovery_count_total counter
selfheal_recovery_count_total{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.recovery_count}

# HELP selfheal_mttr_current_seconds Current MTTR in seconds
# TYPE selfheal_mttr_current_seconds gauge
selfheal_mttr_current_seconds{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.mttr_current}

# HELP selfheal_mttr_average_seconds Average MTTR in seconds
# TYPE selfheal_mttr_average_seconds gauge
selfheal_mttr_average_seconds{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.mttr_avg}

# HELP selfheal_mttr_p50_seconds 50th percentile MTTR in seconds
# TYPE selfheal_mttr_p50_seconds gauge
selfheal_mttr_p50_seconds{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.mttr_p50}

# HELP selfheal_mttr_p95_seconds 95th percentile MTTR in seconds
# TYPE selfheal_mttr_p95_seconds gauge
selfheal_mttr_p95_seconds{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.mttr_p95}

# HELP selfheal_mttr_p99_seconds 99th percentile MTTR in seconds
# TYPE selfheal_mttr_p99_seconds gauge
selfheal_mttr_p99_seconds{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.mttr_p99}

# HELP selfheal_remediation_attempts_total Total remediation attempts
# TYPE selfheal_remediation_attempts_total counter
selfheal_remediation_attempts_total{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.remediation_attempts}

# HELP selfheal_remediation_successes_total Total successful remediations
# TYPE selfheal_remediation_successes_total counter
selfheal_remediation_successes_total{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.remediation_successes}

# HELP selfheal_remediation_tc_clears_total Total TC netem rule clears
# TYPE selfheal_remediation_tc_clears_total counter
selfheal_remediation_tc_clears_total{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.remediation_tc_clears}

# HELP selfheal_remediation_route_fixes_total Total route fixes
# TYPE selfheal_remediation_route_fixes_total counter
selfheal_remediation_route_fixes_total{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.remediation_route_fixes}

# HELP selfheal_remediation_interface_fixes_total Total interface fixes
# TYPE selfheal_remediation_interface_fixes_total counter
selfheal_remediation_interface_fixes_total{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.remediation_interface_fixes}

# HELP selfheal_check_duration_milliseconds Health check duration in milliseconds
# TYPE selfheal_check_duration_milliseconds gauge
selfheal_check_duration_milliseconds{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.check_duration_ms}

# HELP selfheal_uptime_seconds Agent uptime in seconds
# TYPE selfheal_uptime_seconds gauge
selfheal_uptime_seconds{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {uptime}

# HELP selfheal_last_check_timestamp Last health check timestamp
# TYPE selfheal_last_check_timestamp gauge
selfheal_last_check_timestamp{{device="{DEVICE_NAME}",role="{DEVICE_ROLE}",ip="{DEVICE_IP}"}} {metrics.last_check_timestamp}
"""
        return prometheus_metrics
    
    def log_message(self, format, *args):
        # Suppress default HTTP logging
        pass

def start_metrics_server():
    """Start Prometheus metrics HTTP server in background thread"""
    try:
        server = HTTPServer(('0.0.0.0', METRICS_PORT), MetricsHandler)
        logger.info(f"📊 Metrics server started on port {METRICS_PORT}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")

def main():
    """Main agent loop with enhanced monitoring"""
    logger.info("🚀 Enhanced Self-Healing Network Agent Starting")
    logger.info(f"Configuration: Device={DEVICE_NAME}, Role={DEVICE_ROLE}, IP={DEVICE_IP}")
    logger.info(f"Network: Interface={IFACE}, Gateway={GATEWAY}, Check={CHECK_HOST}:{CHECK_PORT}")
    logger.info(f"Metrics: Port={METRICS_PORT}")
    
    # Start metrics server in background thread
    metrics_thread = threading.Thread(target=start_metrics_server, daemon=True)
    metrics_thread.start()
    
    consecutive_failures = 0
    backoff_sleep = SLEEP_INTERVAL
    max_backoff = 60
    
    while True:
        try:
            # Perform health check
            health = network_health_check()
            
            # Log health status
            status_msg = f"Health: {'✅ HEALTHY' if health['healthy'] else '❌ UNHEALTHY'}"
            if health['healthy']:
                logger.info(status_msg)
                consecutive_failures = 0
                backoff_sleep = SLEEP_INTERVAL
            else:
                logger.warning(status_msg)
                logger.warning(f"Issues: Interface UP={health['interface_up']}, Route={health['default_route']}, "
                             f"Connectivity={health['tcp_connectivity']}, TC Drift={health['tc_drift']}")
                
                # Perform remediation
                remediation = perform_remediation()
                logger.info(f"Remediation completed: {json.dumps(remediation)}")
                
                # Wait a moment and re-check
                time.sleep(2)
                post_health = network_health_check()
                
                if post_health['healthy']:
                    logger.info("✅ Network connectivity restored!")
                    consecutive_failures = 0
                    backoff_sleep = SLEEP_INTERVAL
                else:
                    consecutive_failures += 1
                    logger.error(f"❌ Remediation failed. Consecutive failures: {consecutive_failures}")
                    
                    # Exponential backoff on repeated failures
                    if consecutive_failures > 1:
                        backoff_sleep = min(backoff_sleep * 2, max_backoff)
                        logger.warning(f"Using backoff sleep: {backoff_sleep}s")
            
        except KeyboardInterrupt:
            logger.info("🛑 Agent stopped by user")
            break
        except Exception as e:
            logger.error(f"Agent error: {e}")
            consecutive_failures += 1
        
        time.sleep(backoff_sleep)

if __name__ == "__main__":
    main()
