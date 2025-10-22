#!/usr/bin/env python3
"""
Load Testing and Stress Testing System
Comprehensive load testing for API endpoints, database, and system resources
"""

import asyncio
import aiohttp
import time
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
import statistics
import random
import concurrent.futures
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class LoadTestConfig:
    """Load test configuration"""
    base_url: str = "http://localhost:8000"
    concurrent_users: int = 10
    test_duration_seconds: int = 60
    ramp_up_seconds: int = 10
    think_time_seconds: float = 1.0
    max_requests_per_second: Optional[int] = None
    timeout_seconds: int = 30
    
@dataclass
class TestScenario:
    """Individual test scenario"""
    name: str
    endpoint: str
    method: str = "GET"
    headers: Dict[str, str] = None
    payload: Dict[str, Any] = None
    weight: float = 1.0  # Probability weight
    auth_required: bool = False
    
@dataclass 
class TestResult:
    """Individual test result"""
    scenario_name: str
    endpoint: str
    method: str
    status_code: int
    response_time: float
    response_size: int
    timestamp: datetime
    error_message: Optional[str] = None
    success: bool = True

@dataclass
class LoadTestReport:
    """Comprehensive load test report"""
    test_name: str
    config: LoadTestConfig
    scenarios: List[TestScenario]
    results: List[TestResult]
    start_time: datetime
    end_time: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_rate: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    throughput_mb_per_second: float
    errors_by_type: Dict[str, int]

