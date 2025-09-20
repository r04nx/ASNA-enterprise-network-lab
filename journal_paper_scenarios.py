#!/usr/bin/env python3
"""
Journal Paper Test Scenarios for Self-Healing Network Research
Comprehensive testing framework for academic publication
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
import logging
import sys
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Tuple
import random
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'paper_testing_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class NetworkTopology:
    """Network topology configuration for journal paper testing"""
    
    DEVICES = {
        # Core Layer - Critical Infrastructure
        'core-router': {'container': 'clab-enterprise-final-core-router', 'role': 'core', 'ip': '172.20.20.10', 'criticality': 'critical'},
        'core-firewall': {'container': 'clab-enterprise-final-core-firewall', 'role': 'core', 'ip': '172.20.20.2', 'criticality': 'critical'},
        
        # Distribution Layer - High Importance
        'dist-eng': {'container': 'clab-enterprise-final-dist-eng', 'role': 'distribution', 'ip': '172.20.20.11', 'criticality': 'high'},
        'dist-sales': {'container': 'clab-enterprise-final-dist-sales', 'role': 'distribution', 'ip': '172.20.20.16', 'criticality': 'high'},
        'dist-servers': {'container': 'clab-enterprise-final-dist-servers', 'role': 'distribution', 'ip': '172.20.20.8', 'criticality': 'high'},
        
        # Access Layer - Medium Importance
        'access-eng': {'container': 'clab-enterprise-final-access-eng', 'role': 'access', 'ip': '172.20.20.15', 'criticality': 'medium'},
        'access-sales': {'container': 'clab-enterprise-final-access-sales', 'role': 'access', 'ip': '172.20.20.12', 'criticality': 'medium'},
        
        # Client Devices - Low-Medium Importance
        'eng-gui': {'container': 'clab-enterprise-final-eng-gui', 'role': 'client', 'ip': '172.20.20.14', 'criticality': 'medium'},
        'eng-dev': {'container': 'clab-enterprise-final-eng-dev', 'role': 'client', 'ip': '172.20.20.3', 'criticality': 'low'},
        'sales-gui': {'container': 'clab-enterprise-final-sales-gui', 'role': 'client', 'ip': '172.20.20.4', 'criticality': 'medium'},
        'sales-mobile': {'container': 'clab-enterprise-final-sales-mobile', 'role': 'client', 'ip': '172.20.20.13', 'criticality': 'low'},
        
        # Servers - High Importance
        'web-server': {'container': 'clab-enterprise-final-web-server', 'role': 'server', 'ip': '172.20.20.7', 'criticality': 'high'},
        'db-server': {'container': 'clab-enterprise-final-db-server', 'role': 'server', 'ip': '172.20.20.9', 'criticality': 'critical'},
        'file-server': {'container': 'clab-enterprise-final-file-server', 'role': 'server', 'ip': '172.20.20.6', 'criticality': 'medium'},
        'public-web': {'container': 'clab-enterprise-final-public-web', 'role': 'server', 'ip': '172.20.20.5', 'criticality': 'high'},
    }
    
    # Journal Paper Test Scenarios
    PAPER_SCENARIOS = {
        # Scenario 1: Lightweight Network Degradation
        'light_delay': {
            'name': 'Light Network Delay',
            'command': 'tc qdisc add dev eth0 root netem delay 100ms 20ms',
            'severity': 'light',
            'expected_mttr_range': (0.5, 2.0),
            'paper_category': 'Performance Degradation',
            'description': 'Simulates minor network congestion'
        },
        
        # Scenario 2: Moderate Network Issues
        'moderate_delay': {
            'name': 'Moderate Network Delay', 
            'command': 'tc qdisc add dev eth0 root netem delay 300ms 50ms',
            'severity': 'moderate',
            'expected_mttr_range': (1.0, 3.0),
            'paper_category': 'Performance Degradation',
            'description': 'Simulates moderate network congestion'
        },
        
        # Scenario 3: High Packet Loss
        'packet_loss_high': {
            'name': 'High Packet Loss',
            'command': 'tc qdisc add dev eth0 root netem loss 40%',
            'severity': 'high',
            'expected_mttr_range': (1.0, 2.5),
            'paper_category': 'Connectivity Loss',
            'description': 'Simulates significant packet loss'
        },
        
        # Scenario 4: Severe Network Issues
        'severe_delay': {
            'name': 'Severe Network Delay',
            'command': 'tc qdisc add dev eth0 root netem delay 800ms 100ms',
            'severity': 'severe',
            'expected_mttr_range': (1.5, 4.0),
            'paper_category': 'Performance Degradation',
            'description': 'Simulates severe network congestion'
        },
        
        # Scenario 5: Complete Interface Failure
        'interface_down': {
            'name': 'Interface Failure',
            'command': 'ip link set eth0 down',
            'severity': 'critical',
            'expected_mttr_range': (0.5, 1.5),
            'paper_category': 'Hardware Failure',
            'description': 'Simulates complete interface failure'
        },
        
        # Scenario 6: Routing Table Corruption
        'route_removal': {
            'name': 'Routing Failure',
            'command': 'ip route del default',
            'severity': 'high',
            'expected_mttr_range': (0.8, 2.0),
            'paper_category': 'Configuration Drift',
            'description': 'Simulates routing table corruption'
        },
        
        # Scenario 7: Packet Corruption
        'packet_corruption': {
            'name': 'Packet Corruption',
            'command': 'tc qdisc add dev eth0 root netem corrupt 30%',
            'severity': 'moderate',
            'expected_mttr_range': (1.0, 2.5),
            'paper_category': 'Data Integrity',
            'description': 'Simulates packet corruption'
        },
        
        # Scenario 8: Extreme Packet Loss
        'packet_loss_extreme': {
            'name': 'Extreme Packet Loss', 
            'command': 'tc qdisc add dev eth0 root netem loss 80%',
            'severity': 'critical',
            'expected_mttr_range': (1.0, 2.0),
            'paper_category': 'Connectivity Loss',
            'description': 'Simulates near-total connectivity loss'
        }
    }

class PrometheusClient:
    """Enhanced Prometheus client for research data collection"""
    
    def __init__(self, base_url='http://localhost:9090'):
        self.base_url = base_url
        
    def query_with_retry(self, query: str, retries=3) -> Dict:
        """Query with retry logic for reliability"""
        for attempt in range(retries):
            try:
                response = requests.get(f"{self.base_url}/api/v1/query", params={'query': query}, timeout=10)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                if attempt == retries - 1:
                    logger.error(f"Prometheus query failed after {retries} attempts: {e}")
                    return {}
                time.sleep(1)
        return {}

class FailureInjector:
    """Advanced failure injection for research scenarios"""
    
    @staticmethod
    def run_command_with_timeout(container: str, command: str, timeout=15) -> Tuple[bool, str]:
        """Execute command with extended timeout for complex operations"""
        try:
            result = subprocess.run(
                ['docker', 'exec', container, 'sh', '-c', command],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            logger.warning(f"Command timeout after {timeout}s: {command}")
            return False, f"Timeout after {timeout}s"
        except Exception as e:
            return False, str(e)
    
    def inject_scenario(self, device_name: str, scenario_key: str) -> bool:
        """Inject specific research scenario"""
        if device_name not in NetworkTopology.DEVICES:
            logger.error(f"Unknown device: {device_name}")
            return False
            
        if scenario_key not in NetworkTopology.PAPER_SCENARIOS:
            logger.error(f"Unknown scenario: {scenario_key}")
            return False
        
        container = NetworkTopology.DEVICES[device_name]['container']
        scenario = NetworkTopology.PAPER_SCENARIOS[scenario_key]
        command = scenario['command']
        
        logger.info(f"Injecting {scenario['name']} into {device_name}")
        success, output = self.run_command_with_timeout(container, command)
        
        if not success:
            logger.warning(f"Scenario injection warning: {output}")
        
        return True
    
    def clear_all_issues(self, device_name: str) -> bool:
        """Comprehensive cleanup for research reliability"""
        if device_name not in NetworkTopology.DEVICES:
            return False
        
        container = NetworkTopology.DEVICES[device_name]['container']
        
        # Comprehensive cleanup commands
        cleanup_commands = [
            "tc qdisc del dev eth0 root 2>/dev/null || true",
            "ip link set eth0 up 2>/dev/null || true", 
            "ip route del default 2>/dev/null || true",
            "ip route add default via 172.20.20.1 dev eth0 2>/dev/null || true"
        ]
        
        success_count = 0
        for cmd in cleanup_commands:
            success, _ = self.run_command_with_timeout(container, cmd, timeout=5)
            if success:
                success_count += 1
        
        return success_count >= 2  # At least partial success

class ResearchDataCollector:
    """Collects and analyzes data for journal paper"""
    
    def __init__(self):
        self.prometheus = PrometheusClient()
        self.injector = FailureInjector()
        
    def wait_for_recovery_with_monitoring(self, device: str, max_wait: int = 300) -> Tuple[bool, float, Dict]:
        """Enhanced recovery monitoring with detailed metrics"""
        start_time = time.time()
        metrics_timeline = []
        
        while (time.time() - start_time) < max_wait:
            current_time = time.time()
            
            # Collect comprehensive metrics
            queries = {
                'agent_health': f'selfheal_agent_health{{device="{device}"}}',
                'connectivity': f'selfheal_network_connectivity{{device="{device}"}}', 
                'interface_status': f'selfheal_interface_status{{device="{device}"}}',
                'route_status': f'selfheal_default_route_status{{device="{device}"}}',
                'tc_drift': f'selfheal_tc_drift_detected{{device="{device}"}}'
            }
            
            current_metrics = {'timestamp': current_time}
            agent_healthy = False
            
            for metric_name, query in queries.items():
                result = self.prometheus.query_with_retry(query)
                if (result.get('status') == 'success' and 
                    result.get('data', {}).get('result')):
                    value = float(result['data']['result'][0]['value'][1])
                    current_metrics[metric_name] = value
                    if metric_name == 'agent_health' and value == 1.0:
                        agent_healthy = True
                else:
                    current_metrics[metric_name] = 0
            
            metrics_timeline.append(current_metrics)
            
            # Check for recovery
            if agent_healthy:
                recovery_time = current_time - start_time
                logger.info(f"Recovery detected for {device} after {recovery_time:.3f}s")
                return True, recovery_time, {
                    'recovered': True,
                    'timeline': metrics_timeline,
                    'recovery_time': recovery_time
                }
            
            time.sleep(0.5)
        
        # Timeout case
        return False, max_wait, {
            'recovered': False,
            'timeline': metrics_timeline,
            'recovery_time': max_wait
        }
    
    def run_single_research_test(self, device: str, scenario_key: str, test_id: int) -> Dict:
        """Single test with comprehensive data collection"""
        logger.info(f"Research Test #{test_id}: {scenario_key} on {device}")
        
        # Pre-test cleanup
        self.injector.clear_all_issues(device)
        time.sleep(3)
        
        # Record baseline metrics
        baseline_time = time.time()
        scenario = NetworkTopology.PAPER_SCENARIOS[scenario_key]
        device_info = NetworkTopology.DEVICES[device]
        
        # Inject failure
        injection_start = time.time()
        if not self.injector.inject_scenario(device, scenario_key):
            return {
                'test_id': test_id,
                'device': device,
                'scenario': scenario_key,
                'status': 'injection_failed',
                'timestamp': baseline_time
            }
        
        injection_duration = time.time() - injection_start
        
        # Monitor recovery
        recovered, mttr, monitoring_data = self.wait_for_recovery_with_monitoring(device)
        
        # Post-test cleanup
        self.injector.clear_all_issues(device)
        
        # Collect final metrics
        final_queries = {
            'total_failures': f'selfheal_failure_count_total{{device="{device}"}}',
            'total_recoveries': f'selfheal_recovery_count_total{{device="{device}"}}',
            'current_mttr': f'selfheal_mttr_current_seconds{{device="{device}"}}',
            'avg_mttr': f'selfheal_mttr_average_seconds{{device="{device}"}}'
        }
        
        final_metrics = {}
        for metric_name, query in final_queries.items():
            result = self.prometheus.query_with_retry(query)
            if (result.get('status') == 'success' and 
                result.get('data', {}).get('result')):
                final_metrics[metric_name] = float(result['data']['result'][0]['value'][1])
            else:
                final_metrics[metric_name] = 0
        
        return {
            'test_id': test_id,
            'device': device,
            'device_role': device_info['role'],
            'device_criticality': device_info['criticality'],
            'scenario': scenario_key,
            'scenario_name': scenario['name'],
            'scenario_severity': scenario['severity'],
            'scenario_category': scenario['paper_category'],
            'status': 'recovered' if recovered else 'timeout',
            'mttr': mttr,
            'expected_mttr_min': scenario['expected_mttr_range'][0],
            'expected_mttr_max': scenario['expected_mttr_range'][1],
            'injection_duration': injection_duration,
            'baseline_timestamp': baseline_time,
            'monitoring_data': monitoring_data,
            'final_metrics': final_metrics,
            'within_expected_range': (
                scenario['expected_mttr_range'][0] <= mttr <= scenario['expected_mttr_range'][1] 
                if recovered else False
            )
        }

class JournalPaperTestSuite:
    """Main test suite for journal paper data collection"""
    
    def __init__(self):
        self.data_collector = ResearchDataCollector()
        self.results_dir = f"journal_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(self.results_dir, exist_ok=True)
        
    def run_comprehensive_research_tests(self, iterations_per_scenario=10) -> Dict:
        """Run comprehensive test suite for journal paper"""
        logger.info(f"Starting Journal Paper Test Suite - {iterations_per_scenario} iterations per scenario")
        
        all_results = []
        test_id = 1
        
        # Test all scenarios across different device types
        device_categories = {
            'critical': ['core-router', 'core-firewall', 'db-server'],
            'high': ['dist-eng', 'dist-sales', 'dist-servers', 'web-server', 'public-web'],
            'medium': ['access-eng', 'access-sales', 'eng-gui', 'file-server'],
            'low': ['eng-dev', 'sales-mobile']
        }
        
        for scenario_key in NetworkTopology.PAPER_SCENARIOS:
            scenario = NetworkTopology.PAPER_SCENARIOS[scenario_key]
            logger.info(f"\n=== Testing Scenario: {scenario['name']} ===")
            
            for iteration in range(iterations_per_scenario):
                # Select devices from different criticality levels
                for criticality, devices in device_categories.items():
                    # Test on one device from each criticality level per iteration
                    device = random.choice(devices)
                    
                    logger.info(f"Iteration {iteration+1}/{iterations_per_scenario}, Testing {device} ({criticality})")
                    
                    result = self.data_collector.run_single_research_test(device, scenario_key, test_id)
                    all_results.append(result)
                    test_id += 1
                    
                    # Brief pause between tests
                    time.sleep(random.uniform(3, 8))
                
                # Longer pause between iterations
                logger.info(f"Completed iteration {iteration+1}/{iterations_per_scenario} for {scenario['name']}")
                time.sleep(random.uniform(10, 20))
        
        # Process and analyze results
        analysis = self._analyze_results(all_results)
        
        # Save comprehensive results
        results_data = {
            'test_metadata': {
                'start_time': datetime.now().isoformat(),
                'total_tests': len(all_results),
                'iterations_per_scenario': iterations_per_scenario,
                'scenarios_tested': len(NetworkTopology.PAPER_SCENARIOS),
                'devices_involved': len(NetworkTopology.DEVICES),
                'test_duration_seconds': time.time() - (all_results[0]['baseline_timestamp'] if all_results else time.time())
            },
            'individual_results': all_results,
            'statistical_analysis': analysis,
            'scenarios_summary': NetworkTopology.PAPER_SCENARIOS
        }
        
        self._save_results(results_data)
        self._generate_paper_visualizations(all_results, analysis)
        
        return results_data
    
    def _analyze_results(self, results: List[Dict]) -> Dict:
        """Comprehensive statistical analysis for journal paper"""
        successful_results = [r for r in results if r['status'] == 'recovered']
        
        if not successful_results:
            return {'error': 'No successful recoveries to analyze'}
        
        # Basic statistics
        mttr_values = [r['mttr'] for r in successful_results]
        
        basic_stats = {
            'total_tests': len(results),
            'successful_recoveries': len(successful_results),
            'success_rate': len(successful_results) / len(results) * 100,
            'mttr_mean': np.mean(mttr_values),
            'mttr_median': np.median(mttr_values),
            'mttr_std': np.std(mttr_values),
            'mttr_min': np.min(mttr_values),
            'mttr_max': np.max(mttr_values),
            'mttr_p90': np.percentile(mttr_values, 90),
            'mttr_p95': np.percentile(mttr_values, 95),
            'mttr_p99': np.percentile(mttr_values, 99)
        }
        
        # Analysis by scenario
        scenario_analysis = {}
        for scenario_key in NetworkTopology.PAPER_SCENARIOS:
            scenario_results = [r for r in successful_results if r['scenario'] == scenario_key]
            if scenario_results:
                scenario_mttrs = [r['mttr'] for r in scenario_results]
                scenario_analysis[scenario_key] = {
                    'count': len(scenario_results),
                    'success_rate': len(scenario_results) / len([r for r in results if r['scenario'] == scenario_key]) * 100,
                    'mttr_mean': np.mean(scenario_mttrs),
                    'mttr_std': np.std(scenario_mttrs),
                    'mttr_min': np.min(scenario_mttrs),
                    'mttr_max': np.max(scenario_mttrs),
                    'within_expected_range': len([r for r in scenario_results if r['within_expected_range']]) / len(scenario_results) * 100
                }
        
        # Analysis by device role
        role_analysis = {}
        for role in ['core', 'distribution', 'access', 'client', 'server']:
            role_results = [r for r in successful_results if r['device_role'] == role]
            if role_results:
                role_mttrs = [r['mttr'] for r in role_results]
                role_analysis[role] = {
                    'count': len(role_results),
                    'mttr_mean': np.mean(role_mttrs),
                    'mttr_std': np.std(role_mttrs),
                    'success_rate': len(role_results) / len([r for r in results if r['device_role'] == role]) * 100
                }
        
        # Analysis by criticality
        criticality_analysis = {}
        for criticality in ['critical', 'high', 'medium', 'low']:
            crit_results = [r for r in successful_results if r['device_criticality'] == criticality]
            if crit_results:
                crit_mttrs = [r['mttr'] for r in crit_results]
                criticality_analysis[criticality] = {
                    'count': len(crit_results),
                    'mttr_mean': np.mean(crit_mttrs),
                    'mttr_std': np.std(crit_mttrs),
                    'success_rate': len(crit_results) / len([r for r in results if r['device_criticality'] == criticality]) * 100
                }
        
        return {
            'basic_statistics': basic_stats,
            'scenario_analysis': scenario_analysis,
            'role_analysis': role_analysis,
            'criticality_analysis': criticality_analysis
        }
    
    def _save_results(self, results: Dict):
        """Save comprehensive results for journal paper"""
        # Main results file
        with open(f'{self.results_dir}/comprehensive_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # CSV for statistical analysis
        df = pd.DataFrame(results['individual_results'])
        df.to_csv(f'{self.results_dir}/test_results.csv', index=False)
        
        # Summary statistics
        with open(f'{self.results_dir}/statistical_summary.json', 'w') as f:
            json.dump(results['statistical_analysis'], f, indent=2)
        
        logger.info(f"Results saved to {self.results_dir}/")
    
    def _generate_paper_visualizations(self, results: List[Dict], analysis: Dict):
        """Generate publication-quality visualizations"""
        successful_results = [r for r in results if r['status'] == 'recovered']
        df = pd.DataFrame(successful_results)
        
        if df.empty:
            logger.warning("No successful results to visualize")
            return
        
        # Set publication style
        plt.style.use('seaborn-v0_8-paper')
        sns.set_palette("husl")
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Self-Healing Network Performance Analysis - Journal Paper Results', fontsize=16)
        
        # 1. MTTR Distribution
        axes[0,0].hist(df['mttr'], bins=30, alpha=0.7, edgecolor='black')
        axes[0,0].set_title('MTTR Distribution')
        axes[0,0].set_xlabel('Recovery Time (seconds)')
        axes[0,0].set_ylabel('Frequency')
        axes[0,0].grid(True, alpha=0.3)
        
        # 2. MTTR by Scenario
        df.boxplot(column='mttr', by='scenario_name', ax=axes[0,1])
        axes[0,1].set_title('MTTR by Failure Scenario')
        axes[0,1].set_xlabel('Scenario')
        axes[0,1].set_ylabel('Recovery Time (seconds)')
        axes[0,1].tick_params(axis='x', rotation=45)
        
        # 3. MTTR by Device Role
        df.boxplot(column='mttr', by='device_role', ax=axes[0,2])
        axes[0,2].set_title('MTTR by Network Layer')
        axes[0,2].set_xlabel('Network Layer')
        axes[0,2].set_ylabel('Recovery Time (seconds)')
        
        # 4. Success Rate by Scenario
        scenario_success = df.groupby('scenario_name').size()
        scenario_total = pd.DataFrame(results).groupby('scenario_name').size()
        success_rates = (scenario_success / scenario_total * 100).fillna(0)
        success_rates.plot(kind='bar', ax=axes[1,0])
        axes[1,0].set_title('Success Rate by Scenario')
        axes[1,0].set_xlabel('Scenario')
        axes[1,0].set_ylabel('Success Rate (%)')
        axes[1,0].tick_params(axis='x', rotation=45)
        
        # 5. MTTR by Criticality Level
        df.boxplot(column='mttr', by='device_criticality', ax=axes[1,1])
        axes[1,1].set_title('MTTR by Device Criticality')
        axes[1,1].set_xlabel('Criticality Level')
        axes[1,1].set_ylabel('Recovery Time (seconds)')
        
        # 6. Performance vs Expected Range
        within_range = df['within_expected_range'].sum()
        total_tests = len(df)
        categories = ['Within Expected Range', 'Outside Expected Range']
        values = [within_range, total_tests - within_range]
        axes[1,2].pie(values, labels=categories, autopct='%1.1f%%')
        axes[1,2].set_title('Performance vs Expected Range')
        
        plt.tight_layout()
        plt.savefig(f'{self.results_dir}/journal_paper_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Generate detailed scenario comparison chart
        self._generate_scenario_comparison(df)
        
        logger.info(f"Visualizations saved to {self.results_dir}/")
    
    def _generate_scenario_comparison(self, df: pd.DataFrame):
        """Generate detailed scenario comparison for paper"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Group by scenario and calculate statistics
        scenario_stats = df.groupby('scenario_name')['mttr'].agg(['mean', 'std', 'count']).reset_index()
        
        # Create bar plot with error bars
        bars = ax.bar(scenario_stats['scenario_name'], scenario_stats['mean'], 
                     yerr=scenario_stats['std'], capsize=5, alpha=0.7)
        
        # Add count annotations
        for i, (bar, count) in enumerate(zip(bars, scenario_stats['count'])):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + scenario_stats['std'][i] + 0.1,
                   f'n={count}', ha='center', va='bottom', fontsize=10)
        
        ax.set_title('Mean Time To Recovery by Failure Scenario\n(with Standard Deviation)', fontsize=14)
        ax.set_xlabel('Failure Scenario', fontsize=12)
        ax.set_ylabel('MTTR (seconds)', fontsize=12)
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.results_dir}/scenario_comparison_detailed.png', dpi=300, bbox_inches='tight')
        plt.close()

