"""Test HITL approval creation"""
import sys
import os
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration.action_executor import ActionExecutor

# Test the approval creation
vault_path = Path(r"i:\hackathon 0 personal ai employee\obsidian_vault")
executor = ActionExecutor(vault_path=vault_path)

# Create a test action
action = {
    "action_type": "social_post",
    "platform": "linkedin",
    "task_id": "TEST_linkedin_post_manual",
    "data": {
        "text": "🎉 Exciting milestone reached! Our Personal AI Employee automation system is now fully operational with end-to-end execution. From file detection to social media posting, everything runs autonomously. #AI #Automation #Hackathon #Innovation",
        "visibility": "PUBLIC"
    },
    "requires_approval": True,
    "risk_level": "medium"
}

print("Creating HITL approval request...")
print("="*80)

result = executor.create_approval_request(action)

print(f"\n✅ Approval request created!")
print(f"   Status: {result['status']}")
print(f"   Message: {result['message']}")
if 'approval_file' in result:
    approval_path = Path(result['approval_file'])
    print(f"   File: {approval_path.name}")
    print(f"   Location: {approval_path.parent.name}/")
    
    print(f"\n📄 Approval file content:")
    print("="*80)
    
    with open(approval_path, 'r', encoding='utf-8') as f:
        content = f.read()
        print(content)

print("\n" + "="*80)
print("✅ HITL approval creation successful!")
print(f"\n📌 To approve: Move to /Approved/")
print(f"📌 To reject: Move to /Rejected/")
