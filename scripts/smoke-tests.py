#!/usr/bin/env python3
"""
Smoke tests for ClinChat-RAG deployment validation
Validates core functionality after deployment
"""

import requests
import time
import sys
import os
import json
import argparse
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class TestResult:
    name: str
    passed: bool
    message: str
    duration: float
    details: Optional[Dict] = None

class SmokeTests:
    def __init__(self, environment: str):
        self.environment = environment
        self.base_url = self._get_base_url()
        self.results: List[TestResult] = []
        
    def _get_base_url(self) -> str:
        """Get base URL for the environment"""
        if self.environment == 'production':
            return os.getenv('PROD_BASE_URL', 'https://clinchat-rag.example.com')
        elif self.environment == 'staging':
            return os.getenv('STAGING_BASE_URL', 'https://clinchat-rag-staging.example.com')
        else:
            return os.getenv('DEV_BASE_URL', 'http://localhost:8000')
            
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault('timeout', 30)
        
        # Add authentication headers if available
        auth_token = os.getenv('API_AUTH_TOKEN')
        if auth_token:
            kwargs.setdefault('headers', {})
            kwargs['headers']['Authorization'] = f"Bearer {auth_token}"
            
        return requests.request(method, url, **kwargs)
        
    def test_health_check(self) -> TestResult:
        """Test basic health endpoint"""
        start_time = time.time()
        
        try:
            response = self._make_request('GET', '/health')
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    return TestResult(
                        name="Health Check",
                        passed=True,
                        message="Service is healthy",
                        duration=duration,
                        details=data
                    )
                else:
                    return TestResult(
                        name="Health Check",
                        passed=False,
                        message=f"Service reports unhealthy status: {data.get('status')}",
                        duration=duration,
                        details=data
                    )
            else:
                return TestResult(
                    name="Health Check",
                    passed=False,
                    message=f"HTTP {response.status_code}: {response.text}",
                    duration=duration
                )
                
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name="Health Check",
                passed=False,
                message=f"Request failed: {str(e)}",
                duration=duration
            )
            
    def test_api_documentation(self) -> TestResult:
        """Test API documentation endpoint"""
        start_time = time.time()
        
        try:
            response = self._make_request('GET', '/docs')
            duration = time.time() - start_time
            
            if response.status_code == 200:
                # Check if it's HTML (Swagger UI)
                content_type = response.headers.get('content-type', '')
                if 'text/html' in content_type:
                    return TestResult(
                        name="API Documentation",
                        passed=True,
                        message="API documentation is accessible",
                        duration=duration
                    )
                else:
                    return TestResult(
                        name="API Documentation",
                        passed=False,
                        message=f"Unexpected content type: {content_type}",
                        duration=duration
                    )
            else:
                return TestResult(
                    name="API Documentation",
                    passed=False,
                    message=f"HTTP {response.status_code}",
                    duration=duration
                )
                
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name="API Documentation",
                passed=False,
                message=f"Request failed: {str(e)}",
                duration=duration
            )
            
    def test_metrics_endpoint(self) -> TestResult:
        """Test metrics endpoint"""
        start_time = time.time()
        
        try:
            response = self._make_request('GET', '/metrics')
            duration = time.time() - start_time
            
            if response.status_code == 200:
                # Check if it's Prometheus format
                content = response.text
                if 'TYPE' in content and 'HELP' in content:
                    return TestResult(
                        name="Metrics Endpoint",
                        passed=True,
                        message="Metrics endpoint is working",
                        duration=duration
                    )
                else:
                    return TestResult(
                        name="Metrics Endpoint",
                        passed=False,
                        message="Metrics format appears invalid",
                        duration=duration
                    )
            else:
                return TestResult(
                    name="Metrics Endpoint",
                    passed=False,
                    message=f"HTTP {response.status_code}",
                    duration=duration
                )
                
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name="Metrics Endpoint",
                passed=False,
                message=f"Request failed: {str(e)}",
                duration=duration
            )
            
    def test_chat_endpoint(self) -> TestResult:
        """Test chat functionality with sample query"""
        start_time = time.time()
        
        try:
            # Test query that should be safe and general
            test_query = "What is the normal range for blood pressure?"
            
            response = self._make_request(
                'POST',
                '/chat',
                json={
                    'message': test_query,
                    'user_id': 'smoke-test-user',
                    'session_id': f'smoke-test-{int(time.time())}'
                }
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get('response'):
                    return TestResult(
                        name="Chat Endpoint",
                        passed=True,
                        message="Chat endpoint is working",
                        duration=duration,
                        details={
                            'query': test_query,
                            'response_length': len(data.get('response', ''))
                        }
                    )
                else:
                    return TestResult(
                        name="Chat Endpoint",
                        passed=False,
                        message="No response received from chat",
                        duration=duration,
                        details=data
                    )
            else:
                return TestResult(
                    name="Chat Endpoint",
                    passed=False,
                    message=f"HTTP {response.status_code}: {response.text}",
                    duration=duration
                )
                
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name="Chat Endpoint",
                passed=False,
                message=f"Request failed: {str(e)}",
                duration=duration
            )
            
    def test_search_endpoint(self) -> TestResult:
        """Test search functionality"""
        start_time = time.time()
        
        try:
            response = self._make_request(
                'POST',
                '/search',
                json={
                    'query': 'hypertension treatment',
                    'limit': 5
                }
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) or data.get('results'):
                    return TestResult(
                        name="Search Endpoint",
                        passed=True,
                        message="Search endpoint is working",
                        duration=duration,
                        details={
                            'result_count': len(data) if isinstance(data, list) else len(data.get('results', []))
                        }
                    )
                else:
                    return TestResult(
                        name="Search Endpoint",
                        passed=False,
                        message="No results structure found in response",
                        duration=duration,
                        details=data
                    )
            else:
                return TestResult(
                    name="Search Endpoint",
                    passed=False,
                    message=f"HTTP {response.status_code}: {response.text}",
                    duration=duration
                )
                
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name="Search Endpoint",
                passed=False,
                message=f"Request failed: {str(e)}",
                duration=duration
            )
            
    def test_ssl_certificate(self) -> TestResult:
        """Test SSL certificate validity (for HTTPS endpoints)"""
        start_time = time.time()
        
        if not self.base_url.startswith('https://'):
            return TestResult(
                name="SSL Certificate",
                passed=True,
                message="Skipped (not HTTPS)",
                duration=0.0
            )
            
        try:
            import ssl
            import socket
            from urllib.parse import urlparse
            
            parsed = urlparse(self.base_url)
            hostname = parsed.hostname
            port = parsed.port or 443
            
            context = ssl.create_default_context()
            
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
            duration = time.time() - start_time
            
            return TestResult(
                name="SSL Certificate",
                passed=True,
                message="SSL certificate is valid",
                duration=duration,
                details={
                    'subject': dict(x[0] for x in cert['subject']),
                    'issuer': dict(x[0] for x in cert['issuer']),
                    'version': cert['version']
                }
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name="SSL Certificate",
                passed=False,
                message=f"SSL check failed: {str(e)}",
                duration=duration
            )
            
    def run_all_tests(self) -> bool:
        """Run all smoke tests"""
        print(f"🧪 Running smoke tests for {self.environment} environment")
        print(f"🎯 Target: {self.base_url}")
        print("=" * 60)
        
        tests = [
            self.test_health_check,
            self.test_ssl_certificate,
            self.test_api_documentation,
            self.test_metrics_endpoint,
            self.test_chat_endpoint,
            self.test_search_endpoint,
        ]
        
        for test_func in tests:
            print(f"⏳ Running {test_func.__name__.replace('test_', '').replace('_', ' ').title()}...")
            result = test_func()
            self.results.append(result)
            
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"{status} - {result.message} ({result.duration:.2f}s)")
            
            if result.details:
                print(f"    Details: {json.dumps(result.details, indent=2)}")
            print()
            
        # Summary
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        
        print("=" * 60)
        print(f"📊 Test Results: {passed}/{total} passed")
        
        if passed == total:
            print("🎉 All smoke tests passed!")
            return True
        else:
            print("💥 Some tests failed!")
            for result in self.results:
                if not result.passed:
                    print(f"   ❌ {result.name}: {result.message}")
            return False
            
def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Run smoke tests')
    parser.add_argument('--environment', required=True, 
                       choices=['staging', 'production', 'development'],
                       help='Environment to test')
    
    args = parser.parse_args()
    
    # Wait a bit for services to be ready
    if args.environment in ['staging', 'production']:
        print("⏰ Waiting 30 seconds for services to stabilize...")
        time.sleep(30)
    
    smoke_tests = SmokeTests(args.environment)
    
    if smoke_tests.run_all_tests():
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()