#!/usr/bin/env python3
"""
Quick test to verify the journal paper testing framework
Runs 2 scenarios with 2 iterations each to validate setup
"""

import subprocess
import time
import requests
import json
from datetime import datetime

def test_prometheus_connection():
    """Verify Prometheus is accessible"""
    try:
        response = requests.get("http://localhost:9090/api/v1/query?query=up", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print("✅ Prometheus connection verified")
                return True
    except Exception as e:
        print(f"❌ Prometheus connection failed: {e}")
        return False

def test_selfhealing_metrics():
    """Verify self-healing metrics are available"""
    try:
        response = requests.get("http://localhost:9090/api/v1/query?query=selfheal_agent_health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success' and data.get('data', {}).get('result'):
                agent_count = len(data['data']['result'])
                print(f"✅ Self-healing metrics verified - {agent_count} agents found")
                return agent_count >= 10  # Should have most agents
    except Exception as e:
        print(f"❌ Self-healing metrics test failed: {e}")
        return False

def run_quick_failure_test():
    """Run a quick failure injection to test the system"""
    print("🧪 Running quick failure test on eng-gui...")
    
    # Inject TC delay
    result = subprocess.run([
        'docker', 'exec', 'clab-enterprise-final-eng-gui', 
        'tc', 'qdisc', 'add', 'dev', 'eth0', 'root', 'netem', 'delay', '200ms'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failure injection failed: {result.stderr}")
        return False
    
    print("✅ Failure injected successfully")
    
    # Wait for recovery
    print("⏱️  Waiting for recovery (max 15s)...")
    start_time = time.time()
    
    for i in range(30):  # 15 seconds with 0.5s intervals
        try:
            response = requests.get('http://localhost:9090/api/v1/query?query=selfheal_agent_health{device="eng-gui"}', timeout=2)
            if response.status_code == 200:
                data = response.json()
                if (data.get('status') == 'success' and 
                    data.get('data', {}).get('result') and
                    float(data['data']['result'][0]['value'][1]) == 1.0):
                    recovery_time = time.time() - start_time
                    print(f"✅ Recovery detected after {recovery_time:.2f}s")
                    
                    # Cleanup
                    subprocess.run([
                        'docker', 'exec', 'clab-enterprise-final-eng-gui',
                        'tc', 'qdisc', 'del', 'dev', 'eth0', 'root'
                    ], capture_output=True)
                    
                    return True
        except Exception as e:
            print(f"⚠️  Query error: {e}")
        
        time.sleep(0.5)
    
    print("❌ Recovery not detected within 15s")
    # Cleanup anyway
    subprocess.run([
        'docker', 'exec', 'clab-enterprise-final-eng-gui',
        'tc', 'qdisc', 'del', 'dev', 'eth0', 'root'
    ], capture_output=True)
    
    return False

def main():
    print("🔍 Quick Paper Test - Validating Journal Test Framework")
    print("=" * 55)
    
    # Test 1: Prometheus connectivity
    if not test_prometheus_connection():
        print("❌ Cannot proceed - Prometheus not accessible")
        return False
    
    # Test 2: Self-healing metrics
    if not test_selfhealing_metrics():
        print("❌ Cannot proceed - Self-healing metrics not available")
        return False
    
    # Test 3: Failure injection and recovery
    if not run_quick_failure_test():
        print("❌ Cannot proceed - Failure recovery test failed")
        return False
    
    print("\n✅ All validation tests passed!")
    print("🚀 System is ready for journal paper data collection")
    print("\n📋 To run the full journal paper test suite:")
    print("   python3 journal_paper_scenarios.py")
    print("\n💡 Recommended settings for paper:")
    print("   - 5-10 iterations per scenario (reliable results)")
    print("   - Expected duration: 30-60 minutes")
    print("   - Will generate publication-ready graphs and statistics")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
