#!/usr/bin/env python3
"""
Auto-Approval Watcher (OPTIONAL - Removes HITL Safety Gate)
WARNING: This auto-approves ALL actions without human review!
Use only for trusted, non-financial actions.
"""

import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoApprovalHandler(FileSystemEventHandler):
    """Automatically approve pending actions (USE WITH CAUTION!)"""
    
    def __init__(self, pending_dir: Path, approved_dir: Path):
        self.pending_dir = pending_dir
        self.approved_dir = approved_dir
        
    def on_created(self, event):
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Only process approval requests
        if file_path.suffix == '.md' and 'APPROVAL_' in file_path.name:
            logger.info(f"🔍 New approval request detected: {file_path.name}")
            
            # Auto-approve by renaming to .approved.md
            approved_name = file_path.stem + '.approved.md'
            approved_path = self.approved_dir / approved_name
            
            # Wait for file write completion
            time.sleep(1)
            
            # Move to Approved folder
            try:
                file_path.rename(approved_path)
                logger.info(f"✅ AUTO-APPROVED: {approved_name}")
            except Exception as e:
                logger.error(f"❌ Failed to auto-approve: {e}")

def main():
    vault = Path("./obsidian_vault")
    pending_dir = vault / "Pending_Approval"
    approved_dir = vault / "Approved"
    
    # Ensure directories exist
    pending_dir.mkdir(parents=True, exist_ok=True)
    approved_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("⚠️  AUTO-APPROVAL WATCHER STARTING")
    logger.info("⚠️  WARNING: This bypasses human safety checks!")
    logger.info("=" * 60)
    
    event_handler = AutoApprovalHandler(pending_dir, approved_dir)
    observer = Observer()
    observer.schedule(event_handler, str(pending_dir), recursive=False)
    observer.start()
    
    logger.info(f"👀 Monitoring: {pending_dir}")
    logger.info(f"✅ Auto-approving to: {approved_dir}")
    
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("Auto-approval watcher stopped")
    
    observer.join()

if __name__ == "__main__":
    main()
