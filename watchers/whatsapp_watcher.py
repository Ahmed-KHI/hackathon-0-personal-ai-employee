"""
WhatsApp Watcher - Silver Tier

Watches WhatsApp Web for new messages using Playwright automation.
Creates tasks for incoming messages.

DEPLOYMENT TIER: Silver
DEPENDENCIES: playwright
WARNING: Requires browser automation, can be fragile
"""

import os
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime, timezone

try:
    from playwright.sync_api import sync_playwright, Page, Browser, Playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    sync_playwright = None  # type: ignore
    Page = None  # type: ignore
    Browser = None  # type: ignore
    Playwright = None  # type: ignore
    PLAYWRIGHT_AVAILABLE = False

from base_watcher import BaseWatcher, WatcherConfigError, WatcherConnectionError
from dotenv import load_dotenv

load_dotenv()


class WhatsAppWatcher(BaseWatcher):
    """
    Watches WhatsApp Web for new messages.
    
    Configuration (.env):
        WHATSAPP_SESSION_PATH: Path to store session data
        WHATSAPP_CHECK_INTERVAL: Seconds between checks (default: 10)
    
    Usage:
        watcher = WhatsAppWatcher()
        watcher.start()
    
    NOTES:
    - First run requires QR code scan
    - Session is saved for future runs
    - Requires Chromium installed: playwright install chromium
    """
    
    def __init__(self):
        if not PLAYWRIGHT_AVAILABLE or sync_playwright is None:
            raise WatcherConfigError(
                "Playwright not installed. Run: pip install playwright && playwright install chromium"
            )
        
        super().__init__("whatsapp_watcher")
        
        self.session_path = Path(os.getenv("WHATSAPP_SESSION_PATH", "./secrets/whatsapp_session"))
        self.check_interval = int(os.getenv("WHATSAPP_CHECK_INTERVAL", "10"))
        
        self.browser: Optional[Browser] = None  # type: ignore
        self.page: Optional[Page] = None  # type: ignore
        self.playwright: Optional[Playwright] = None  # type: ignore
        
        self.last_message_ids = set()
    
    def _launch_browser(self) -> None:
        """Launch browser with persistent context."""
        if not sync_playwright:
            raise WatcherConnectionError("Playwright not available")
        
        try:
            self.playwright = sync_playwright().start()  # type: ignore
            
            if not self.playwright:
                raise WatcherConnectionError("Failed to start Playwright")
            
            # Use persistent context to save session
            self.browser = self.playwright.chromium.launch_persistent_context(  # type: ignore
                user_data_dir=str(self.session_path),
                headless=False,  # WhatsApp Web requires visible browser
                args=['--no-sandbox']
            )
            
            if not self.browser:
                raise WatcherConnectionError("Failed to launch browser")
            
            self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()  # type: ignore
            
            self.logger.info("Browser launched")
            
        except Exception as e:
            raise WatcherConnectionError(f"Failed to launch browser: {e}")
    
    def _connect_whatsapp(self) -> None:
        """Connect to WhatsApp Web."""
        if not self.page:
            raise WatcherConnectionError("Browser page not available")
        
        try:
            self.page.goto("https://web.whatsapp.com")  # type: ignore
            
            # Wait for either QR code or chat list
            self.logger.info("Waiting for WhatsApp Web to load...")
            
            # Check if already logged in
            try:
                self.page.wait_for_selector('[data-testid="chat-list"]', timeout=10000)  # type: ignore
                self.logger.info("Already logged in to WhatsApp Web")
            except:
                # Need to scan QR code
                self.logger.info("Please scan QR code in browser window...")
                self.page.wait_for_selector('[data-testid="chat-list"]', timeout=120000)  # type: ignore
                self.logger.info("QR code scanned successfully!")
            
        except Exception as e:
            raise WatcherConnectionError(f"Failed to connect to WhatsApp Web: {e}")
    
    def _get_unread_chats(self) -> list:
        """Get list of chats with unread messages."""
        if not self.page:
            return []
        
        try:
            # Find chats with unread badge
            unread_chats = self.page.query_selector_all('[data-testid="cell-frame-container"]:has([data-testid="icon-unread"])')  # type: ignore
            
            return unread_chats
            
        except Exception as e:
            self.logger.error(f"Error getting unread chats: {e}")
            return []
    
    def _get_chat_details(self, chat_element) -> Optional[Dict[str, Any]]:
        """Extract details from a chat element."""
        if not self.page:
            return None
        
        try:
            # Click chat to open
            chat_element.click()
            time.sleep(1)
            
            # Get contact name
            contact_header = self.page.query_selector('[data-testid="conversation-header"]')  # type: ignore
            if not contact_header:
                return None
            contact_name = contact_header.inner_text()  # type: ignore
            
            # Get messages in chat
            messages = self.page.query_selector_all('[data-testid="msg-container"]')  # type: ignore
            
            # Get last few messages
            recent_messages = []
            for msg in messages[-5:]:  # Last 5 messages
                try:
                    text = msg.query_selector('[data-testid="msg-text"]')
                    if text:
                        message_text = text.inner_text()
                        recent_messages.append(message_text)
                except:
                    continue
            
            if not recent_messages:
                return None
            
            return {
                "contact": contact_name.split('\n')[0],  # First line is name
                "messages": recent_messages,
                "last_message": recent_messages[-1] if recent_messages else "",
                "message_count": len(recent_messages)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting chat details: {e}")
            return None
    
    def on_event(self, chat_details: Dict[str, Any]) -> None:
        """
        Handle a new WhatsApp message by creating a task.
        
        Args:
            chat_details: Details of the chat with new messages
        """
        # Determine priority
        priority = "normal"
        last_msg = chat_details['last_message'].lower()
        
        if any(word in last_msg for word in ['urgent', 'asap', 'emergency']):
            priority = "high"
        
        # WhatsApp messages generally don't require HITL unless specific keywords
        hitl_required = any(word in last_msg for word in ['contract', 'payment', 'legal'])
        
        # Create task
        self.create_task(
            task_type="whatsapp_response",
            context=chat_details,
            priority=priority,
            required_skills=["social_skills", "email_skills"],
            hitl_required=hitl_required
        )
        
        self.logger.info(f"Task created for WhatsApp message from: {chat_details['contact']}")
    
    def start(self) -> None:
        """Start watching WhatsApp."""
        if self.running:
            self.logger.warning("Watcher already running")
            return
        
        # Launch browser and connect
        self._launch_browser()
        self._connect_whatsapp()
        
        self.running = True
        
        self.logger.info(f"WhatsApp watcher started. Checking every {self.check_interval}s")
        
        try:
            while self.running:
                # Get unread chats
                unread_chats = self._get_unread_chats()
                
                if unread_chats:
                    self.logger.info(f"Found {len(unread_chats)} unread chats")
                    
                    # Process each chat
                    for chat in unread_chats:
                        details = self._get_chat_details(chat)
                        if details:
                            # Generate unique ID for this message
                            msg_id = f"{details['contact']}_{details['last_message'][:20]}"
                            
                            # Only process if not seen before
                            if msg_id not in self.last_message_ids:
                                self.on_event(details)
                                self.last_message_ids.add(msg_id)
                
                # Wait before next check
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            self.logger.error(f"Error in watch loop: {e}")
            self.stop()
    
    def stop(self) -> None:
        """Stop watching WhatsApp."""
        if not self.running:
            return
        
        self.running = False
        
        # Close browser
        if self.browser:
            self.browser.close()
        
        if self.playwright:
            self.playwright.stop()
        
        self.logger.info("WhatsApp watcher stopped")


def main():
    """Run WhatsApp watcher standalone."""
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║  PERSONAL AI EMPLOYEE - WHATSAPP WATCHER (SILVER TIER)     ║
    ╚════════════════════════════════════════════════════════════╝
    
    This watcher monitors WhatsApp Web for new messages.
    
    Setup Instructions:
    1. Install Playwright: playwright install chromium
    2. Run this script
    3. Scan QR code when prompted (first time only)
    4. Session will be saved for future runs
    
    WARNING: Keep browser window open while running!
    
    Press Ctrl+C to stop
    """)
    
    try:
        watcher = WhatsAppWatcher()
        watcher.start()
    except WatcherConfigError as e:
        print(f"\n❌ Configuration Error: {e}")
    except KeyboardInterrupt:
        print("\n\nShutting down...")


if __name__ == "__main__":
    main()