class LoadTester:
    """Advanced load testing system"""
    
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.results: List[TestResult] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(
            limit=self.config.concurrent_users * 2,
            limit_per_host=self.config.concurrent_users,
            keepalive_timeout=30
        )
        
        timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"User-Agent": "ClinChat-RAG-LoadTester/1.0"}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def run_load_test(self, scenarios: List[TestScenario], 
                          test_name: str = "Load Test") -> LoadTestReport:
        """Run comprehensive load test"""
        
        logger.info(f"Starting load test: {test_name}")
        logger.info(f"Configuration: {self.config.concurrent_users} users, "
                   f"{self.config.test_duration_seconds}s duration")
        
        self.start_time = datetime.now()
        self.results = []
        
        # Create semaphore for rate limiting if specified
        semaphore = None
        if self.config.max_requests_per_second:
            semaphore = asyncio.Semaphore(self.config.max_requests_per_second)
        
        # Calculate ramp-up delay between user starts
        ramp_up_delay = self.config.ramp_up_seconds / self.config.concurrent_users
        
        # Start virtual users
        tasks = []
        for user_id in range(self.config.concurrent_users):
            # Stagger user start times for ramp-up
            start_delay = user_id * ramp_up_delay
            
            task = asyncio.create_task(
                self._virtual_user(user_id, scenarios, start_delay, semaphore)
            )
            tasks.append(task)
        
        # Wait for test duration
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.config.test_duration_seconds + self.config.ramp_up_seconds + 30
            )
        except asyncio.TimeoutError:
            logger.warning("Load test timed out, cancelling remaining tasks")
            for task in tasks:
                task.cancel()
        
        self.end_time = datetime.now()
        
        # Generate report
        report = self._generate_report(test_name, scenarios)
        logger.info(f"Load test completed: {report.total_requests} requests, "
                   f"{report.error_rate:.1f}% error rate")
        
        return report
    
    async def _virtual_user(self, user_id: int, scenarios: List[TestScenario],
                           start_delay: float, semaphore: Optional[asyncio.Semaphore]):
        """Simulate individual virtual user"""
        
        # Wait for ramp-up delay
        if start_delay > 0:
            await asyncio.sleep(start_delay)
        
        user_start_time = time.time()
        request_count = 0
        
        try:
            while True:
                # Check if test duration exceeded
                elapsed_time = time.time() - user_start_time + start_delay
                if elapsed_time >= self.config.test_duration_seconds:
                    break
                
                # Apply rate limiting if configured
                if semaphore:
                    async with semaphore:
                        await self._execute_scenario(user_id, scenarios)
                else:
                    await self._execute_scenario(user_id, scenarios)
                
                request_count += 1
                
                # Think time between requests
                if self.config.think_time_seconds > 0:
                    think_time = random.uniform(
                        self.config.think_time_seconds * 0.5,
                        self.config.think_time_seconds * 1.5
                    )
                    await asyncio.sleep(think_time)
                
        except Exception as e:
            logger.error(f"Virtual user {user_id} error: {e}")
        
        logger.debug(f"Virtual user {user_id} completed {request_count} requests")
    
    async def _execute_scenario(self, user_id: int, scenarios: List[TestScenario]):
        """Execute a randomly selected test scenario"""
        
        # Select scenario based on weights
        scenario = self._select_weighted_scenario(scenarios)
        
        start_time = time.time()
        
        try:
            # Prepare request
            url = f"{self.config.base_url}{scenario.endpoint}"
            
            headers = scenario.headers or {}
            
            # Add authentication if required
            if scenario.auth_required:
                headers["Authorization"] = f"Bearer test_token_{user_id}"
            
            # Execute request
            async with self.session.request(
                method=scenario.method,
                url=url,
                headers=headers,
                json=scenario.payload if scenario.method in ["POST", "PUT", "PATCH"] else None
            ) as response:
                
                response_time = time.time() - start_time
                response_size = len(await response.read())
                
                result = TestResult(
                    scenario_name=scenario.name,
                    endpoint=scenario.endpoint,
                    method=scenario.method,
                    status_code=response.status,
                    response_time=response_time,
                    response_size=response_size,
                    timestamp=datetime.now(),
                    success=200 <= response.status < 400
                )
                
                self.results.append(result)
                
        except Exception as e:
            response_time = time.time() - start_time
            
            result = TestResult(
                scenario_name=scenario.name,
                endpoint=scenario.endpoint,
                method=scenario.method,
                status_code=0,
                response_time=response_time,
                response_size=0,
                timestamp=datetime.now(),
                error_message=str(e),
                success=False
            )
            
            self.results.append(result)
    
    def _select_weighted_scenario(self, scenarios: List[TestScenario]) -> TestScenario:
        """Select scenario based on weights"""
        total_weight = sum(scenario.weight for scenario in scenarios)
        random_value = random.uniform(0, total_weight)
        
        current_weight = 0
        for scenario in scenarios:
            current_weight += scenario.weight
            if random_value <= current_weight:
                return scenario
        
        # Fallback to first scenario
        return scenarios[0]
    
    def _generate_report(self, test_name: str, 
                        scenarios: List[TestScenario]) -> LoadTestReport:
        """Generate comprehensive load test report"""
        
        if not self.results:
            raise ValueError("No test results available")
        
        # Filter successful requests for response time calculations
        successful_results = [r for r in self.results if r.success]
        response_times = [r.response_time for r in successful_results]
        
        # Calculate statistics
        total_requests = len(self.results)
        successful_requests = len(successful_results)
        failed_requests = total_requests - successful_requests
        error_rate = (failed_requests / total_requests) * 100 if total_requests > 0 else 0
        
        test_duration = (self.end_time - self.start_time).total_seconds()
        requests_per_second = total_requests / test_duration if test_duration > 0 else 0
        
        total_response_size = sum(r.response_size for r in successful_results)
        throughput_mb_per_second = (total_response_size / (1024 * 1024)) / test_duration if test_duration > 0 else 0
        
        # Response time statistics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p50_response_time = statistics.median(response_times)
            
            sorted_times = sorted(response_times)
            p95_index = int(0.95 * len(sorted_times))
            p99_index = int(0.99 * len(sorted_times))
            p95_response_time = sorted_times[p95_index] if p95_index < len(sorted_times) else max_response_time
            p99_response_time = sorted_times[p99_index] if p99_index < len(sorted_times) else max_response_time
        else:
            avg_response_time = min_response_time = max_response_time = 0
            p50_response_time = p95_response_time = p99_response_time = 0
        
        # Error analysis
        errors_by_type = {}
        for result in self.results:
            if not result.success:
                error_key = f"{result.status_code}:{result.error_message or 'Unknown'}"
                errors_by_type[error_key] = errors_by_type.get(error_key, 0) + 1
        
        return LoadTestReport(
            test_name=test_name,
            config=self.config,
            scenarios=scenarios,
            results=self.results,
            start_time=self.start_time,
            end_time=self.end_time,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            error_rate=error_rate,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p50_response_time=p50_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            throughput_mb_per_second=throughput_mb_per_second,
            errors_by_type=errors_by_type
        )

