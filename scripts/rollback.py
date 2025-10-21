#!/usr/bin/env python3
"""
Production deployment rollback mechanism for ClinChat-RAG
Provides automated rollback capabilities with validation
"""

import subprocess
import json
import time
import sys
import argparse
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DeploymentInfo:
    """Deployment information structure"""
    revision: int
    image: str
    timestamp: str
    status: str
    ready_replicas: int
    total_replicas: int

@dataclass
class RollbackResult:
    """Rollback operation result"""
    success: bool
    previous_revision: int
    current_revision: int
    message: str
    duration_seconds: float

class ProductionRollback:
    """Production rollback system with validation"""
    
    def __init__(self, namespace: str = "clinchat-rag"):
        self.namespace = namespace
        self.deployment_name = "clinchat-rag-api"
        
    def get_deployment_history(self) -> List[DeploymentInfo]:
        """Get deployment rollout history"""
        try:
            # Get rollout history
            cmd = ["kubectl", "rollout", "history", f"deployment/{self.deployment_name}", 
                   "-n", self.namespace, "--output=json"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            history_data = json.loads(result.stdout)
            deployments = []
            
            # Parse deployment history
            for item in history_data.get('items', []):
                metadata = item.get('metadata', {})
                spec = item.get('spec', {})
                status = item.get('status', {})
                
                revision = int(metadata.get('annotations', {}).get('deployment.kubernetes.io/revision', '0'))
                
                # Get image from containers
                containers = spec.get('template', {}).get('spec', {}).get('containers', [])
                image = containers[0].get('image', 'unknown') if containers else 'unknown'
                
                deployment_info = DeploymentInfo(
                    revision=revision,
                    image=image,
                    timestamp=metadata.get('creationTimestamp', ''),
                    status=status.get('phase', 'Unknown'),
                    ready_replicas=status.get('readyReplicas', 0),
                    total_replicas=status.get('replicas', 0)
                )
                deployments.append(deployment_info)
            
            # Sort by revision (newest first)
            deployments.sort(key=lambda x: x.revision, reverse=True)
            return deployments
            
        except Exception as e:
            logger.error(f"Failed to get deployment history: {str(e)}")
            return []
    
    def get_current_deployment_status(self) -> Dict[str, any]:
        """Get current deployment status"""
        try:
            cmd = ["kubectl", "get", f"deployment/{self.deployment_name}", 
                   "-n", self.namespace, "-o", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            deployment_data = json.loads(result.stdout)
            status = deployment_data.get('status', {})
            
            return {
                'ready_replicas': status.get('readyReplicas', 0),
                'total_replicas': status.get('replicas', 0),
                'updated_replicas': status.get('updatedReplicas', 0),
                'available_replicas': status.get('availableReplicas', 0),
                'conditions': status.get('conditions', [])
            }
            
        except Exception as e:
            logger.error(f"Failed to get deployment status: {str(e)}")
            return {}
    
    def validate_system_health(self) -> Tuple[bool, List[str]]:
        """Validate system health before/after rollback"""
        issues = []
        
        try:
            # Check deployment status
            deployment_status = self.get_current_deployment_status()
            ready = deployment_status.get('ready_replicas', 0)
            total = deployment_status.get('total_replicas', 0)
            
            if ready != total:
                issues.append(f"Not all replicas ready: {ready}/{total}")
            
            # Check pods status
            cmd = ["kubectl", "get", "pods", "-n", self.namespace, 
                   "-l", f"app={self.deployment_name}", "-o", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            pods_data = json.loads(result.stdout)
            pods = pods_data.get('items', [])
            
            for pod in pods:
                pod_name = pod.get('metadata', {}).get('name', '')
                pod_status = pod.get('status', {}).get('phase', '')
                
                if pod_status != 'Running':
                    issues.append(f"Pod {pod_name} not running: {pod_status}")
                
                # Check container statuses
                container_statuses = pod.get('status', {}).get('containerStatuses', [])
                for container in container_statuses:
                    if not container.get('ready', False):
                        container_name = container.get('name', '')
                        issues.append(f"Container {container_name} in pod {pod_name} not ready")
            
            # Run smoke tests
            smoke_test_result = self.run_smoke_tests()
            if not smoke_test_result['success']:
                issues.extend(smoke_test_result['errors'])
            
            return len(issues) == 0, issues
            
        except Exception as e:
            issues.append(f"Health check failed: {str(e)}")
            return False, issues
    
    def run_smoke_tests(self) -> Dict[str, any]:
        """Run basic smoke tests"""
        try:
            # Run the smoke test script
            cmd = ["python", "scripts/smoke-tests.py", "--environment", "production"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return {'success': True, 'errors': []}
            else:
                return {
                    'success': False, 
                    'errors': [f"Smoke tests failed: {result.stderr}"]
                }
                
        except subprocess.TimeoutExpired:
            return {'success': False, 'errors': ['Smoke tests timed out']}
        except Exception as e:
            return {'success': False, 'errors': [f"Smoke test error: {str(e)}"]}
    
    def perform_rollback(self, target_revision: Optional[int] = None, 
                        dry_run: bool = False) -> RollbackResult:
        """Perform deployment rollback"""
        start_time = time.time()
        
        try:
            # Get current deployment info
            history = self.get_deployment_history()
            if len(history) < 2:
                return RollbackResult(
                    success=False,
                    previous_revision=0,
                    current_revision=0,
                    message="Not enough deployment history for rollback",
                    duration_seconds=time.time() - start_time
                )
            
            current_revision = history[0].revision
            
            # Determine target revision
            if target_revision is None:
                # Rollback to previous revision
                target_revision = history[1].revision
            
            # Validate target revision exists
            target_deployment = next((d for d in history if d.revision == target_revision), None)
            if not target_deployment:
                return RollbackResult(
                    success=False,
                    previous_revision=current_revision,
                    current_revision=current_revision,
                    message=f"Target revision {target_revision} not found in history",
                    duration_seconds=time.time() - start_time
                )
            
            logger.info(f"Rolling back from revision {current_revision} to {target_revision}")
            logger.info(f"Target image: {target_deployment.image}")
            
            if dry_run:
                return RollbackResult(
                    success=True,
                    previous_revision=current_revision,
                    current_revision=target_revision,
                    message=f"DRY RUN: Would rollback to revision {target_revision}",
                    duration_seconds=time.time() - start_time
                )
            
            # Perform the rollback
            cmd = ["kubectl", "rollout", "undo", f"deployment/{self.deployment_name}",
                   "-n", self.namespace, f"--to-revision={target_revision}"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Rollback initiated: {result.stdout}")
            
            # Wait for rollout to complete
            logger.info("Waiting for rollout to complete...")
            cmd = ["kubectl", "rollout", "status", f"deployment/{self.deployment_name}",
                   "-n", self.namespace, "--timeout=600s"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info("Rollout completed")
            
            # Validate system health after rollback
            logger.info("Validating system health after rollback...")
            health_ok, health_issues = self.validate_system_health()
            
            if not health_ok:
                logger.error("Health validation failed after rollback!")
                for issue in health_issues:
                    logger.error(f"  - {issue}")
                
                return RollbackResult(
                    success=False,
                    previous_revision=current_revision,
                    current_revision=target_revision,
                    message=f"Rollback completed but health validation failed: {'; '.join(health_issues)}",
                    duration_seconds=time.time() - start_time
                )
            
            logger.info("Rollback completed successfully and health validation passed")
            
            return RollbackResult(
                success=True,
                previous_revision=current_revision,
                current_revision=target_revision,
                message=f"Successfully rolled back to revision {target_revision}",
                duration_seconds=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
            return RollbackResult(
                success=False,
                previous_revision=current_revision if 'current_revision' in locals() else 0,
                current_revision=current_revision if 'current_revision' in locals() else 0,
                message=f"Rollback failed: {str(e)}",
                duration_seconds=time.time() - start_time
            )
    
    def emergency_rollback(self) -> RollbackResult:
        """Emergency rollback to last known good deployment"""
        logger.warning("EMERGENCY ROLLBACK INITIATED!")
        
        # Get deployment history
        history = self.get_deployment_history()
        if len(history) < 2:
            return RollbackResult(
                success=False,
                previous_revision=0,
                current_revision=0,
                message="No previous deployment available for emergency rollback",
                duration_seconds=0
            )
        
        # Find last known good deployment (first one that was successfully deployed)
        target_deployment = None
        for deployment in history[1:]:  # Skip current deployment
            if deployment.ready_replicas == deployment.total_replicas:
                target_deployment = deployment
                break
        
        if not target_deployment:
            # Fallback to previous deployment regardless of status
            target_deployment = history[1]
        
        logger.warning(f"Emergency rollback target: revision {target_deployment.revision}")
        
        # Perform emergency rollback
        return self.perform_rollback(target_deployment.revision)
    
    def create_rollback_report(self, result: RollbackResult) -> Dict[str, any]:
        """Create rollback report for audit purposes"""
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'rollback_result': {
                'success': result.success,
                'previous_revision': result.previous_revision,
                'current_revision': result.current_revision,
                'message': result.message,
                'duration_seconds': result.duration_seconds
            },
            'deployment_history': [],
            'system_status': {}
        }
        
        # Add deployment history
        history = self.get_deployment_history()
        for deployment in history[:5]:  # Last 5 deployments
            report['deployment_history'].append({
                'revision': deployment.revision,
                'image': deployment.image,
                'timestamp': deployment.timestamp,
                'status': deployment.status
            })
        
        # Add current system status
        report['system_status'] = self.get_current_deployment_status()
        
        return report

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description='ClinChat-RAG Production Rollback Tool')
    parser.add_argument('--namespace', default='clinchat-rag', 
                       help='Kubernetes namespace (default: clinchat-rag)')
    parser.add_argument('--revision', type=int, 
                       help='Target revision to rollback to (default: previous)')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be rolled back without performing it')
    parser.add_argument('--emergency', action='store_true', 
                       help='Perform emergency rollback to last known good deployment')
    parser.add_argument('--status', action='store_true', 
                       help='Show current deployment status and history')
    parser.add_argument('--validate-health', action='store_true', 
                       help='Only validate system health')
    
    args = parser.parse_args()
    
    # Initialize rollback system
    rollback_system = ProductionRollback(namespace=args.namespace)
    
    # Handle different operations
    if args.status:
        print("📊 Current Deployment Status")
        print("=" * 50)
        
        # Show current status
        status = rollback_system.get_current_deployment_status()
        print(f"Ready Replicas: {status.get('ready_replicas', 0)}/{status.get('total_replicas', 0)}")
        print(f"Updated Replicas: {status.get('updated_replicas', 0)}")
        print(f"Available Replicas: {status.get('available_replicas', 0)}")
        
        # Show deployment history
        print("\n📜 Deployment History")
        print("=" * 50)
        history = rollback_system.get_deployment_history()
        for i, deployment in enumerate(history[:10]):  # Show last 10
            marker = "→" if i == 0 else " "
            print(f"{marker} Revision {deployment.revision}: {deployment.image}")
            print(f"   Status: {deployment.status}, Ready: {deployment.ready_replicas}/{deployment.total_replicas}")
            print(f"   Timestamp: {deployment.timestamp}")
            print()
    
    elif args.validate_health:
        print("🏥 Validating System Health")
        print("=" * 50)
        
        health_ok, issues = rollback_system.validate_system_health()
        
        if health_ok:
            print("✅ System health validation passed")
            sys.exit(0)
        else:
            print("❌ System health validation failed:")
            for issue in issues:
                print(f"   - {issue}")
            sys.exit(1)
    
    elif args.emergency:
        print("🚨 EMERGENCY ROLLBACK INITIATED")
        print("=" * 50)
        
        result = rollback_system.emergency_rollback()
        
        if result.success:
            print(f"✅ Emergency rollback successful: {result.message}")
            print(f"   Duration: {result.duration_seconds:.2f} seconds")
        else:
            print(f"❌ Emergency rollback failed: {result.message}")
            sys.exit(1)
    
    else:
        # Regular rollback
        if args.dry_run:
            print("🔍 DRY RUN: Rollback Analysis")
        else:
            print("🔄 Performing Production Rollback")
        print("=" * 50)
        
        result = rollback_system.perform_rollback(
            target_revision=args.revision,
            dry_run=args.dry_run
        )
        
        if result.success:
            print(f"✅ Rollback successful: {result.message}")
            print(f"   Previous revision: {result.previous_revision}")
            print(f"   Current revision: {result.current_revision}")
            print(f"   Duration: {result.duration_seconds:.2f} seconds")
        else:
            print(f"❌ Rollback failed: {result.message}")
            sys.exit(1)
    
    # Generate rollback report
    if not args.status and not args.validate_health:
        report = rollback_system.create_rollback_report(result)
        
        # Save report to file
        report_file = f"rollback_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Rollback report saved to: {report_file}")

if __name__ == '__main__':
    main()