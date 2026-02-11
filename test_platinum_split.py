"""
Quick test of Platinum Tier cloud/local split
"""
from draft_reviewer import DraftReviewer
import os

print("Testing Platinum Tier Draft System")
print("=" * 50)

# Create reviewer and process any tasks in inbox
reviewer = DraftReviewer()
print(f"\n1. Processing tasks from inbox...")
reviewer.process_new_tasks()

# Check what was created
drafts_folder = "obsidian_vault/Drafts"
if os.path.exists(drafts_folder):
    files = os.listdir(drafts_folder)
    print(f"\n2. Drafts created: {len(files)}")
    for f in files:
        print(f"   ✓ {f}")
else:
    print(f"\n2. Drafts folder not found")

# Check inbox
inbox_folder = "task_queue/inbox"
inbox_files = os.listdir(inbox_folder)  
print(f"\n3. Remaining in inbox: {len(inbox_files)}")

print("\n" + "=" * 50)
print("Test complete!")
print("\nNext steps:")
print("1. Open obsidian_vault/Drafts/ in Obsidian")
print("2. Review the draft")
print("3. Rename to .approved.md to approve")
print("4. Run reviewer again to move to Needs_Action/")