def main():
    """Main execution function for journal paper testing"""
    print("🎓 Journal Paper Test Suite for Self-Healing Networks")
    print("=" * 60)
    
    iterations = int(input("Enter number of iterations per scenario (recommended 5-10 for paper): ") or "5")
    
    test_suite = JournalPaperTestSuite()
    
    print(f"\nStarting comprehensive test suite with {iterations} iterations per scenario...")
    print("This will test all 8 failure scenarios across different network layers")
    print("Expected duration: 30-60 minutes\n")
    
    start_time = time.time()
    results = test_suite.run_comprehensive_research_tests(iterations_per_scenario=iterations)
    duration = time.time() - start_time
    
    # Print summary for paper
    stats = results['statistical_analysis']['basic_statistics']
    print("\n" + "=" * 60)
    print("📊 JOURNAL PAPER RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total Tests Conducted: {stats['total_tests']}")
    print(f"Successful Recoveries: {stats['successful_recoveries']}")
    print(f"Overall Success Rate: {stats['success_rate']:.2f}%")
    print(f"Mean MTTR: {stats['mttr_mean']:.3f}s")
    print(f"Median MTTR: {stats['mttr_median']:.3f}s")
    print(f"MTTR Standard Deviation: {stats['mttr_std']:.3f}s")
    print(f"95th Percentile MTTR: {stats['mttr_p95']:.3f}s")
    print(f"99th Percentile MTTR: {stats['mttr_p99']:.3f}s")
    print(f"Test Duration: {duration/60:.1f} minutes")
    print(f"\n📁 Results Directory: {test_suite.results_dir}")
    print("📈 Publication-ready visualizations generated")
    print("📊 Statistical analysis completed")
    print("\n🎉 Journal paper data collection complete!")
    
    return results

if __name__ == "__main__":
    main()
