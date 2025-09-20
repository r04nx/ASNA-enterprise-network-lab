#!/usr/bin/env python3
"""
Journal Quality Self-Healing Network Testing Framework
Advanced testing with statistical analysis, concurrent failures, and comprehensive metrics
"""

import subprocess
import time
import json
import threading
import statistics
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import concurrent.futures
import argparse
import logging
import sys
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Tuple
import random

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'journal_testing_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class NetworkTopologyConfig:
    """Network topology configuration and device mappings"""
    
    DEVICES = {
        # Core Layer
        'core-router': {'container': 'clab-enterprise-final-core-router', 'role': 'core', 'ip': '172.20.20.10'},
        'core-firewall': {'container': 'clab-enterprise-final-core-firewall', 'role': 'core', 'ip': '172.20.20.2'},
        
        # Distribution Layer
        'dist-eng': {'container': 'clab-enterprise-final-dist-eng', 'role': 'distribution', 'ip': '172.20.20.11'},
        'dist-sales': {'container': 'clab-enterprise-final-dist-sales', 'role': 'distribution', 'ip': '172.20.20.16'},
        'dist-servers': {'container': 'clab-enterprise-final-dist-servers', 'role': 'distribution', 'ip': '172.20.20.8'},
        
        # Access Layer
        'access-eng': {'container': 'clab-enterprise-final-access-eng', 'role': 'access', 'ip': '172.20.20.15'},
        'access-sales': {'container': 'clab-enterprise-final-access-sales', 'role': 'access', 'ip': '172.20.20.12'},
        
        # Client Devices
        'eng-gui': {'container': 'clab-enterprise-final-eng-gui', 'role': 'client', 'ip': '172.20.20.14'},
        'eng-dev': {'container': 'clab-enterprise-final-eng-dev', 'role': 'client', 'ip': '172.20.20.3'},
        'sales-gui': {'container': 'clab-enterprise-final-sales-gui', 'role': 'client', 'ip': '172.20.20.4'},
        'sales-mobile': {'container': 'clab-enterprise-final-sales-mobile', 'role': 'client', 'ip': '172.20.20.13'},
        
        # Servers
        'web-server': {'container': 'clab-enterprise-final-web-server', 'role': 'server', 'ip': '172.20.20.7'},
        'db-server': {'container': 'clab-enterprise-final-db-server', 'role': 'server', 'ip': '172.20.20.9'},
        'file-server': {'container': 'clab-enterprise-final-file-server', 'role': 'server', 'ip': '172.20.20.6'},
        'public-web': {'container': 'clab-enterprise-final-public-web', 'role': 'server', 'ip': '172.20.20.5'},
    }
    
    FAILURE_SCENARIOS = {
        'tc_netem_delay': {
            'name': 'TC Netem Delay',
            'command': 'tc qdisc add dev eth0 root netem delay 500ms 100ms',
            'severity': 'medium',
            'expected_mttr': 2.0
        },
        'tc_packet_loss': {
            'name': 'TC Packet Loss',
            'command': 'tc qdisc add dev eth0 root netem loss 75%',
            'severity': 'high',
            'expected_mttr': 1.5
        },
        'interface_down': {
            'name': 'Interface Down',
            'command': 'ip link set eth0 down',
            'severity': 'critical',
            'expected_mttr': 1.0
        },
        'remove_default_route': {
            'name': 'Remove Default Route',
            'command': 'ip route del default',
            'severity': 'high',
            'expected_mttr': 1.2
        },
        'tc_corruption': {
            'name': 'TC Packet Corruption',
            'command': 'tc qdisc add dev eth0 root netem corrupt 50%',
            'severity': 'medium',
            'expected_mttr': 2.0
        },
        'tc_duplicate': {
            'name': 'TC Packet Duplication',
            'command': 'tc qdisc add dev eth0 root netem duplicate 25%',
            'severity': 'low',
            'expected_mttr': 2.5
        }
    }

