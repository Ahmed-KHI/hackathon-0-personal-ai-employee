"""
Filesystem Watcher - Hackathon 0 Compliant
Monitors watch_inbox folder and creates tasks in /Needs_Action
"""

import os
import time
import logging
from pathlib import Path
from datetime import datetime, timezone
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FilesystemWatcher(FileSystemEventHandler):
    """Watches filesystem for new files and creates tasks in /Needs_Action"""
    
    def __init__(self, watch_path: str = "./watch_inbox", vault_path: str = "./obsidian_vault"):
        self.watch_path = Path(watch_path)
        self.vault = Path(vault_path)
        self.needs_action = self.vault / "Needs_Action"
        self.needs_action.mkdir(parents=True, exist_ok=True)
        logger.info(f"Filesystem watcher initialized: {self.watch_path} → {self.needs_action}")
    
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
            # Wait a moment for file to be fully written
            time.sleep(0.5)
            
            # Read file content
            try:
                content = file_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                content = f"[Binary file - {file_path.stat().st_size} bytes]"
            
            # Create task file in /Needs_Action as markdown (per Hackathon 0 spec)
            task_file = self.needs_action / f"FILE_{file_path.name}.md"
            
            markdown_content = f"""---
type: file_drop
original_name: {file_path.name}
size: {file_path.stat().st_size}
created: {datetime.now(timezone.utc).isoformat()}
priority: medium
status: pending
---

## File Dropped for Processing

**File**: {file_path.name}  
**Size**: {file_path.stat().st_size} bytes  
**Location**: {str(file_path.absolute())}  
**Created**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

## Content Preview

```
{content[:1000] if len(content) > 1000 else content}
{'...[truncated]' if len(content) > 1000 else ''}
```

## Suggested Actions
- [ ] Analyze file content and determine intent
- [ ] Create appropriate plan in /Plans
- [ ] Execute or request human approval if needed
- [ ] Move to /Done when complete
"""
            
            task_file.write_text(markdown_content)
            logger.info(f"Created task: {task_file.name}")
            
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
