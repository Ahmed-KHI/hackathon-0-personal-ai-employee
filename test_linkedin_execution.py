"""Test LinkedIn post execution"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration.action_executor import ActionExecutor

# Test execution
vault_path = Path(r"i:\hackathon 0 personal ai employee\obsidian_vault")
executor = ActionExecutor(vault_path=vault_path)

approved_file = Path(r"i:\hackathon 0 personal ai employee\obsidian_vault\Approved\APPROVAL_social_post_TEST_linkedin_post_manual_20260210_160549.approved.md")

print(f"Testing LinkedIn post execution...")
print("="*80)

try:
    result = executor.process_approved_file(approved_file)
    print(f"\n✅ Execution Result:")
    print(f"   Status: {result.get('status', 'Unknown')}")
    print(f"   Message: {result.get('message', 'No message')}")
    if 'post_id' in result:
        print(f"   Post ID: {result['post_id']}")
    if 'url' in result:
        print(f"   URL: {result['url']}")
except Exception as e:
    print(f"\n❌ Execution failed: {str(e)}")
    import traceback
    traceback.print_exc()
