#!/usr/bin/env python3
"""
Comprehensive Endpoint Testing Script for Quenty Microservices
Tests all endpoints, extracts Docker logs, and generates detailed reports.
Uses only standard library modules.
"""

import json
import os
import subprocess
import sys
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import concurrent.futures
from pathlib import Path
import traceback
import time
import threading
import socket

class DockerLogExtractor:
    """Extracts and analyzes Docker container logs for errors."""
    
    def __init__(self, log_dir: str = "logs/scripts"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.containers = [
            "quenty-auth-service",
            "quenty-order-service", 
            "quenty-customer-service",
            "quenty-pickup-service",
            "quenty-intl-shipping-service",
            "quenty-microcredit-service",
            "quenty-analytics-service",
            "quenty-reverse-logistics-service",
            "quenty-franchise-service",
            "quenty-api-gateway",
            "quenty-prometheus",
            "quenty-grafana",
            "quenty-loki",
            "quenty-promtail"
        ]
    
    def extract_logs(self, minutes_back: int = 10) -> Dict[str, Dict[str, Any]]:
        """Extract logs from all containers."""
        print(f"\n🔍 Extracting Docker logs from last {minutes_back} minutes...")
        
        since_time = (datetime.now() - timedelta(minutes=minutes_back)).strftime("%Y-%m-%dT%H:%M:%S")
        logs_data = {}
        
        for container in self.containers:
            try:
                # Get container logs
                cmd = ["docker", "logs", "--since", since_time, "--timestamps", container]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    logs = result.stdout + result.stderr
                    errors = self._extract_errors(logs)
                    
                    logs_data[container] = {
                        "status": "success",
                        "total_lines": len(logs.split('\n')) if logs else 0,
                        "errors": errors,
                        "error_count": len(errors),
                        "raw_logs": logs[:2000] if logs else ""  # First 2000 chars
                    }
                    
                    # Save full logs to file
                    log_file = self.log_dir / f"{container}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                    with open(log_file, 'w') as f:
                        f.write(logs)
                        
                else:
                    logs_data[container] = {
                        "status": "failed",
                        "error": result.stderr,
                        "total_lines": 0,
                        "errors": [],
                        "error_count": 0,
                        "raw_logs": ""
                    }
                    
            except subprocess.TimeoutExpired:
                logs_data[container] = {
                    "status": "timeout",
                    "error": "Log extraction timed out",
                    "total_lines": 0,
                    "errors": [],
                    "error_count": 0,
                    "raw_logs": ""
                }
            except Exception as e:
                logs_data[container] = {
                    "status": "error",
                    "error": str(e),
                    "total_lines": 0,
                    "errors": [],
                    "error_count": 0,
                    "raw_logs": ""
                }
        
        return logs_data
    
    def _extract_errors(self, logs: str) -> List[Dict[str, str]]:
        """Extract error patterns from logs."""
        if not logs:
            return []
            
        error_patterns = [
            "ERROR", "FATAL", "CRITICAL", "Exception", "Traceback",
            "failed", "error", "Error", "FAILED", "timeout", "Timeout",
            "refused connection", "connection refused", "500", "502", "503", "504"
        ]
        
        errors = []
        lines = logs.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            for pattern in error_patterns:
                if pattern.lower() in line_lower:
                    # Include context (previous and next lines)
                    context_start = max(0, i-1)
                    context_end = min(len(lines), i+2)
                    context = '\n'.join(lines[context_start:context_end])
                    
                    errors.append({
                        "line_number": i + 1,
                        "pattern": pattern,
                        "content": line.strip(),
                        "context": context,
                        "timestamp": self._extract_timestamp(line)
                    })
                    break
        
        return errors
    
    def _extract_timestamp(self, line: str) -> Optional[str]:
        """Extract timestamp from log line if present."""
        # Common timestamp patterns
        import re
        patterns = [
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
            r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',
            r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group()
        return None

class HTTPClient:
    """Simple HTTP client using urllib."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.auth_token = None
    
    def set_auth_token(self, token: str):
        """Set authentication token."""
        self.auth_token = token
    
    def request(self, method: str, url: str, data: dict = None, headers: dict = None) -> Dict[str, Any]:
        """Make HTTP request."""
        if headers is None:
            headers = {}
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        headers["Content-Type"] = "application/json"
        
        start_time = time.time()
        
        try:
            if data:
                data = json.dumps(data).encode('utf-8')
            
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                response_time = (time.time() - start_time) * 1000
                response_data = response.read().decode('utf-8')
                
                try:
                    response_json = json.loads(response_data)
                except json.JSONDecodeError:
                    response_json = response_data
                
                return {
                    "success": True,
                    "status_code": response.status,
                    "response": response_json,
                    "response_time_ms": round(response_time, 2),
                    "response_size": len(response_data),
                    "headers": dict(response.headers)
                }
                
        except urllib.error.HTTPError as e:
            response_time = (time.time() - start_time) * 1000
            try:
                error_data = e.read().decode('utf-8')
                try:
                    error_json = json.loads(error_data)
                except json.JSONDecodeError:
                    error_json = error_data
            except:
                error_json = str(e)
            
            return {
                "success": False,
                "status_code": e.code,
                "error": error_json,
                "response_time_ms": round(response_time, 2)
            }
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "success": False,
                "error": str(e),
                "response_time_ms": round(response_time, 2),
                "traceback": traceback.format_exc()
            }

class EndpointTester:
    """Comprehensive endpoint testing for all microservices."""
    
    def __init__(self):
        self.base_urls = {
            "auth": "http://localhost:8009",
            "order": "http://localhost:8002", 
            "customer": "http://localhost:8001",
            "pickup": "http://localhost:8003",
            "intl-shipping": "http://localhost:8004",
            "microcredit": "http://localhost:8005",
            "analytics": "http://localhost:8006",
            "reverse-logistics": "http://localhost:8007",
            "franchise": "http://localhost:8008",
            "api-gateway": "http://localhost:8000"
        }
        self.client = HTTPClient()
        
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive endpoint testing."""
        print("🚀 Starting Comprehensive Endpoint Testing...")
        
        # Step 1: Authentication (must be first)
        print("\n🔐 Step 1: Authentication...")
        auth_result = self._test_authentication()
        
        if auth_result["success"]:
            print(f"✅ Authentication successful. Token obtained.")
            if "token" in auth_result:
                self.client.set_auth_token(auth_result["token"])
        else:
            print(f"❌ Authentication failed: {auth_result.get('error', 'Unknown error')}")
            return {"error": "Authentication failed", "details": auth_result}
        
        # Step 2: Health checks for all services
        print("\n🏥 Step 2: Health Checks...")
        health_results = self._test_all_health_endpoints()
        
        # Step 3: Parallel endpoint testing
        print("\n🔄 Step 3: Parallel Endpoint Testing...")
        endpoint_results = self._test_all_endpoints_parallel()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "authentication": auth_result,
            "health_checks": health_results,
            "endpoint_tests": endpoint_results,
            "summary": self._generate_summary(health_results, endpoint_results)
        }
    
    def _test_authentication(self) -> Dict[str, Any]:
        """Test authentication endpoint and get token."""
        try:
            login_data = {
                "username_or_email": "admin",
                "password": "AdminPassword123"
            }
            
            result = self.client.request("POST", f"{self.base_urls['auth']}/api/v1/auth/login", data=login_data)
            
            if result["success"]:
                response = result["response"]
                return {
                    "success": True,
                    "status_code": result["status_code"],
                    "token": response.get("access_token"),
                    "user_info": response.get("user", {}),
                    "token_type": response.get("token_type"),
                    "expires_in": response.get("expires_in"),
                    "response_time_ms": result["response_time_ms"]
                }
            else:
                return {
                    "success": False,
                    "status_code": result.get("status_code"),
                    "error": result.get("error"),
                    "response_time_ms": result.get("response_time_ms", 0)
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception during authentication: {str(e)}",
                "traceback": traceback.format_exc()
            }
    
    def _test_all_health_endpoints(self) -> Dict[str, Any]:
        """Test health endpoints for all services using threading."""
        health_results = {}
        
        def test_health(service, base_url):
            return service, self._test_health_endpoint(service, base_url)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(test_health, service, base_url)
                for service, base_url in self.base_urls.items()
            ]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    service, result = future.result()
                    health_results[service] = result
                except Exception as e:
                    print(f"Error testing health endpoint: {e}")
        
        return health_results
    
    def _test_health_endpoint(self, service: str, base_url: str) -> Dict[str, Any]:
        """Test health endpoint for a single service."""
        try:
            result = self.client.request("GET", f"{base_url}/health")
            
            if result["success"]:
                return {
                    "service": service,
                    "status": "healthy",
                    "status_code": result["status_code"],
                    "response": result["response"],
                    "response_time_ms": result["response_time_ms"]
                }
            else:
                return {
                    "service": service,
                    "status": "unhealthy",
                    "status_code": result.get("status_code"),
                    "error": result.get("error"),
                    "response_time_ms": result.get("response_time_ms", 0)
                }
        except Exception as e:
            return {
                "service": service,
                "status": "error",
                "error": str(e)
            }
    
    def _test_all_endpoints_parallel(self) -> Dict[str, Any]:
        """Test all endpoints in parallel after authentication."""
        
        endpoint_definitions = {
            "auth": [
                {"method": "GET", "path": "/api/v1/profile", "auth_required": True},
                {"method": "GET", "path": "/api/v1/users", "auth_required": True},
            ],
            "order": [
                {"method": "GET", "path": "/api/v1/products", "auth_required": True},
                {"method": "GET", "path": "/api/v1/orders", "auth_required": True},
                {"method": "GET", "path": "/api/v1/inventory", "auth_required": True},
                {"method": "GET", "path": "/api/v1/products/low-stock", "auth_required": True}
            ],
            "customer": [
                {"method": "GET", "path": "/api/v1/customers", "auth_required": True},
                {"method": "GET", "path": "/api/v1/companies", "auth_required": True}
            ],
            "pickup": [
                {"method": "GET", "path": "/api/v1/pickups", "auth_required": True},
                {"method": "GET", "path": "/api/v1/routes", "auth_required": True}
            ],
            "intl-shipping": [
                {"method": "GET", "path": "/api/v1/shipments", "auth_required": True},
                {"method": "GET", "path": "/api/v1/tracking", "auth_required": True}
            ],
            "microcredit": [
                {"method": "GET", "path": "/api/v1/applications", "auth_required": True},
                {"method": "GET", "path": "/api/v1/loans", "auth_required": True}
            ],
            "analytics": [
                {"method": "GET", "path": "/api/v1/dashboard", "auth_required": True},
                {"method": "GET", "path": "/api/v1/reports", "auth_required": True}
            ],
            "reverse-logistics": [
                {"method": "GET", "path": "/api/v1/returns", "auth_required": True}
            ],
            "franchise": [
                {"method": "GET", "path": "/api/v1/franchises", "auth_required": True}
            ]
        }
        
        # Create tasks for all endpoints
        def test_endpoint(service, base_url, endpoint_def):
            return service, endpoint_def, self._test_single_endpoint(service, base_url, endpoint_def)
        
        organized_results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for service, endpoints in endpoint_definitions.items():
                if service in self.base_urls:
                    organized_results[service] = []
                    for endpoint in endpoints:
                        future = executor.submit(test_endpoint, service, self.base_urls[service], endpoint)
                        futures.append(future)
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    service, endpoint_def, result = future.result()
                    organized_results[service].append(result)
                except Exception as e:
                    print(f"Error testing endpoint: {e}")
        
        return organized_results
    
    def _test_single_endpoint(self, service: str, base_url: str, endpoint_def: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single endpoint."""
        method = endpoint_def["method"]
        path = endpoint_def["path"]
        auth_required = endpoint_def.get("auth_required", False)
        data = endpoint_def.get("data")
        
        url = f"{base_url}{path}"
        
        try:
            # Temporarily disable auth for this request if not required
            original_token = self.client.auth_token
            if not auth_required:
                self.client.auth_token = None
            
            result = self.client.request(method, url, data=data)
            
            # Restore auth token
            self.client.auth_token = original_token
            
            return {
                "service": service,
                "method": method,
                "path": path,
                "status_code": result.get("status_code"),
                "status": "success" if result.get("success") else "failed",
                "response_time_ms": result.get("response_time_ms", 0),
                "response_size": result.get("response_size", 0),
                "response": result.get("response") if result.get("success") else result.get("error"),
                "error": result.get("error") if not result.get("success") else None
            }
                
        except Exception as e:
            return {
                "service": service,
                "method": method,
                "path": path,
                "status": "error",
                "error": str(e),
                "response_time_ms": 0,
                "traceback": traceback.format_exc()
            }
    
    def _generate_summary(self, health_results: Dict, endpoint_results: Dict) -> Dict[str, Any]:
        """Generate test summary."""
        total_health_tests = len(health_results)
        healthy_services = sum(1 for result in health_results.values() if result.get("status") == "healthy")
        
        total_endpoint_tests = sum(len(endpoints) for endpoints in endpoint_results.values())
        successful_endpoints = sum(
            sum(1 for endpoint in endpoints if endpoint.get("status") == "success")
            for endpoints in endpoint_results.values()
        )
        
        return {
            "health_check_summary": {
                "total_services": total_health_tests,
                "healthy_services": healthy_services,
                "unhealthy_services": total_health_tests - healthy_services,
                "health_rate": f"{(healthy_services/total_health_tests)*100:.1f}%" if total_health_tests > 0 else "0%"
            },
            "endpoint_test_summary": {
                "total_endpoints": total_endpoint_tests,
                "successful_endpoints": successful_endpoints,
                "failed_endpoints": total_endpoint_tests - successful_endpoints,
                "success_rate": f"{(successful_endpoints/total_endpoint_tests)*100:.1f}%" if total_endpoint_tests > 0 else "0%"
            }
        }

class ReportGenerator:
    """Generate comprehensive test reports."""
    
    def __init__(self, output_dir: str = "logs/scripts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_reports(self, test_results: Dict[str, Any], docker_logs: Dict[str, Any]) -> Dict[str, str]:
        """Generate comprehensive reports."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        reports = {}
        
        # JSON Report
        json_file = self.output_dir / f"comprehensive_test_report_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump({
                "test_results": test_results,
                "docker_logs": docker_logs
            }, f, indent=2, default=str)
        reports["json"] = str(json_file)
        
        # Text Report
        text_file = self.output_dir / f"comprehensive_test_report_{timestamp}.txt"
        with open(text_file, 'w') as f:
            f.write(self._generate_text_report(test_results, docker_logs))
        reports["text"] = str(text_file)
        
        # Error Summary Report
        error_file = self.output_dir / f"error_summary_{timestamp}.txt"
        with open(error_file, 'w') as f:
            f.write(self._generate_error_summary(test_results, docker_logs))
        reports["errors"] = str(error_file)
        
        return reports
    
    def _generate_text_report(self, test_results: Dict[str, Any], docker_logs: Dict[str, Any]) -> str:
        """Generate human-readable text report."""
        report = []
        report.append("=" * 80)
        report.append("QUENTY MICROSERVICES - COMPREHENSIVE TEST REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        if "summary" in test_results:
            summary = test_results["summary"]
            report.append("📊 EXECUTIVE SUMMARY")
            report.append("-" * 40)
            
            health_summary = summary.get("health_check_summary", {})
            report.append(f"Health Checks: {health_summary.get('healthy_services', 0)}/{health_summary.get('total_services', 0)} services healthy ({health_summary.get('health_rate', '0%')})")
            
            endpoint_summary = summary.get("endpoint_test_summary", {})
            report.append(f"Endpoint Tests: {endpoint_summary.get('successful_endpoints', 0)}/{endpoint_summary.get('total_endpoints', 0)} endpoints successful ({endpoint_summary.get('success_rate', '0%')})")
            report.append("")
        
        # Health Check Results
        report.append("🏥 HEALTH CHECK RESULTS")
        report.append("-" * 40)
        if "health_checks" in test_results:
            for service, result in test_results["health_checks"].items():
                status = result.get("status", "unknown")
                response_time = result.get("response_time_ms", 0)
                emoji = "✅" if status == "healthy" else "❌"
                report.append(f"{emoji} {service.upper()}: {status} ({response_time}ms)")
                if "error" in result:
                    report.append(f"   Error: {result['error']}")
        report.append("")
        
        # Endpoint Test Results
        report.append("🔄 ENDPOINT TEST RESULTS")
        report.append("-" * 40)
        if "endpoint_tests" in test_results:
            for service, endpoints in test_results["endpoint_tests"].items():
                report.append(f"\n{service.upper()} SERVICE:")
                for endpoint in endpoints:
                    status = endpoint.get("status", "unknown")
                    method = endpoint.get("method", "")
                    path = endpoint.get("path", "")
                    status_code = endpoint.get("status_code", "")
                    response_time = endpoint.get("response_time_ms", 0)
                    
                    emoji = "✅" if status == "success" else "❌"
                    report.append(f"  {emoji} {method} {path} - {status_code} ({response_time}ms)")
                    
                    if "error" in endpoint and endpoint["error"]:
                        error_msg = str(endpoint["error"])[:200]
                        report.append(f"     Error: {error_msg}")
        
        # Docker Logs Summary
        report.append("\n🐳 DOCKER LOGS ANALYSIS")
        report.append("-" * 40)
        for container, log_data in docker_logs.items():
            status = log_data.get("status", "unknown")
            error_count = log_data.get("error_count", 0)
            total_lines = log_data.get("total_lines", 0)
            
            emoji = "✅" if error_count == 0 else "⚠️"
            report.append(f"{emoji} {container}: {total_lines} log lines, {error_count} errors")
            
            if error_count > 0:
                errors = log_data.get("errors", [])[:3]  # Show first 3 errors
                for error in errors:
                    report.append(f"   - {error.get('content', '')[:100]}...")
        
        return "\n".join(report)
    
    def _generate_error_summary(self, test_results: Dict[str, Any], docker_logs: Dict[str, Any]) -> str:
        """Generate error-focused summary."""
        report = []
        report.append("ERROR SUMMARY REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Endpoint Errors
        report.append("🔴 ENDPOINT ERRORS:")
        report.append("-" * 30)
        if "endpoint_tests" in test_results:
            error_found = False
            for service, endpoints in test_results["endpoint_tests"].items():
                for endpoint in endpoints:
                    if endpoint.get("status") != "success":
                        error_found = True
                        method = endpoint.get("method", "")
                        path = endpoint.get("path", "")
                        error = endpoint.get("error", "Unknown error")
                        status_code = endpoint.get("status_code", "")
                        
                        report.append(f"❌ {service.upper()} - {method} {path}")
                        report.append(f"   Status: {status_code}")
                        report.append(f"   Error: {str(error)[:200]}")
                        report.append("")
            
            if not error_found:
                report.append("✅ No endpoint errors found!")
        
        # Docker Log Errors
        report.append("\n🐳 DOCKER LOG ERRORS:")
        report.append("-" * 30)
        for container, log_data in docker_logs.items():
            errors = log_data.get("errors", [])
            if errors:
                report.append(f"\n⚠️ {container.upper()}:")
                for error in errors[:5]:  # Show first 5 errors
                    report.append(f"   [{error.get('timestamp', 'N/A')}] {error.get('content', '')}")
        
        return "\n".join(report)

def main():
    """Main execution function."""
    print("🎯 Quenty Microservices - Comprehensive Testing Suite")
    print("=" * 60)
    
    try:
        # Initialize components
        log_extractor = DockerLogExtractor()
        endpoint_tester = EndpointTester()
        report_generator = ReportGenerator()
        
        # Step 1: Extract Docker logs (before testing to avoid noise)
        print("📋 Phase 1: Extracting Docker logs...")
        docker_logs = log_extractor.extract_logs(minutes_back=15)
        print(f"✅ Extracted logs from {len(docker_logs)} containers")
        
        # Step 2: Run endpoint tests
        print("\n📋 Phase 2: Running endpoint tests...")
        test_results = endpoint_tester.run_comprehensive_test()
        
        # Step 3: Generate reports
        print("\n📋 Phase 3: Generating reports...")
        reports = report_generator.generate_reports(test_results, docker_logs)
        
        # Print summary
        print("\n📊 TEST EXECUTION SUMMARY")
        print("-" * 40)
        
        if "summary" in test_results:
            summary = test_results["summary"]
            health_summary = summary.get("health_check_summary", {})
            endpoint_summary = summary.get("endpoint_test_summary", {})
            
            print(f"🏥 Health Checks: {health_summary.get('healthy_services', 0)}/{health_summary.get('total_services', 0)} services healthy")
            print(f"🔄 Endpoints: {endpoint_summary.get('successful_endpoints', 0)}/{endpoint_summary.get('total_endpoints', 0)} successful")
        
        # Docker logs summary
        total_errors = sum(log_data.get("error_count", 0) for log_data in docker_logs.values())
        print(f"🐳 Docker Logs: {total_errors} errors found across all containers")
        
        print(f"\n📁 Reports generated:")
        for report_type, file_path in reports.items():
            print(f"   {report_type.upper()}: {file_path}")
        
        print(f"\n✅ Comprehensive testing completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during test execution: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    # Check if required tools are available
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker is not available or not running")
        sys.exit(1)
    
    # Run the main function
    main()