class StressTester:
    """Stress testing for finding system limits"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    async def run_stress_test(self, scenario: TestScenario,
                            max_users: int = 1000,
                            step_size: int = 50,
                            step_duration: int = 30) -> List[LoadTestReport]:
        """Run incremental stress test to find breaking point"""
        
        reports = []
        current_users = step_size
        
        logger.info(f"Starting stress test up to {max_users} users")
        
        while current_users <= max_users:
            logger.info(f"Testing with {current_users} concurrent users")
            
            # Configure load test for current user count
            config = LoadTestConfig(
                base_url=self.base_url,
                concurrent_users=current_users,
                test_duration_seconds=step_duration,
                ramp_up_seconds=10,
                think_time_seconds=0.1  # Minimal think time for stress testing
            )
            
            async with LoadTester(config) as tester:
                report = await tester.run_load_test(
                    [scenario], 
                    f"Stress Test - {current_users} users"
                )
                reports.append(report)
                
                # Check if system is breaking down
                if report.error_rate > 50 or report.avg_response_time > 10:
                    logger.warning(f"System breaking point detected at {current_users} users")
                    break
            
            current_users += step_size
            
            # Small delay between stress levels
            await asyncio.sleep(5)
        
        return reports

class LoadTestReporter:
    """Generate detailed load test reports"""
    
    def generate_html_report(self, report: LoadTestReport, 
                           output_file: str = "load_test_report.html"):
        """Generate HTML report"""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Load Test Report - {report.test_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .summary {{ display: flex; flex-wrap: wrap; gap: 20px; margin: 20px 0; }}
                .metric {{ background-color: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 5px; min-width: 200px; }}
                .metric h3 {{ margin: 0 0 10px 0; color: #333; }}
                .metric .value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
                .error {{ color: #dc3545; }}
                .success {{ color: #28a745; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .chart {{ margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Load Test Report: {report.test_name}</h1>
                <p><strong>Test Period:</strong> {report.start_time} to {report.end_time}</p>
                <p><strong>Duration:</strong> {(report.end_time - report.start_time).total_seconds():.1f} seconds</p>
                <p><strong>Configuration:</strong> {report.config.concurrent_users} users, {report.config.test_duration_seconds}s test</p>
            </div>
            
            <div class="summary">
                <div class="metric">
                    <h3>Total Requests</h3>
                    <div class="value">{report.total_requests:,}</div>
                </div>
                <div class="metric">
                    <h3>Success Rate</h3>
                    <div class="value success">{100 - report.error_rate:.1f}%</div>
                </div>
                <div class="metric">
                    <h3>Error Rate</h3>
                    <div class="value {'error' if report.error_rate > 5 else ''}">{report.error_rate:.1f}%</div>
                </div>
                <div class="metric">
                    <h3>Requests/Second</h3>
                    <div class="value">{report.requests_per_second:.1f}</div>
                </div>
                <div class="metric">
                    <h3>Avg Response Time</h3>
                    <div class="value">{report.avg_response_time:.3f}s</div>
                </div>
                <div class="metric">
                    <h3>95th Percentile</h3>
                    <div class="value">{report.p95_response_time:.3f}s</div>
                </div>
                <div class="metric">
                    <h3>Throughput</h3>
                    <div class="value">{report.throughput_mb_per_second:.2f} MB/s</div>
                </div>
            </div>
            
            <h2>Response Time Statistics</h2>
            <table>
                <tr><th>Metric</th><th>Value (seconds)</th></tr>
                <tr><td>Minimum</td><td>{report.min_response_time:.3f}</td></tr>
                <tr><td>Average</td><td>{report.avg_response_time:.3f}</td></tr>
                <tr><td>Median (50th percentile)</td><td>{report.p50_response_time:.3f}</td></tr>
                <tr><td>95th percentile</td><td>{report.p95_response_time:.3f}</td></tr>
                <tr><td>99th percentile</td><td>{report.p99_response_time:.3f}</td></tr>
                <tr><td>Maximum</td><td>{report.max_response_time:.3f}</td></tr>
            </table>
        """
        
        if report.errors_by_type:
            html_content += """
            <h2>Error Analysis</h2>
            <table>
                <tr><th>Error Type</th><th>Count</th><th>Percentage</th></tr>
            """
            
            for error_type, count in report.errors_by_type.items():
                percentage = (count / report.total_requests) * 100
                html_content += f"""
                <tr>
                    <td>{error_type}</td>
                    <td>{count}</td>
                    <td>{percentage:.1f}%</td>
                </tr>
                """
            
            html_content += "</table>"
        
        html_content += """
            <h2>Test Scenarios</h2>
            <table>
                <tr><th>Scenario</th><th>Endpoint</th><th>Method</th><th>Weight</th></tr>
        """
        
        for scenario in report.scenarios:
            html_content += f"""
            <tr>
                <td>{scenario.name}</td>
                <td>{scenario.endpoint}</td>
                <td>{scenario.method}</td>
                <td>{scenario.weight}</td>
            </tr>
            """
        
        html_content += """
            </table>
        </body>
        </html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {output_file}")
    
    def save_json_report(self, report: LoadTestReport, 
                        output_file: str = "load_test_report.json"):
        """Save report as JSON"""
        
        # Convert report to dict, handling datetime serialization
        report_dict = asdict(report)
        
        # Convert datetime objects to ISO format strings
        report_dict['start_time'] = report.start_time.isoformat()
        report_dict['end_time'] = report.end_time.isoformat()
        
        # Convert result timestamps
        for result in report_dict['results']:
            result['timestamp'] = datetime.fromisoformat(result['timestamp']).isoformat() if isinstance(result['timestamp'], str) else result['timestamp'].isoformat()
        
        with open(output_file, 'w') as f:
            json.dump(report_dict, f, indent=2)
        
        logger.info(f"JSON report saved: {output_file}")

# Example test scenarios for ClinChat-RAG
def get_clinchat_test_scenarios() -> List[TestScenario]:
    """Get predefined test scenarios for ClinChat-RAG"""
    
    return [
        TestScenario(
            name="Dashboard Load",
            endpoint="/api/dashboard",
            method="GET",
            weight=2.0,
            auth_required=True
        ),
        TestScenario(
            name="Patient Search",
            endpoint="/api/patients",
            method="GET",
            weight=3.0,
            auth_required=True
        ),
        TestScenario(
            name="Patient Details",
            endpoint="/api/patients/12345",
            method="GET",
            weight=2.5,
            auth_required=True
        ),
        TestScenario(
            name="AI Chat Query",
            endpoint="/api/chat/query",
            method="POST",
            payload={"query": "What is the patient's latest lab results?"},
            weight=1.5,
            auth_required=True
        ),
        TestScenario(
            name="Document Upload",
            endpoint="/api/documents",
            method="POST",
            payload={"content": "Sample medical document", "patient_id": "12345"},
            weight=0.5,
            auth_required=True
        ),
        TestScenario(
            name="Health Check",
            endpoint="/health",
            method="GET",
            weight=0.5,
            auth_required=False
        )
    ]

# Example usage
async def run_clinchat_load_test():
    """Run load test for ClinChat-RAG system"""
    
    # Configure load test
    config = LoadTestConfig(
        base_url="http://localhost:8000",
        concurrent_users=50,
        test_duration_seconds=120,
        ramp_up_seconds=30,
        think_time_seconds=2.0,
        max_requests_per_second=100
    )
    
    # Get test scenarios
    scenarios = get_clinchat_test_scenarios()
    
    # Run load test
    async with LoadTester(config) as tester:
        report = await tester.run_load_test(scenarios, "ClinChat-RAG Load Test")
    
    # Generate reports
    reporter = LoadTestReporter()
    reporter.generate_html_report(report, "clinchat_load_test_report.html")
    reporter.save_json_report(report, "clinchat_load_test_report.json")
    
    # Print summary
    print(f"\n🔍 Load Test Summary:")
    print(f"   Total Requests: {report.total_requests:,}")
    print(f"   Success Rate: {100 - report.error_rate:.1f}%")
    print(f"   Avg Response Time: {report.avg_response_time:.3f}s")
    print(f"   95th Percentile: {report.p95_response_time:.3f}s")
    print(f"   Requests/Second: {report.requests_per_second:.1f}")
    print(f"   Throughput: {report.throughput_mb_per_second:.2f} MB/s")
    
    return report

if __name__ == "__main__":
    asyncio.run(run_clinchat_load_test())