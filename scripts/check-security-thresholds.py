#!/usr/bin/env python3
"""
Security threshold checker for CI/CD pipeline
Validates security scan results against defined thresholds
"""

import json
import sys
import os
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class SecurityThresholds:
    """Security vulnerability thresholds for CI/CD gates"""
    max_critical: int = 0      # No critical vulnerabilities allowed
    max_high: int = 2          # Maximum 2 high vulnerabilities
    max_medium: int = 10       # Maximum 10 medium vulnerabilities
    max_low: int = 50          # Maximum 50 low vulnerabilities

class SecurityChecker:
    def __init__(self, thresholds: SecurityThresholds):
        self.thresholds = thresholds
        self.violations = []
        
    def check_bandit_results(self, bandit_file: str) -> bool:
        """Check Bandit SAST results"""
        if not os.path.exists(bandit_file):
            print(f"⚠️ Bandit report not found: {bandit_file}")
            return True
            
        try:
            with open(bandit_file, 'r') as f:
                data = json.load(f)
                
            # Count issues by severity
            severity_counts = {
                'UNDEFINED': 0, 'LOW': 0, 'MEDIUM': 0, 'HIGH': 0
            }
            
            for result in data.get('results', []):
                severity = result.get('issue_severity', 'UNDEFINED')
                severity_counts[severity] += 1
                
            # Check thresholds
            violations = []
            if severity_counts['HIGH'] > self.thresholds.max_high:
                violations.append(f"HIGH severity: {severity_counts['HIGH']} (max: {self.thresholds.max_high})")
                
            if severity_counts['MEDIUM'] > self.thresholds.max_medium:
                violations.append(f"MEDIUM severity: {severity_counts['MEDIUM']} (max: {self.thresholds.max_medium})")
                
            if severity_counts['LOW'] > self.thresholds.max_low:
                violations.append(f"LOW severity: {severity_counts['LOW']} (max: {self.thresholds.max_low})")
                
            if violations:
                print("🚫 Bandit security threshold violations:")
                for violation in violations:
                    print(f"   - {violation}")
                self.violations.extend([f"Bandit: {v}" for v in violations])
                return False
            else:
                print("✅ Bandit security scan passed")
                return True
                
        except Exception as e:
            print(f"❌ Error processing Bandit results: {e}")
            return False
            
    def check_safety_results(self, safety_file: str) -> bool:
        """Check Safety dependency scan results"""
        if not os.path.exists(safety_file):
            print(f"⚠️ Safety report not found: {safety_file}")
            return True
            
        try:
            with open(safety_file, 'r') as f:
                data = json.load(f)
                
            vulnerabilities = data.get('vulnerabilities', [])
            
            # Count by severity (Safety uses different severity levels)
            severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
            
            for vuln in vulnerabilities:
                # Safety doesn't always provide severity, assume high for known CVEs
                severity = vuln.get('severity', 'high').lower()
                if severity in severity_counts:
                    severity_counts[severity] += 1
                else:
                    severity_counts['high'] += 1  # Default to high
                    
            # Check thresholds
            violations = []
            if severity_counts['critical'] > self.thresholds.max_critical:
                violations.append(f"CRITICAL severity: {severity_counts['critical']} (max: {self.thresholds.max_critical})")
                
            if severity_counts['high'] > self.thresholds.max_high:
                violations.append(f"HIGH severity: {severity_counts['high']} (max: {self.thresholds.max_high})")
                
            if severity_counts['medium'] > self.thresholds.max_medium:
                violations.append(f"MEDIUM severity: {severity_counts['medium']} (max: {self.thresholds.max_medium})")
                
            if violations:
                print("🚫 Safety dependency threshold violations:")
                for violation in violations:
                    print(f"   - {violation}")
                self.violations.extend([f"Safety: {v}" for v in violations])
                return False
            else:
                print("✅ Safety dependency scan passed")
                return True
                
        except Exception as e:
            print(f"❌ Error processing Safety results: {e}")
            return False
            
    def check_semgrep_results(self, semgrep_file: str) -> bool:
        """Check Semgrep SAST results"""
        if not os.path.exists(semgrep_file):
            print(f"⚠️ Semgrep report not found: {semgrep_file}")
            return True
            
        try:
            with open(semgrep_file, 'r') as f:
                data = json.load(f)
                
            results = data.get('results', [])
            
            # Count by severity
            severity_counts = {'ERROR': 0, 'WARNING': 0, 'INFO': 0}
            
            for result in results:
                severity = result.get('extra', {}).get('severity', 'WARNING')
                if severity in severity_counts:
                    severity_counts[severity] += 1
                    
            # Map to our severity levels
            violations = []
            if severity_counts['ERROR'] > self.thresholds.max_high:
                violations.append(f"ERROR (HIGH) severity: {severity_counts['ERROR']} (max: {self.thresholds.max_high})")
                
            if severity_counts['WARNING'] > self.thresholds.max_medium:
                violations.append(f"WARNING (MEDIUM) severity: {severity_counts['WARNING']} (max: {self.thresholds.max_medium})")
                
            if violations:
                print("🚫 Semgrep security threshold violations:")
                for violation in violations:
                    print(f"   - {violation}")
                self.violations.extend([f"Semgrep: {v}" for v in violations])
                return False
            else:
                print("✅ Semgrep security scan passed")
                return True
                
        except Exception as e:
            print(f"❌ Error processing Semgrep results: {e}")
            return False
            
    def check_all_results(self) -> bool:
        """Check all security scan results"""
        print("🔍 Checking security scan results against thresholds...")
        print(f"📊 Thresholds: Critical={self.thresholds.max_critical}, "
              f"High={self.thresholds.max_high}, "
              f"Medium={self.thresholds.max_medium}, "
              f"Low={self.thresholds.max_low}")
        print()
        
        results = []
        
        # Check Bandit results
        results.append(self.check_bandit_results('bandit-report.json'))
        
        # Check Safety results
        results.append(self.check_safety_results('safety-report.json'))
        
        # Check Semgrep results  
        results.append(self.check_semgrep_results('semgrep-report.json'))
        
        # Overall result
        all_passed = all(results)
        
        print()
        if all_passed:
            print("🎉 All security scans passed threshold checks!")
            return True
        else:
            print("💥 Security threshold violations found:")
            for violation in self.violations:
                print(f"   - {violation}")
            print()
            print("🚫 Build failed due to security policy violations")
            return False

def main():
    """Main execution function"""
    # Get environment-specific thresholds
    environment = os.getenv('ENVIRONMENT', 'staging')
    
    if environment == 'production':
        # Stricter thresholds for production
        thresholds = SecurityThresholds(
            max_critical=0,
            max_high=0,
            max_medium=3,
            max_low=10
        )
    else:
        # More lenient for staging/development
        thresholds = SecurityThresholds(
            max_critical=0,
            max_high=2,
            max_medium=10,
            max_low=50
        )
    
    print(f"🛡️ Security Threshold Checker - Environment: {environment}")
    print("=" * 60)
    
    checker = SecurityChecker(thresholds)
    
    if checker.check_all_results():
        print("✅ Security gate passed - deployment can proceed")
        sys.exit(0)
    else:
        print("❌ Security gate failed - blocking deployment")
        sys.exit(1)

if __name__ == '__main__':
    main()