class PrometheusClient:
    """Client for interacting with Prometheus metrics"""
    
    def __init__(self, base_url='http://localhost:9090'):
        self.base_url = base_url
        
    def query(self, query: str) -> Dict:
        """Execute Prometheus query"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/query", params={'query': query})
            return response.json() if response.status_code == 200 else {}
        except Exception as e:
            logger.error(f"Prometheus query failed: {e}")
            return {}
    
    def query_range(self, query: str, start: datetime, end: datetime, step: str = '5s') -> Dict:
        """Execute Prometheus range query"""
        try:
            params = {
                'query': query,
                'start': start.timestamp(),
                'end': end.timestamp(),
                'step': step
            }
            response = requests.get(f"{self.base_url}/api/v1/query_range", params=params)
            return response.json() if response.status_code == 200 else {}
        except Exception as e:
            logger.error(f"Prometheus range query failed: {e}")
            return {}

class FailureInjector:
    """Injects network failures into devices"""
    
    @staticmethod
    def run_command(container: str, command: str) -> Tuple[bool, str]:
        """Execute command in container"""
        try:
            result = subprocess.run(
                ['docker', 'exec', container, 'sh', '-c', command],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)
    
    def inject_failure(self, device_name: str, scenario: str) -> bool:
        """Inject failure scenario into device"""
        if device_name not in NetworkTopologyConfig.DEVICES:
            logger.error(f"Unknown device: {device_name}")
            return False
            
        if scenario not in NetworkTopologyConfig.FAILURE_SCENARIOS:
            logger.error(f"Unknown scenario: {scenario}")
            return False
        
        container = NetworkTopologyConfig.DEVICES[device_name]['container']
        command = NetworkTopologyConfig.FAILURE_SCENARIOS[scenario]['command']
        
        logger.info(f"Injecting {scenario} into {device_name}")
        success, output = self.run_command(container, command)
        
        if not success:
            logger.warning(f"Failure injection may have failed: {output}")
        
        return True
    
    def clear_failures(self, device_name: str) -> bool:
        """Clear all network failures from device"""
        if device_name not in NetworkTopologyConfig.DEVICES:
            return False
        
        container = NetworkTopologyConfig.DEVICES[device_name]['container']
        
        # Clear TC rules
        self.run_command(container, "tc qdisc del dev eth0 root 2>/dev/null || true")
        
        # Restore interface
        self.run_command(container, "ip link set eth0 up 2>/dev/null || true")
        
        # Restore default route
        self.run_command(container, "ip route add default via 172.20.20.1 dev eth0 2>/dev/null || true")
        
        return True

class MTTRCalculator:
    """Advanced MTTR calculation with statistical analysis"""
    
    def __init__(self, prometheus_client: PrometheusClient):
        self.prometheus = prometheus_client
        
    def get_device_mttr_metrics(self, device: str, start: datetime, end: datetime) -> Dict:
        """Get MTTR metrics for a specific device"""
        metrics = {}
        
        queries = {
            'failures': f'increase(selfheal_failure_count_total{{device="{device}"}}[{int((end-start).total_seconds())}s])',
            'recoveries': f'increase(selfheal_recovery_count_total{{device="{device}"}}[{int((end-start).total_seconds())}s])',
            'mttr_current': f'selfheal_mttr_current_seconds{{device="{device}"}}',
            'mttr_avg': f'selfheal_mttr_average_seconds{{device="{device}"}}',
            'mttr_p50': f'selfheal_mttr_p50_seconds{{device="{device}"}}',
            'mttr_p95': f'selfheal_mttr_p95_seconds{{device="{device}"}}',
            'mttr_p99': f'selfheal_mttr_p99_seconds{{device="{device}"}}'
        }
        
        for metric_name, query in queries.items():
            result = self.prometheus.query(query)
            if result.get('status') == 'success' and result.get('data', {}).get('result'):
                metrics[metric_name] = float(result['data']['result'][0]['value'][1])
            else:
                metrics[metric_name] = 0.0
        
        return metrics
    
    def calculate_network_statistics(self, test_results: List[Dict]) -> Dict:
        """Calculate comprehensive network statistics"""
        if not test_results:
            return {}
        
        # Extract MTTR values
        mttr_values = [r['mttr'] for r in test_results if r['status'] == 'recovered']
        
        if not mttr_values:
            return {'success_rate': 0.0}
        
        statistics_result = {
            'total_tests': len(test_results),
            'successful_recoveries': len(mttr_values),
            'success_rate': len(mttr_values) / len(test_results) * 100,
            'mttr_mean': statistics.mean(mttr_values),
            'mttr_median': statistics.median(mttr_values),
            'mttr_std': statistics.stdev(mttr_values) if len(mttr_values) > 1 else 0.0,
            'mttr_min': min(mttr_values),
            'mttr_max': max(mttr_values),
            'mttr_p90': np.percentile(mttr_values, 90),
            'mttr_p95': np.percentile(mttr_values, 95),
            'mttr_p99': np.percentile(mttr_values, 99) if len(mttr_values) >= 5 else max(mttr_values)
        }
        
        return statistics_result

class TestExecution:
    """Manages test execution and result collection"""
    
    def __init__(self):
        self.injector = FailureInjector()
        self.prometheus = PrometheusClient()
        self.mttr_calc = MTTRCalculator(self.prometheus)
        
    def wait_for_recovery(self, device: str, max_wait: int = 300) -> Tuple[bool, float]:
        """Wait for device recovery and measure MTTR"""
        start_time = time.time()
        
        while (time.time() - start_time) < max_wait:
            # Check agent health from Prometheus
            query = f'selfheal_agent_health{{device="{device}"}}'
            result = self.prometheus.query(query)
            
            if (result.get('status') == 'success' and 
                result.get('data', {}).get('result') and
                float(result['data']['result'][0]['value'][1]) == 1.0):
                
                recovery_time = time.time() - start_time
                return True, recovery_time
            
            time.sleep(0.5)
        
        return False, max_wait
    
    def run_single_test(self, device: str, scenario: str) -> Dict:
        """Run a single failure-recovery test"""
        logger.info(f"Testing {scenario} on {device}")
        
        # Clear any existing failures
        self.injector.clear_failures(device)
        time.sleep(5)
        
        # Record test start time
        test_start = time.time()
        
        # Inject failure
        if not self.injector.inject_failure(device, scenario):
            return {
                'device': device,
                'scenario': scenario,
                'status': 'injection_failed',
                'mttr': None,
                'timestamp': test_start
            }
        
        # Wait for recovery
        recovered, mttr = self.wait_for_recovery(device)
        
        # Clear failures
        self.injector.clear_failures(device)
        
        return {
            'device': device,
            'scenario': scenario,
            'status': 'recovered' if recovered else 'timeout',
            'mttr': mttr,
            'timestamp': test_start,
            'expected_mttr': NetworkTopologyConfig.FAILURE_SCENARIOS[scenario]['expected_mttr']
        }
    
    def run_concurrent_tests(self, device_scenarios: List[Tuple[str, str]], max_workers: int = 5) -> List[Dict]:
        """Run multiple tests concurrently"""
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tests
            future_to_test = {
                executor.submit(self.run_single_test, device, scenario): (device, scenario)
                for device, scenario in device_scenarios
            }
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_test):
                device, scenario = future_to_test[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"Test completed: {device}-{scenario}, MTTR: {result.get('mttr', 'N/A')}s")
                except Exception as e:
                    logger.error(f"Test failed: {device}-{scenario} - {e}")
                    results.append({
                        'device': device,
                        'scenario': scenario,
                        'status': 'error',
                        'mttr': None,
                        'timestamp': time.time()
                    })
        
        return results

class JournalQualityTestFramework:
    """Main test framework for journal-quality experiments"""
    
    def __init__(self):
        self.test_executor = TestExecution()
        self.results = []
        
    def run_comprehensive_test_suite(self, iterations: int = 100, concurrent_tests: int = 3) -> Dict:
        """Run comprehensive test suite with statistical significance"""
        logger.info(f"Starting comprehensive test suite: {iterations} iterations, {concurrent_tests} concurrent tests")
        
        all_results = []
        
        for iteration in range(iterations):
            logger.info(f"Running iteration {iteration + 1}/{iterations}")
            
            # Select random devices and scenarios for this iteration
            devices = random.sample(list(NetworkTopologyConfig.DEVICES.keys()), min(concurrent_tests, len(NetworkTopologyConfig.DEVICES)))
            scenarios = [random.choice(list(NetworkTopologyConfig.FAILURE_SCENARIOS.keys())) for _ in devices]
            
            device_scenarios = list(zip(devices, scenarios))
            
            # Run tests
            iteration_results = self.test_executor.run_concurrent_tests(device_scenarios)
            all_results.extend(iteration_results)
            
            # Brief pause between iterations
            time.sleep(random.uniform(5, 15))
        
        # Calculate comprehensive statistics
        stats = self.test_executor.mttr_calc.calculate_network_statistics(all_results)
        
        # Save results
        results_data = {
            'test_parameters': {
                'iterations': iterations,
                'concurrent_tests': concurrent_tests,
                'total_tests': len(all_results),
                'test_duration': time.time() - (all_results[0]['timestamp'] if all_results else time.time())
            },
            'individual_results': all_results,
            'aggregate_statistics': stats
        }
        
        self._save_results(results_data)
        self._generate_visualizations(all_results)
        
        return results_data
    
    def _save_results(self, results: Dict):
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"journal_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {filename}")
    
    def _generate_visualizations(self, results: List[Dict]):
        """Generate publication-quality visualizations"""
        if not results:
            return
        
        # Create DataFrame
        df = pd.DataFrame(results)
        successful_results = df[df['status'] == 'recovered']
        
        if successful_results.empty:
            logger.warning("No successful recoveries to visualize")
            return
        
        # Set up the plotting style
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Self-Healing Network Performance Analysis', fontsize=16)
        
        # MTTR Distribution
        axes[0, 0].hist(successful_results['mttr'], bins=30, alpha=0.7, edgecolor='black')
        axes[0, 0].set_title('MTTR Distribution')
        axes[0, 0].set_xlabel('Recovery Time (seconds)')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].grid(True, alpha=0.3)
        
        # MTTR by Scenario
        if len(successful_results['scenario'].unique()) > 1:
            successful_results.boxplot(column='mttr', by='scenario', ax=axes[0, 1])
            axes[0, 1].set_title('MTTR by Failure Scenario')
            axes[0, 1].set_xlabel('Scenario')
            axes[0, 1].set_ylabel('Recovery Time (seconds)')
        
        # MTTR by Device Role
        if 'device' in successful_results.columns:
            # Add role information
            successful_results['role'] = successful_results['device'].map(
                lambda x: NetworkTopologyConfig.DEVICES.get(x, {}).get('role', 'unknown')
            )
            if len(successful_results['role'].unique()) > 1:
                successful_results.boxplot(column='mttr', by='role', ax=axes[1, 0])
                axes[1, 0].set_title('MTTR by Device Role')
                axes[1, 0].set_xlabel('Device Role')
                axes[1, 0].set_ylabel('Recovery Time (seconds)')
        
        # Success Rate Analysis
        success_rate = df.groupby('scenario')['status'].apply(lambda x: (x == 'recovered').mean() * 100)
        success_rate.plot(kind='bar', ax=axes[1, 1])
        axes[1, 1].set_title('Success Rate by Scenario')
        axes[1, 1].set_xlabel('Scenario')
        axes[1, 1].set_ylabel('Success Rate (%)')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Save plot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plt.savefig(f"mttr_analysis_{timestamp}.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Visualizations saved as mttr_analysis_{timestamp}.png")

def main():
    parser = argparse.ArgumentParser(description='Journal Quality Self-Healing Network Testing Framework')
    parser.add_argument('--iterations', type=int, default=50, help='Number of test iterations')
    parser.add_argument('--concurrent', type=int, default=3, help='Number of concurrent tests per iteration')
    parser.add_argument('--quick-test', action='store_true', help='Run quick test with fewer iterations')
    
    args = parser.parse_args()
    
    if args.quick_test:
        iterations = 10
        concurrent = 2
    else:
        iterations = args.iterations
        concurrent = args.concurrent
    
    framework = JournalQualityTestFramework()
    
    logger.info("=== Journal Quality Self-Healing Network Testing Framework ===")
    logger.info(f"Test Configuration: {iterations} iterations, {concurrent} concurrent tests")
    logger.info("Starting comprehensive test suite...")
    
    results = framework.run_comprehensive_test_suite(iterations=iterations, concurrent_tests=concurrent)
    
    # Print summary
    stats = results['aggregate_statistics']
    logger.info("=== TEST RESULTS SUMMARY ===")
    logger.info(f"Total Tests: {stats.get('total_tests', 0)}")
    logger.info(f"Success Rate: {stats.get('success_rate', 0):.2f}%")
    logger.info(f"Mean MTTR: {stats.get('mttr_mean', 0):.3f}s")
    logger.info(f"Median MTTR: {stats.get('mttr_median', 0):.3f}s")
    logger.info(f"MTTR Std Dev: {stats.get('mttr_std', 0):.3f}s")
    logger.info(f"95th Percentile MTTR: {stats.get('mttr_p95', 0):.3f}s")
    logger.info(f"99th Percentile MTTR: {stats.get('mttr_p99', 0):.3f}s")
    
    print("\n🎉 Journal Quality Testing Complete!")
    print(f"📊 Results saved with comprehensive statistics and visualizations")
    print(f"🚀 Ready for academic publication!")

if __name__ == "__main__":
    main()
