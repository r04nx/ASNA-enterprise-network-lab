#!/usr/bin/env python3
"""
Smart Autonomous Self-Healing Network Agent
Detects network isolation and autonomously recovers
"""

import os
import subprocess
import time
import json
import socket
import logging
import sys
from datetime import datetime

# Configuration from environment
IFACE = os.environ.get("AGENT_IFACE", "eth0")
GATEWAY = os.environ.get("AGENT_GATEWAY", "172.20.20.1")  
CHECK_HOST = os.environ.get("AGENT_CHECK_HOST", "172.20.20.1")  
CHECK_PORT = int(os.environ.get("AGENT_CHECK_PORT", "80"))
SLEEP_INTERVAL = int(os.environ.get("AGENT_SLEEP", "5"))
LOG_LEVEL = os.environ.get("AGENT_LOG_LEVEL", "INFO")

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - SelfHeal - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_cmd(cmd, timeout=10):
    """Execute shell command with timeout and return result"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            timeout=timeout
        )
        return result
    except subprocess.TimeoutExpired:
        logger.warning(f"Command timeout: {cmd}")
        return None
    except Exception as e:
        logger.error(f"Command failed: {cmd} - {e}")
        return None

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
    result = run_cmd(f"tc qdisc show dev {iface}")
    if result and result.returncode == 0:
        output = result.stdout + result.stderr
        return "netem" in output.lower()
    return False

def interface_is_up(iface):
    """Check if network interface is UP"""
    result = run_cmd(f"ip addr show {iface}")
    if result and result.returncode == 0:
        return "state UP" in result.stdout
    return False

def has_default_route():
    """Check if default route exists"""
    result = run_cmd("ip route show default")
    if result and result.returncode == 0:
        return "default" in result.stdout
    return False

def network_health_check():
    """Comprehensive network health assessment"""
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
    
    return health

def remediate_tc_drift(iface):
    """Remove traffic control netem rules"""
    logger.info(f"Removing TC netem drift from {iface}")
    result = run_cmd(f"tc qdisc del dev {iface} root")
    if result and result.returncode == 0:
        logger.info("Successfully removed TC netem rule")
        return True
    else:
        logger.error(f"Failed to remove TC rule: {result.stderr if result else 'Unknown error'}")
        return False

def remediate_interface(iface):
    """Ensure network interface is UP"""
    logger.info(f"Ensuring interface {iface} is UP")
    result = run_cmd(f"ip link set {iface} up")
    if result and result.returncode == 0:
        logger.info(f"Interface {iface} set to UP")
        return True
    else:
        logger.error(f"Failed to set interface UP: {result.stderr if result else 'Unknown error'}")
        return False

def remediate_default_route(gateway, iface):
    """Restore default route"""
    logger.info(f"Restoring default route via {gateway} dev {iface}")
    result = run_cmd(f"ip route replace default via {gateway} dev {iface}")
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
    
    return {
        'actions_taken': actions_taken,
        'success_count': success_count,
        'timestamp': datetime.utcnow().isoformat()
    }

def main():
    """Main agent loop"""
    logger.info("🚀 Self-Healing Network Agent Starting")
    logger.info(f"Configuration: Interface={IFACE}, Gateway={GATEWAY}, Check={CHECK_HOST}:{CHECK_PORT}")
    
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
