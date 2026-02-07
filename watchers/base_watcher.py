"""
Base Watcher - Abstract Class for All Event Watchers

ARCHITECTURAL RULES:
1. Watchers PERCEIVE events, never take actions
2. Output: JSON task files in task_queue/inbox/
3. No reasoning, no API calls (except for event detection)
4. Must be subclassed - define on_event() method
"""

import os
import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class BaseWatcher(ABC):
    """
    Abstract base class for all watchers in the Personal AI Employee system.
    
    Watchers are responsible for:
    - Detecting events (email, file changes, API webhooks, etc.)
    - Creating task JSON files in task_queue/inbox/
    - NEVER taking actions or making decisions
    
    Subclasses must implement:
    - on_event(): Define what constitutes an "event"
    - start(): Start watching for events
    - stop(): Clean shutdown
    """
    
    def __init__(self, watcher_name: str):
        self.watcher_name = watcher_name
        self.logger = logging.getLogger(f"watchers.{watcher_name}")
        self.inbox_path = Path(os.getenv("VAULT_PATH", "./obsidian_vault")).parent / "task_queue" / "inbox"
        self.inbox_path.mkdir(parents=True, exist_ok=True)
        self.running = False
        
        self.logger.info(f"{watcher_name} initialized. Inbox: {self.inbox_path}")
    
    def create_task(
        self,
        task_type: str,
        context: Dict[str, Any],
        priority: str = "normal",
        required_skills: Optional[list] = None,
        hitl_required: bool = False
    ) -> str:
        """
        Create a task file in task_queue/inbox/
        
        Args:
            task_type: Type of task (e.g., "email_response", "file_process")
            context: Event-specific data
            priority: "critical", "high", "normal", "low"
            required_skills: List of agent skill files needed (e.g., ["email_skills", "finance_skills"])
            hitl_required: Whether this task requires human approval
        
        Returns:
            task_id: UUID of created task
        """
        task_id = str(uuid.uuid4())
        
        task = {
            "task_id": task_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": self.watcher_name,
            "type": task_type,
            "priority": priority,
            "context": context,
            "required_skills": required_skills or [],
            "hitl_required": hitl_required,
            "status": "pending"
        }
        
        task_file = self.inbox_path / f"{task_id}.json"
        
        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(task, f, indent=2, ensure_ascii=False)
        
        self.logger.info(
            f"Task created: {task_id} | Type: {task_type} | Priority: {priority} | HITL: {hitl_required}"
        )
        
        return task_id
    
    @abstractmethod
    def on_event(self, event_data: Any) -> None:
        """
        Handle an event by creating a task.
        
        This method is called when the watcher detects an event.
        Subclasses must implement this to define event handling logic.
        
        Args:
            event_data: Raw event data (varies by watcher type)
        """
        pass
    
    @abstractmethod
    def start(self) -> None:
        """
        Start watching for events.
        
        This method should:
        1. Initialize connections (API clients, file watchers, etc.)
        2. Set self.running = True
        3. Begin event loop
        """
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """
        Stop watching and clean up resources.
        
        This method should:
        1. Set self.running = False
        2. Close connections
        3. Release resources
        """
        pass
    
    def is_running(self) -> bool:
        """Check if watcher is currently running."""
        return self.running
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current watcher status.
        
        Returns:
            Dict with status information
        """
        return {
            "watcher_name": self.watcher_name,
            "running": self.running,
            "inbox_path": str(self.inbox_path),
            "tasks_created_lifetime": self._count_tasks_created()
        }
    
    def _count_tasks_created(self) -> int:
        """Count tasks created by this watcher (best-effort)."""
        try:
            count = 0
            for task_file in self.inbox_path.glob("*.json"):
                with open(task_file, "r") as f:
                    task = json.load(f)
                    if task.get("source") == self.watcher_name:
                        count += 1
            return count
        except Exception as e:
            self.logger.warning(f"Could not count tasks: {e}")
            return 0


class WatcherError(Exception):
    """Base exception for watcher-related errors."""
    pass


class WatcherConfigError(WatcherError):
    """Raised when watcher configuration is invalid."""
    pass


class WatcherConnectionError(WatcherError):
    """Raised when watcher cannot connect to event source."""
    pass
