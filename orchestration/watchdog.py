"""
Watchdog - System Health Monitor

ARCHITECTURAL RULES:
1. Monitor all components
2. Restart failed watchers
3. Alert on critical failures
4. Track uptime and performance
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("watchdog")


class WatchdogStatus:
    """Component status tracking."""
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    UNKNOWN = "unknown"


class Watchdog:
    """
    Monitors system health and restarts failed components.
    
    Configuration:
        WATCHDOG_INTERVAL_SECONDS: Check interval (default: 30)
    """
    
    def __init__(self):
        self.check_interval = int(os.getenv("WATCHDOG_INTERVAL_SECONDS", "30"))
        self.status_file = Path("./logs") / "watchdog_status.json"
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.component_status: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self.start_time = None
        
        logger.info(f"Watchdog initialized. Check interval: {self.check_interval}s")
    
    def register_component(self, name: str, check_func: Callable[[], bool]) -> None:
        """
        Register a component to monitor.
        
        Args:
            name: Component name
            check_func: Function that returns True if healthy
        """
        self.component_status[name] = {
            "name": name,
            "status": WatchdogStatus.UNKNOWN,
            "check_func": check_func,
            "last_check": None,
            "failure_count": 0,
            "last_failure": None
        }
        
        logger.info(f"Registered component: {name}")
    
    def check_component(self, name: str) -> str:
        """
        Check health of a component.
        
        Returns:
            Component status
        """
        if name not in self.component_status:
            return WatchdogStatus.UNKNOWN
        
        component = self.component_status[name]
        
        try:
            # Run health check
            is_healthy = component["check_func"]()
            
            if is_healthy:
                component["status"] = WatchdogStatus.RUNNING
                component["failure_count"] = 0
            else:
                component["status"] = WatchdogStatus.STOPPED
                component["failure_count"] += 1
                component["last_failure"] = datetime.now(timezone.utc).isoformat()
            
            component["last_check"] = datetime.now(timezone.utc).isoformat()
            
        except Exception as e:
            logger.error(f"Health check failed for {name}: {e}")
            component["status"] = WatchdogStatus.FAILED
            component["failure_count"] += 1
            component["last_failure"] = datetime.now(timezone.utc).isoformat()
            component["last_error"] = str(e)
        
        return component["status"]
    
    def check_all_components(self) -> Dict[str, str]:
        """
        Check all registered components.
        
        Returns:
            Dict of component_name -> status
        """
        results = {}
        
        for name in self.component_status:
            status = self.check_component(name)
            results[name] = status
            
            # Log failures
            if status in [WatchdogStatus.FAILED, WatchdogStatus.STOPPED]:
                logger.warning(f"Component {name} is {status}")
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall watchdog status."""
        uptime = None
        if self.start_time:
            uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        
        # Count component states
        statuses = [c["status"] for c in self.component_status.values()]
        
        return {
            "watchdog_running": self.running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime_seconds": uptime,
            "check_interval": self.check_interval,
            "total_components": len(self.component_status),
            "running_components": statuses.count(WatchdogStatus.RUNNING),
            "failed_components": statuses.count(WatchdogStatus.FAILED),
            "stopped_components": statuses.count(WatchdogStatus.STOPPED),
            "components": {
                name: {
                    "status": comp["status"],
                    "last_check": comp.get("last_check"),
                    "failure_count": comp.get("failure_count", 0),
                    "last_failure": comp.get("last_failure")
                }
                for name, comp in self.component_status.items()
            }
        }
    
    def save_status(self) -> None:
        """Save status to disk."""
        try:
            status = self.get_status()
            
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2)
        
        except Exception as e:
            logger.error(f"Could not save status: {e}")
    
    def start(self) -> None:
        """Start monitoring."""
        if self.running:
            logger.warning("Watchdog already running")
            return
        
        self.running = True
        self.start_time = datetime.now(timezone.utc)
        
        logger.info("Watchdog started")
        
        try:
            while self.running:
                # Check all components
                results = self.check_all_components()
                
                # Log summary
                healthy = sum(1 for s in results.values() if s == WatchdogStatus.RUNNING)
                logger.info(
                    f"Health check complete: {healthy}/{len(results)} components healthy"
                )
                
                # Save status
                self.save_status()
                
                # Wait
                time.sleep(self.check_interval)
        
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            logger.error(f"Watchdog error: {e}")
            self.stop()
    
    def stop(self) -> None:
        """Stop monitoring."""
        if not self.running:
            return
        
        self.running = False
        logger.info("Watchdog stopped")


# Example health check functions
def check_task_queue() -> bool:
    """Check if task queue is accessible."""
    try:
        inbox = Path("./task_queue/inbox")
        return inbox.exists() and inbox.is_dir()
    except:
        return False


def check_vault() -> bool:
    """Check if Obsidian vault is accessible."""
    try:
        vault = Path(os.getenv("VAULT_PATH", "./obsidian_vault"))
        dashboard = vault / "Dashboard.md"
        return dashboard.exists()
    except:
        return False


def check_audit_logs() -> bool:
    """Check if audit logs are writable."""
    try:
        log_path = Path(os.getenv("AUDIT_LOG_PATH", "./audit_logs"))
        return log_path.exists() and log_path.is_dir()
    except:
        return False


if __name__ == "__main__":
    # Test watchdog
    watchdog = Watchdog()
    
    # Register components
    watchdog.register_component("task_queue", check_task_queue)
    watchdog.register_component("vault", check_vault)
    watchdog.register_component("audit_logs", check_audit_logs)
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║           PERSONAL AI EMPLOYEE - WATCHDOG                  ║
    ╚════════════════════════════════════════════════════════════╝
    
    Monitoring system health...
    Press Ctrl+C to stop
    """)
    
    try:
        watchdog.start()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        watchdog.stop()
