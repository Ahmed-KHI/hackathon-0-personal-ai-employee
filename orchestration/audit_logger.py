"""
Audit Logger - Immutable Compliance Trail

ARCHITECTURAL RULES:
1. Append-only logs (no modifications)
2. Cryptographic signatures for integrity
3. Every action must be logged
4. Logs are permanent (respect retention policy)
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

load_dotenv()

# Create module-level logger with unique name
_module_logger = logging.getLogger("audit_logger_module")


class AuditLogger:
    """
    Immutable audit trail for compliance.
    
    All actions taken by the AI Employee are logged with:
    - Timestamp (UTC)
    - Action type
    - Task ID
    - Result
    - Cryptographic signature
    
    Logs are append-only and cannot be modified.
    """
    
    def __init__(self):
        self.log_path = Path(os.getenv("AUDIT_LOG_PATH", "./audit_logs"))
        self.log_path.mkdir(parents=True, exist_ok=True)
        
        # Secret for signing (in production, use proper key management)
        self.signing_key = os.getenv("AUDIT_SIGNING_KEY", "default_key_change_me")
        
        _module_logger.info(f"Audit logger initialized. Path: {self.log_path}")
    
    def log(
        self,
        action: str,
        task_id: str,
        result: str,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> str:
        """
        Log an action to the audit trail.
        
        Args:
            action: Action type (e.g., "task_claimed", "email_sent")
            task_id: Associated task ID
            result: Action result ("success", "failure", "pending")
            details: Additional context
            error: Error message if failed
        
        Returns:
            log_entry_id: Unique ID of log entry
        """
        timestamp = datetime.now(timezone.utc)
        
        # Create log entry
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "action": action,
            "task_id": task_id,
            "result": result,
            "details": details or {},
            "error": error
        }
        
        # Add signature
        signature = self._sign_entry(log_entry)
        log_entry["signature"] = signature
        
        # Determine log file (one per day)
        log_file = self.log_path / f"audit_{timestamp.strftime('%Y-%m-%d')}.jsonl"
        
        # Append to log (JSONL format - one JSON object per line)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        
        _module_logger.info(f"Audit log: {action} | {task_id} | {result}")
        
        return signature[:16]  # Return short ID
    
    def _sign_entry(self, entry: Dict[str, Any]) -> str:
        """
        Create cryptographic signature for log entry.
        
        In production, use proper digital signatures (RSA, ECDSA).
        This is a simplified HMAC-like implementation.
        """
        # Create canonical representation
        canonical = json.dumps(entry, sort_keys=True, ensure_ascii=False)
        
        # Sign with key
        signature = hashlib.sha256(
            (canonical + self.signing_key).encode('utf-8')
        ).hexdigest()
        
        return signature
    
    def verify_entry(self, entry: Dict[str, Any]) -> bool:
        """
        Verify integrity of a log entry.
        
        Returns:
            True if signature matches, False if tampered
        """
        stored_signature = entry.pop("signature", None)
        
        if not stored_signature:
            return False
        
        computed_signature = self._sign_entry(entry)
        
        # Restore signature
        entry["signature"] = stored_signature
        
        return stored_signature == computed_signature
    
    def get_logs(
        self,
        task_id: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> list:
        """
        Query audit logs.
        
        Args:
            task_id: Filter by task ID
            action: Filter by action type
            start_date: Filter by start date
            end_date: Filter by end date
        
        Returns:
            List of matching log entries
        """
        matching_entries = []
        
        # Determine which log files to read
        log_files = sorted(self.log_path.glob("audit_*.jsonl"))
        
        for log_file in log_files:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        
                        # Apply filters
                        if task_id and entry.get("task_id") != task_id:
                            continue
                        
                        if action and entry.get("action") != action:
                            continue
                        
                        if start_date or end_date:
                            entry_time = datetime.fromisoformat(entry["timestamp"])
                            if start_date and entry_time < start_date:
                                continue
                            if end_date and entry_time > end_date:
                                continue
                        
                        matching_entries.append(entry)
                        
                    except json.JSONDecodeError:
                        _module_logger.warning(f"Invalid JSON in {log_file}")
                        continue
        
        return matching_entries
    
    def verify_all_logs(self) -> Dict[str, Any]:
        """
        Verify integrity of all audit logs.
        
        Returns:
            Dict with verification results
        """
        total = 0
        valid = 0
        invalid = []
        
        log_files = sorted(self.log_path.glob("audit_*.jsonl"))
        
        for log_file in log_files:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        entry = json.loads(line.strip())
                        total += 1
                        
                        if self.verify_entry(entry):
                            valid += 1
                        else:
                            invalid.append({
                                "file": log_file.name,
                                "line": line_num,
                                "task_id": entry.get("task_id")
                            })
                    except:
                        invalid.append({
                            "file": log_file.name,
                            "line": line_num,
                            "error": "parse_error"
                        })
        
        return {
            "total_entries": total,
            "valid_entries": valid,
            "invalid_entries": len(invalid),
            "integrity": "OK" if len(invalid) == 0 else "COMPROMISED",
            "invalid_details": invalid
        }


# Global instance
_audit_logger = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


# Convenience functions
def audit_log(action: str, task_id: str, result: str, **kwargs) -> str:
    """Convenience function for logging."""
    return get_audit_logger().log(action, task_id, result, **kwargs)


if __name__ == "__main__":
    # Test audit logger
    logger = get_audit_logger()
    
    # Log some test actions
    logger.log("task_claimed", "test-123", "success", details={"source": "filesystem"})
    logger.log("email_sent", "test-123", "success", details={"to": "test@example.com"})
    logger.log("task_completed", "test-123", "success")
    
    # Verify integrity
    result = logger.verify_all_logs()
    print(json.dumps(result, indent=2))
    
    # Query logs
    logs = logger.get_logs(task_id="test-123")
    print(f"\nFound {len(logs)} logs for task test-123")
