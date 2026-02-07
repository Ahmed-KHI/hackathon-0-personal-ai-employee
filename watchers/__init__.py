"""
Watchers Package - Event Perception Layer

All watchers inherit from BaseWatcher and follow the same pattern:
1. Detect events (emails, messages, transactions, files)
2. Create task JSON files in task_queue/inbox/
3. NEVER take actions or make decisions

Available Watchers:
- FilesystemWatcher (Bronze) - Watches directory for files
- GmailWatcher (Silver) - Watches Gmail inbox
- WhatsAppWatcher (Silver) - Watches WhatsApp Web
- FinanceWatcher (Silver) - Watches bank transactions
"""

from watchers.base_watcher import BaseWatcher, WatcherError, WatcherConfigError, WatcherConnectionError
from watchers.filesystem_watcher import FilesystemWatcher
from watchers.gmail_watcher import GmailWatcher
from watchers.whatsapp_watcher import WhatsAppWatcher
from watchers.finance_watcher import FinanceWatcher

__all__ = [
    'BaseWatcher',
    'WatcherError',
    'WatcherConfigError',
    'WatcherConnectionError',
    'FilesystemWatcher',
    'GmailWatcher',
    'WhatsAppWatcher',
    'FinanceWatcher'
]
