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
            
            # Create task file in /Needs_Action as markdown (per Hackathon 0 spec)
            task_file = self.needs_action / f"FILE_{file_path.name}.md"
            
            # CRITICAL FIX: Store FULL content, not just preview
            # This ensures Claude has all information needed for plan generation
            markdown_content = f"""---
type: file_drop
original_name: {file_path.name}
size: {file_path.stat().st_size}
created: {datetime.now(timezone.utc).isoformat()}
priority: medium
status: pending
content_length: {len(content_full)}
---

## File Dropped for Processing

**File**: {file_path.name}  
**Size**: {file_path.stat().st_size} bytes  
**Content Length**: {len(content_full)} characters  
**Location**: {str(file_path.absolute())}  
**Created**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

## Full File Content

```
{content_full}
```

## Suggested Actions
- [ ] Analyze file content and determine intent
- [ ] Create appropriate plan in /Plans
- [ ] Execute or request human approval if needed
- [ ] Move to /Done when complete
"""
            
            task_file.write_text(markdown_content, encoding='utf-8')
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
