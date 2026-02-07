"""
Ralph Loop Protection - Stop-Hook for Infinite Loops

Named after Ralph Wiggum: "I'm in danger!"

ARCHITECTURAL RULES:
1. Track iterations per task
2. Abort after MAX_ITERATIONS (default: 50)
3. Alert human when triggered
4. Prevent runaway API costs
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("ralph_loop")


class RalphLoopException(Exception):
    """Raised when Ralph Loop protection is triggered."""
    pass


class RalphLoop:
    """
    Prevents infinite loops by tracking task iterations.
    
    Each task has a maximum number of allowed iterations.
    If exceeded, the task is aborted and human is alerted.
    """
    
    def __init__(self):
        self.max_iterations = int(os.getenv("RALPH_LOOP_MAX_ITERATIONS", "50"))
        self.state_path = Path("./task_queue") / ".ralph_state.json"
        self.iteration_counts: Dict[str, int] = {}
        self.load_state()
        
        logger.info(f"Ralph Loop initialized. Max iterations: {self.max_iterations}")
    
    def load_state(self) -> None:
        """Load iteration counts from disk."""
        if self.state_path.exists():
            try:
                with open(self.state_path, 'r') as f:
                    self.iteration_counts = json.load(f)
                logger.info(f"Loaded {len(self.iteration_counts)} task states")
            except Exception as e:
                logger.warning(f"Could not load Ralph state: {e}")
                self.iteration_counts = {}
    
    def save_state(self) -> None:
        """Save iteration counts to disk."""
        try:
            with open(self.state_path, 'w') as f:
                json.dump(self.iteration_counts, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save Ralph state: {e}")
    
    def track_iteration(self, task_id: str) -> int:
        """
        Track an iteration for a task.
        
        Args:
            task_id: Task ID
        
        Returns:
            Current iteration count
        
        Raises:
            RalphLoopException if max iterations exceeded
        """
        # Increment counter
        current = self.iteration_counts.get(task_id, 0) + 1
        self.iteration_counts[task_id] = current
        
        logger.info(f"Task {task_id}: Iteration {current}/{self.max_iterations}")
        
        # Check limit
        if current > self.max_iterations:
            logger.critical(
                f"🚨 RALPH LOOP TRIGGERED! Task {task_id} exceeded {self.max_iterations} iterations"
            )
            
            # Save state before raising
            self.save_state()
            
            raise RalphLoopException(
                f"Task {task_id} exceeded maximum iterations ({self.max_iterations}). "
                f"Possible infinite loop detected. Task aborted for safety."
            )
        
        # Save state periodically
        if current % 10 == 0:
            self.save_state()
        
        return current
    
    def reset_task(self, task_id: str) -> None:
        """Reset iteration count for a task."""
        if task_id in self.iteration_counts:
            del self.iteration_counts[task_id]
            self.save_state()
            logger.info(f"Reset iteration count for task {task_id}")
    
    def get_status(self, task_id: str) -> Dict[str, Any]:
        """Get status for a task."""
        count = self.iteration_counts.get(task_id, 0)
        return {
            "task_id": task_id,
            "iterations": count,
            "max_iterations": self.max_iterations,
            "percentage": (count / self.max_iterations) * 100,
            "danger_level": self._get_danger_level(count)
        }
    
    def _get_danger_level(self, count: int) -> str:
        """Get danger level based on iteration count."""
        percentage = (count / self.max_iterations) * 100
        
        if percentage < 50:
            return "safe"
        elif percentage < 75:
            return "warning"
        elif percentage < 90:
            return "danger"
        else:
            return "critical"
    
    def get_all_status(self) -> Dict[str, Any]:
        """Get status for all tracked tasks."""
        return {
            task_id: self.get_status(task_id)
            for task_id in self.iteration_counts
        }
    
    def cleanup_completed_tasks(self, completed_task_ids: list) -> None:
        """Remove completed tasks from tracking."""
        for task_id in completed_task_ids:
            if task_id in self.iteration_counts:
                del self.iteration_counts[task_id]
        
        if completed_task_ids:
            self.save_state()
            logger.info(f"Cleaned up {len(completed_task_ids)} completed tasks")


# Global instance
_ralph_loop = None


def get_ralph_loop() -> RalphLoop:
    """Get global Ralph Loop instance."""
    global _ralph_loop
    if _ralph_loop is None:
        _ralph_loop = RalphLoop()
    return _ralph_loop


# Convenience function
def track_iteration(task_id: str) -> int:
    """Track an iteration. Raises RalphLoopException if limit exceeded."""
    return get_ralph_loop().track_iteration(task_id)


if __name__ == "__main__":
    # Test Ralph Loop
    ralph = get_ralph_loop()
    
    print(f"Max iterations: {ralph.max_iterations}\n")
    
    # Simulate iterations
    test_task_id = "test-ralph-123"
    
    try:
        for i in range(60):  # Will trigger at 50
            count = ralph.track_iteration(test_task_id)
            print(f"Iteration {count}")
            
            if count % 10 == 0:
                status = ralph.get_status(test_task_id)
                print(f"  Status: {status['danger_level']} ({status['percentage']:.1f}%)")
    
    except RalphLoopException as e:
        print(f"\n🚨 {e}")
        print("\nRalph says: 'I'm in danger!'")
