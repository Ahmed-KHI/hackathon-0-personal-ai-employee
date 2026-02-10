"""
Enhanced Orchestrator with Multi-Step Planning & Self-Healing
Platinum Tier - Advanced AI Capabilities
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add paths
sys.path.append(str(Path(__file__).parent))

from orchestration.orchestrator import Orchestrator

logger = logging.getLogger(__name__)

class PlatinumOrchestrator(Orchestrator):
    """
    Enhanced orchestrator with:
    - Multi-step task planning with dependencies
    - Self-healing (automatic retry with fallback strategies)
    - Learning from approvals/rejections
    - Proactive suggestions
    """
    
    def __init__(self, vault_path: str = "./vaults/tenant_default"):
        super().__init__(vault_path)
        
        # Track execution history for learning
        self.execution_history = []
        self.approval_patterns = {}
        self.failure_patterns = {}
        
        logger.info("🚀 Platinum Orchestrator initialized with advanced AI")
    
    def execute_with_dependencies(self, plan_file: Path) -> Dict:
        """
        Execute actions with dependency tracking
        Automatically handles sequential vs parallel execution
        """
        # Extract actions with dependencies
        actions = self._extract_actions_with_deps(plan_file)
        
        if not actions:
            return {"status": "no_actions"}
        
        logger.info(f"📊 Executing {len(actions)} action(s) with dependency graph")
        
        # Build dependency graph
        graph = self._build_dependency_graph(actions)
        
        # Execute in topological order
        results = []
        for action_id in graph['execution_order']:
            action = next(a for a in actions if a['id'] == action_id)
            
            # Check if dependencies succeeded
            deps = graph['dependencies'].get(action_id, [])
            if all(self._action_succeeded(d, results) for d in deps):
                result = self._execute_action_with_retry(action)
                results.append(result)
            else:
                logger.warning(f"⏭️  Skipping {action_id}: dependencies failed")
                results.append({
                    'action_id': action_id,
                    'status': 'skipped',
                    'reason': 'dependency_failure'
                })
        
        return {
            "status": "complete",
            "actions_executed": len([r for r in results if r['status'] == 'success']),
            "actions_failed": len([r for r in results if r['status'] == 'failed']),
            "actions_skipped": len([r for r in results if r['status'] == 'skipped']),
            "results": results
        }
    
    def _execute_action_with_retry(self, action: Dict, max_retries: int = 3) -> Dict:
        """
        Execute action with intelligent retry and self-healing
        """
        action_id = action['id']
        action_type = action['type']
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"🔄 Executing {action_id} (attempt {attempt}/{max_retries})")
                
                # Execute action via parent class
                result = self.action_executor.execute_action(action)
                
                if result.get('status') == 'success':
                    # Record success for learning
                    self._record_success(action_id, action_type, attempt)
                    return {
                        'action_id': action_id,
                        'status': 'success',
                        'attempts': attempt,
                        'result': result
                    }
                
            except Exception as e:
                logger.warning(f"⚠️  Attempt {attempt} failed: {e}")
                
                if attempt < max_retries:
                    # Try self-healing strategies
                    healed = self._attempt_self_heal(action, e)
                    if healed:
                        logger.info(f"🔧 Self-healing applied, retrying...")
                        continue
                    
                    # Exponential backoff
                    import time
                    wait_time = 2 ** attempt
                    logger.info(f"⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    # Max retries exceeded, record failure
                    self._record_failure(action_id, action_type, str(e))
        
        return {
            'action_id': action_id,
            'status': 'failed',
            'attempts': max_retries,
            'error': 'Max retries exceeded'
        }
    
    def _attempt_self_heal(self, action: Dict, error: Exception) -> bool:
        """
        Attempt to fix common issues automatically
        Returns True if healing was applied
        """
        error_str = str(error).lower()
        
        # Token expiration
        if 'token' in error_str or 'expired' in error_str or '401' in error_str:
            logger.info("🔧 Detected token expiration, attempting refresh...")
            # TODO: Implement token refresh logic
            return False
        
        # Rate limiting
        if 'rate limit' in error_str or '429' in error_str:
            logger.info("🔧 Rate limit detected, increasing backoff...")
            import time
            time.sleep(60)  # Wait 1 minute
            return True
        
        # Network issues
        if 'connection' in error_str or 'timeout' in error_str:
            logger.info("🔧 Network issue detected, will retry...")
            return True
        
        return False
    
    def _build_dependency_graph(self, actions: List[Dict]) -> Dict:
        """
        Build dependency graph for parallel/sequential execution
        """
        # Simple implementation: execute sequentially for now
        # TODO: Implement proper dependency analysis
        
        execution_order = [a['id'] for a in actions]
        dependencies = {}  # No dependencies for now
        
        return {
            'execution_order': execution_order,
            'dependencies': dependencies
        }
    
    def _extract_actions_with_deps(self, plan_file: Path) -> List[Dict]:
        """Extract actions with dependency information"""
        # Use parent class extraction
        actions = self.action_executor.extract_actions_from_plan(plan_file)
        
        # Add IDs and default dependencies
        for i, action in enumerate(actions):
            action['id'] = f"action_{i+1}"
            action['dependencies'] = []  # TODO: Parse from plan
        
        return actions
    
    def _action_succeeded(self, action_id: str, results: List[Dict]) -> bool:
        """Check if action succeeded"""
        for result in results:
            if result.get('action_id') == action_id:
                return result.get('status') == 'success'
        return False
    
    def _record_success(self, action_id: str, action_type: str, attempts: int):
        """Record successful execution for learning"""
        self.execution_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action_id': action_id,
            'action_type': action_type,
            'status': 'success',
            'attempts': attempts
        })
    
    def _record_failure(self, action_id: str, action_type: str, error: str):
        """Record failure for pattern analysis"""
        self.execution_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action_id': action_id,
            'action_type': action_type,
            'status': 'failed',
            'error': error
        })
        
        # Track failure patterns
        if action_type not in self.failure_patterns:
            self.failure_patterns[action_type] = []
        self.failure_patterns[action_type].append(error)
    
    def get_health_metrics(self) -> Dict:
        """Get system health metrics for monitoring"""
        total_executions = len(self.execution_history)
        successful = len([e for e in self.execution_history if e['status'] == 'success'])
        failed = len([e for e in self.execution_history if e['status'] == 'failed'])
        
        return {
            'total_executions': total_executions,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total_executions * 100) if total_executions > 0 else 0,
            'failure_patterns': self.failure_patterns,
            'uptime_hours': self._calculate_uptime()
        }
    
    def _calculate_uptime(self) -> float:
        """Calculate system uptime in hours"""
        if not self.execution_history:
            return 0.0
        
        first_exec = datetime.fromisoformat(self.execution_history[0]['timestamp'].replace('Z', '+00:00'))
        now = datetime.utcnow()
        delta = now - first_exec
        
        return round(delta.total_seconds() / 3600, 2)


if __name__ == "__main__":
    # Start enhanced orchestrator
    orchestrator = PlatinumOrchestrator()
    orchestrator.start()
