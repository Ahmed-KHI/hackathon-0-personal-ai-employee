"""
Filesystem Watcher - Hackathon 0 Compliant
Monitors watch_inbox folder and creates tasks in task_queue/inbox
"""

import os
import time
import logging
import json
from pathlib import Path
from datetime import datetime, timezone
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FilesystemWatcher(FileSystemEventHandler):
    """Watches filesystem for new files and creates tasks in task_queue/inbox"""
    
    def __init__(self, watch_path: str = "./watch_inbox", task_queue_path: str = "./task_queue"):
        self.watch_path = Path(watch_path)
        self.task_queue = Path(task_queue_path) / "inbox"
        self.task_queue.mkdir(parents=True, exist_ok=True)
        logger.info(f"Filesystem watcher initialized: {self.watch_path} → {self.task_queue}")
    
    def on_created(self, event):
        """Handle new file creation"""
        if event.is_directory:
            return
        
        file_path = Path(str(event.src_path))
        
        # Ignore hidden files and system files
        if file_path.name.startswith('.') or file_path.name.startswith('~'):
            return
        
        logger.info(f"New file detected: {file_path.name}")
        
        try:
            # RACE CONDITION FIX: Wait for file to be fully written
            # Professional approach: Check file stability
            time.sleep(1.0)  # Initial delay
            
            # Verify file still exists and is stable
            if not file_path.exists():
                logger.warning(f"File {file_path.name} disappeared before processing")
                return
            
            prev_size = -1
            current_size = file_path.stat().st_size
            
            # Wait until file size stabilizes (up to 3 seconds)
            for _ in range(3):
                if current_size == prev_size:
                    break
                prev_size = current_size
                time.sleep(0.5)
                current_size = file_path.stat().st_size if file_path.exists() else prev_size
            
            # Read FULL file content (not just preview)
            try:
                content = file_path.read_text(encoding='utf-8')
                # Reasonable limit: 50KB for text files
                if len(content) > 50000:
                    logger.warning(f"File {file_path.name} is large ({len(content)} chars), truncating to 50KB")
                    content_full = content[:50000] + "\n\n[... Content truncated at 50KB ...]"
                else:
                    content_full = content
            except UnicodeDecodeError:
                content_full = f"[Binary file - {file_path.stat().st_size} bytes - cannot display content]"
            
            # Create task file in task_queue/inbox as JSON (per Hackathon 0 spec)
            task_id = f"file_{file_path.stem}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
            task_file = self.task_queue / f"{task_id}.json"
            
            # CRITICAL FIX: Store FULL content with required_skills
            # This ensures Claude has all information and knows which skills to use
            task = {
                'task_id': task_id,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'source': 'filesystem_watcher',
                'type': 'file_process',
                'priority': 'normal',
                'context': {
                    'file_name': file_path.name,
                    'file_path': str(file_path.absolute()),
                    'file_size_bytes': file_path.stat().st_size,
                    'file_modified': file_path.stat().st_mtime,
                    'file_extension': file_path.suffix,
                    'contents': content_full
                },
                'required_skills': ['planning_skills', 'approval_skills']
            }
            
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(task, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Created task: {task_file.name} (content: {len(content_full)} chars)")
            
        except Exception as e:
            logger.error(f"Error processing file {file_path.name}: {e}")
    
    def start(self):
        """Start watching the filesystem"""
        observer = Observer()
        observer.schedule(self, str(self.watch_path), recursive=False)
        observer.start()
        
        logger.info(f"Watching {self.watch_path} for new files...")
        
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            observer.stop()
            logger.info("Filesystem watcher stopped")
        
        observer.join()


if __name__ == "__main__":
    watcher = FilesystemWatcher()
    watcher.start()
