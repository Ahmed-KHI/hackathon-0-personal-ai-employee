"""
Retry Handler - Graceful Failure Recovery

ARCHITECTURAL RULES:
1. Exponential backoff for retries
2. Max retry attempts configurable
3. Log all retry attempts
4. Move to failed queue if exhausted
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("retry_handler")


class RetryExhausted(Exception):
    """Raised when all retry attempts are exhausted."""
    pass


class RetryHandler:
    """
    Handles retries with exponential backoff.
    
    Configuration:
        MAX_RETRY_ATTEMPTS: Number of retries (default: 3)
        RETRY_BACKOFF_SECONDS: Initial backoff (default: 60)
    """
    
    def __init__(self):
        self.max_attempts = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
        self.backoff_seconds = int(os.getenv("RETRY_BACKOFF_SECONDS", "60"))
        
        logger.info(
            f"Retry handler initialized. "
            f"Max attempts: {self.max_attempts}, "
            f"Backoff: {self.backoff_seconds}s"
        )
    
    def execute_with_retry(
        self,
        func: Callable,
        *args,
        task_id: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Execute a function with retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments for func
            task_id: Task ID for logging
            **kwargs: Keyword arguments for func
        
        Returns:
            Result of func
        
        Raises:
            RetryExhausted if all attempts fail
        """
        attempt = 0
        last_error = None
        
        while attempt <= self.max_attempts:
            try:
                attempt += 1
                
                if attempt > 1:
                    logger.info(
                        f"Retry attempt {attempt}/{self.max_attempts + 1} "
                        f"for task {task_id}"
                    )
                
                # Execute function
                result = func(*args, **kwargs)
                
                if attempt > 1:
                    logger.info(f"Retry successful for task {task_id}")
                
                return result
                
            except Exception as e:
                last_error = e
                
                logger.warning(
                    f"Attempt {attempt} failed for task {task_id}: {e}"
                )
                
                # If not last attempt, wait with exponential backoff
                if attempt <= self.max_attempts:
                    wait_time = self.backoff_seconds * (2 ** (attempt - 1))
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
        
        # All attempts exhausted
        logger.error(
            f"All retry attempts exhausted for task {task_id}. "
            f"Last error: {last_error}"
        )
        
        raise RetryExhausted(
            f"Failed after {self.max_attempts + 1} attempts. "
            f"Last error: {last_error}"
        )
    
    def should_retry(self, error: Exception) -> bool:
        """
        Determine if an error is retryable.
        
        Args:
            error: The exception that occurred
        
        Returns:
            True if should retry, False if permanent failure
        """
        # Network errors are retryable
        if isinstance(error, (ConnectionError, TimeoutError)):
            return True
        
        # API rate limits are retryable
        error_str = str(error).lower()
        if any(word in error_str for word in ['rate limit', 'too many requests', '429']):
            return True
        
        # Temporary errors are retryable
        if any(word in error_str for word in ['temporary', 'timeout', 'unavailable']):
            return True
        
        # Authentication and authorization errors are NOT retryable
        if any(word in error_str for word in ['unauthorized', '401', '403', 'forbidden']):
            return False
        
        # Default: retry
        return True


# Global instance
_retry_handler = None


def get_retry_handler() -> RetryHandler:
    """Get global retry handler instance."""
    global _retry_handler
    if _retry_handler is None:
        _retry_handler = RetryHandler()
    return _retry_handler


# Convenience function
def execute_with_retry(func: Callable, *args, **kwargs) -> Any:
    """Execute a function with retry logic."""
    return get_retry_handler().execute_with_retry(func, *args, **kwargs)


if __name__ == "__main__":
    # Test retry handler
    handler = get_retry_handler()
    
    # Test function that fails a few times then succeeds
    attempt_count = 0
    
    def flaky_function():
        global attempt_count
        attempt_count += 1
        
        if attempt_count < 3:
            print(f"Attempt {attempt_count}: Failing...")
            raise ConnectionError("Network error")
        else:
            print(f"Attempt {attempt_count}: Success!")
            return "Success!"
    
    try:
        result = handler.execute_with_retry(
            flaky_function,
            task_id="test-retry"
        )
        print(f"\nResult: {result}")
    except RetryExhausted as e:
        print(f"\nFailed: {e}")
