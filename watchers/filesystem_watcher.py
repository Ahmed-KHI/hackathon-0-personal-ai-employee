"""
Filesystem Watcher - Bronze Tier MVP

Watches a directory for new files and creates tasks.
This is the simplest watcher, used for testing the system.

BRONZE TIER DEPLOYMENT:
- No external dependencies
- Human creates files manually in watched directory
- AI Employee processes them
"""

import os
import time
from pathlib import Path
from typing import Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
from base_watcher import BaseWatcher, WatcherConfigError
from dotenv import load_dotenv

load_dotenv()


class FilesystemEventHandler(FileSystemEventHandler):
    """Handles filesystem events and delegates to watcher."""
    
    def __init__(self, watcher: 'FilesystemWatcher'):
        self.watcher = watcher
    
    def on_created(self, event: FileCreatedEvent):
        """Called when a file is created."""
        if event.is_directory:
            return
        
        # Ignore hidden files and non-text files
        file_path = Path(str(event.src_path))
        if file_path.name.startswith('.'):
            return
        
        # Only process specific file types (txt, md, json)
        if file_path.suffix not in ['.txt', '.md', '.json', '.csv']:
            return
        
        self.watcher.on_event(file_path)


class FilesystemWatcher(BaseWatcher):
    """
    Watches a directory for new files.
    
    Configuration (.env):
        FILESYSTEM_WATCH_PATH: Directory to watch (default: ./watch_inbox)
    
    Usage:
        watcher = FilesystemWatcher()
        watcher.start()
        # Creates tasks when files appear in watched directory
    """
    
    def __init__(self):
        super().__init__("filesystem_watcher")
        
        # Get watch path from environment or use default
        self.watch_path = Path(os.getenv("FILESYSTEM_WATCH_PATH", "./watch_inbox"))
        self.watch_path.mkdir(parents=True, exist_ok=True)
        
        self.observer = None
        
        self.logger.info(f"Watching directory: {self.watch_path}")
    
    def on_event(self, file_path: Path) -> None:
        """
        Handle a new file appearing in watched directory.
        
        Creates a task with:
        - File name
        - File path
        - File size
        - File contents (if text-readable)
        """
        try:
            # Read file metadata
            file_size = file_path.stat().st_size
            file_modified = file_path.stat().st_mtime
            
            # Try to read file contents
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    contents = f.read()
            except UnicodeDecodeError:
                contents = "[Binary file - not readable]"
            except Exception as e:
                contents = f"[Error reading file: {e}]"
            
            # Determine priority based on filename
            priority = "normal"
            if "urgent" in file_path.name.lower():
                priority = "high"
            elif "important" in file_path.name.lower():
                priority = "high"
            
            # Create task
            self.create_task(
                task_type="file_process",
                context={
                    "file_name": file_path.name,
                    "file_path": str(file_path.absolute()),
                    "file_size_bytes": file_size,
                    "file_modified": file_modified,
                    "file_extension": file_path.suffix,
                    "contents": contents[:5000]  # Limit to first 5KB
                },
                priority=priority,
                required_skills=["planning_skills"],
                hitl_required=False  # Bronze tier: all auto-process
            )
            
            self.logger.info(f"Task created for file: {file_path.name}")
            
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
    
    def start(self) -> None:
        """Start watching the directory."""
        if self.running:
            self.logger.warning("Watcher already running")
            return
        
        try:
            # Create observer
            self.observer = Observer()
            event_handler = FilesystemEventHandler(self)
            self.observer.schedule(event_handler, str(self.watch_path), recursive=False)
            
            # Start observer
            self.observer.start()
            self.running = True
            
            self.logger.info(f"Filesystem watcher started. Monitoring: {self.watch_path}")
            
            # Keep running
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop()
                
        except Exception as e:
            self.logger.error(f"Failed to start watcher: {e}")
            raise WatcherConfigError(f"Cannot start filesystem watcher: {e}")
    
    def stop(self) -> None:
        """Stop watching."""
        if not self.running:
            return
        
        self.running = False
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        self.logger.info("Filesystem watcher stopped")


def main():
    """Run the filesystem watcher standalone."""
    watcher = FilesystemWatcher()
    
    print(f"""
    ╔════════════════════════════════════════════════════════════╗
    ║  PERSONAL AI EMPLOYEE - FILESYSTEM WATCHER (BRONZE TIER)   ║
    ╚════════════════════════════════════════════════════════════╝
    
    Watching: {watcher.watch_path}
    Inbox:    {watcher.inbox_path}
    
    Instructions:
    1. Drop files into: {watcher.watch_path}
    2. Tasks will be created in: {watcher.inbox_path}
    3. Press Ctrl+C to stop
    
    Ready! Waiting for files...
    """)
    
    try:
        watcher.start()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        watcher.stop()


if __name__ == "__main__":
    main()
