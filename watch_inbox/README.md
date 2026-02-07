# Watch Inbox Directory

This directory is monitored by the filesystem watcher.

## Usage (Bronze Tier)

Drop files here to create tasks for the AI Employee.

### Examples

**Simple Text File**:
```bash
echo "Process this document" > watch_inbox/task.txt
```

**Urgent Task**:
```bash
echo "Handle this immediately" > watch_inbox/urgent_task.txt
```

**JSON Data**:
```bash
cat > watch_inbox/data.json << EOF
{
  "type": "data_processing",
  "data": [1, 2, 3, 4, 5]
}
EOF
```

### Supported File Types

- `.txt` - Text files
- `.md` - Markdown files
- `.json` - JSON data
- `.csv` - CSV data

### File Naming Conventions

- `urgent_*` → High priority task
- `important_*` → High priority task
- `*` (any other) → Normal priority task

### What Happens

1. File appears in `watch_inbox/`
2. Filesystem watcher detects it
3. Task created in `task_queue/inbox/`
4. Orchestrator claims and processes
5. Result in `task_queue/completed/`

### Notes

- Files are not deleted (only read)
- Original file remains here
- Task JSON stored in task_queue
- Check Dashboard.md for status

---

**Bronze Tier**: This is the primary input method for testing.
**Silver Tier+**: Real watchers (Gmail, WhatsApp, etc.) take over.
