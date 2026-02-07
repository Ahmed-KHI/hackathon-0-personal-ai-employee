"""
Finance Watcher - Silver Tier

Watches bank/finance accounts for transactions via API.
Creates tasks for transactions requiring attention.

DEPLOYMENT TIER: Silver
DEPENDENCIES: plaid-python (or other finance API client)
NOTE: This is a template - adapt to your finance provider
"""

import os
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path

try:
    from plaid import Client as PlaidClient  # type: ignore
    from plaid.errors import PlaidError  # type: ignore
    PLAID_AVAILABLE = True
except ImportError:
    PlaidClient = None  # type: ignore
    PlaidError = None  # type: ignore
    PLAID_AVAILABLE = False

from base_watcher import BaseWatcher, WatcherConfigError, WatcherConnectionError
from dotenv import load_dotenv

load_dotenv()


class FinanceWatcher(BaseWatcher):
    """
    Watches bank accounts for transactions.
    
    Configuration (.env):
        FINANCE_API_KEY: Finance API key (e.g., Plaid)
        FINANCE_API_SECRET: Finance API secret
        FINANCE_ACCOUNT_IDS: Comma-separated account IDs to monitor
        FINANCE_CHECK_INTERVAL: Seconds between checks (default: 300)
        FINANCE_ALERT_THRESHOLD: Transaction amount for alerts (default: 1000)
    
    Usage:
        watcher = FinanceWatcher()
        watcher.start()
    
    NOTES:
    - This is a template using Plaid API
    - Adapt to your finance provider (Yodlee, Stripe, etc.)
    - For Bronze tier, use stub implementation
    """
    
    def __init__(self):
        super().__init__("finance_watcher")
        
        # Get configuration
        self.api_key = os.getenv("FINANCE_API_KEY")
        self.api_secret = os.getenv("FINANCE_API_SECRET")
        self.account_ids = os.getenv("FINANCE_ACCOUNT_IDS", "").split(",")
        self.check_interval = int(os.getenv("FINANCE_CHECK_INTERVAL", "300"))
        self.alert_threshold = float(os.getenv("FINANCE_ALERT_THRESHOLD", "1000"))
        
        self.client = None
        self.last_check_time = None
        
        # Validate configuration
        if not self.api_key or not self.api_secret:
            raise WatcherConfigError(
                "Finance API credentials not configured. "
                "Set FINANCE_API_KEY and FINANCE_API_SECRET in .env"
            )
        
        if not PLAID_AVAILABLE:
            self.logger.warning(
                "Plaid library not installed. "
                "Using stub implementation. "
                "Install: pip install plaid-python"
            )
    
    def _connect(self) -> None:
        """Connect to finance API."""
        if not PLAID_AVAILABLE or not PlaidClient:
            self.logger.warning("Running in stub mode (Plaid not installed)")
            return
        
        try:
            # Initialize Plaid client (example)
            self.client = PlaidClient(  # type: ignore
                client_id=self.api_key,
                secret=self.api_secret,
                environment='sandbox'  # Change to 'production' for real use
            )
            self.logger.info("Connected to finance API")
            
        except Exception as e:
            raise WatcherConnectionError(f"Failed to connect to finance API: {e}")
    
    def _get_recent_transactions(self) -> List[Dict[str, Any]]:
        """Get recent transactions from all monitored accounts."""
        if not PLAID_AVAILABLE or not self.client:
            # Stub implementation for Bronze tier
            return self._get_stub_transactions()
        
        try:
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=1)  # Last 24 hours
            
            # If first run, go back 7 days
            if not self.last_check_time:
                start_date = end_date - timedelta(days=7)
            
            all_transactions = []
            
            # Fetch transactions for each account
            for account_id in self.account_ids:
                if not account_id.strip():
                    continue
                
                try:
                    response = self.client.Transactions.get(
                        access_token=account_id,  # In real usage, this would be account token
                        start_date=str(start_date),
                        end_date=str(end_date)
                    )
                    
                    transactions = response['transactions']
                    all_transactions.extend(transactions)
                    
                except Exception as e:  # type: ignore
                    # Catch PlaidError if available, otherwise general Exception
                    self.logger.error(f"Error fetching transactions for {account_id}: {e}")
                    continue
            
            self.last_check_time = datetime.now(timezone.utc)
            return all_transactions
            
        except Exception as e:
            self.logger.error(f"Error fetching transactions: {e}")
            return []
    
    def _get_stub_transactions(self) -> List[Dict[str, Any]]:
        """
        Stub implementation for Bronze tier testing.
        Returns fake transactions for testing.
        """
        # Only return transactions occasionally for testing
        import random
        if random.random() < 0.1:  # 10% chance
            return [{
                "transaction_id": f"stub_{int(time.time())}",
                "account_id": "stub_account",
                "amount": random.choice([50.00, 150.00, 1200.00, 3500.00]),
                "date": datetime.now().date().isoformat(),
                "name": random.choice([
                    "Amazon.com",
                    "Stripe Payment",
                    "Office Supplies Co",
                    "Client Payment - Invoice #123"
                ]),
                "category": random.choice(["Shopping", "Payment", "Office", "Income"]),
                "pending": False
            }]
        return []
    
    def _categorize_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Add metadata to transaction for task creation."""
        amount = abs(transaction.get('amount', 0))
        name = transaction.get('name', 'Unknown')
        
        # Determine priority
        priority = "low"
        if amount >= self.alert_threshold:
            priority = "high"
        elif amount >= self.alert_threshold / 2:
            priority = "normal"
        
        # Determine if HITL required
        hitl_required = False
        if amount >= self.alert_threshold:
            hitl_required = True
        
        # Check for keywords
        name_lower = name.lower()
        if any(word in name_lower for word in ['fraud', 'dispute', 'refund', 'chargeback']):
            priority = "critical"
            hitl_required = True
        
        return {
            "priority": priority,
            "hitl_required": hitl_required,
            "requires_action": priority in ["high", "critical"]
        }
    
    def on_event(self, transaction: Dict[str, Any]) -> None:
        """
        Handle a transaction by creating a task.
        
        Args:
            transaction: Transaction details from finance API
        """
        metadata = self._categorize_transaction(transaction)
        
        # Create task
        self.create_task(
            task_type="finance_transaction",
            context={
                "transaction_id": transaction.get('transaction_id'),
                "account_id": transaction.get('account_id'),
                "amount": transaction.get('amount'),
                "date": transaction.get('date'),
                "merchant": transaction.get('name'),
                "category": transaction.get('category'),
                "pending": transaction.get('pending', False),
                **metadata
            },
            priority=metadata['priority'],
            required_skills=["finance_skills"],
            hitl_required=metadata['hitl_required']
        )
        
        self.logger.info(
            f"Task created for transaction: {transaction.get('name')} - "
            f"${abs(transaction.get('amount', 0)):.2f}"
        )
    
    def start(self) -> None:
        """Start watching finance accounts."""
        if self.running:
            self.logger.warning("Watcher already running")
            return
        
        # Connect to API
        self._connect()
        
        self.running = True
        
        self.logger.info(
            f"Finance watcher started. "
            f"Checking every {self.check_interval}s. "
            f"Alert threshold: ${self.alert_threshold}"
        )
        
        try:
            while self.running:
                # Get recent transactions
                transactions = self._get_recent_transactions()
                
                if transactions:
                    self.logger.info(f"Found {len(transactions)} transactions")
                    
                    # Process each transaction
                    for transaction in transactions:
                        self.on_event(transaction)
                
                # Wait before next check
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            self.logger.error(f"Error in watch loop: {e}")
            self.stop()
    
    def stop(self) -> None:
        """Stop watching finance accounts."""
        if not self.running:
            return
        
        self.running = False
        self.logger.info("Finance watcher stopped")


def main():
    """Run finance watcher standalone."""
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   PERSONAL AI EMPLOYEE - FINANCE WATCHER (SILVER TIER)     ║
    ╚════════════════════════════════════════════════════════════╝
    
    This watcher monitors bank accounts for transactions.
    
    Setup Instructions:
    1. Sign up for Plaid API (or your finance provider)
    2. Get API credentials
    3. Set FINANCE_API_KEY and FINANCE_API_SECRET in .env
    4. Link your bank accounts and get account IDs
    5. Set FINANCE_ACCOUNT_IDS in .env
    
    For Bronze tier: Runs in stub mode (generates fake transactions)
    
    Press Ctrl+C to stop
    """)
    
    try:
        watcher = FinanceWatcher()
        watcher.start()
    except WatcherConfigError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nSee .env.example for configuration options.")
    except KeyboardInterrupt:
        print("\n\nShutting down...")


if __name__ == "__main__":
    main()
