"""Test ActionExecutor plan parsing"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration.action_executor import ActionExecutor

# Test the parsing
vault_path = Path(r"i:\hackathon 0 personal ai employee\obsidian_vault")
executor = ActionExecutor(vault_path=vault_path)
test_plan = r"i:\hackathon 0 personal ai employee\obsidian_vault\Plans\TEST_linkedin_post_manual_plan.md"

print(f"Testing plan: {test_plan}")
print("="*80)

actions = executor.parse_plan_for_actions(Path(test_plan))

print(f"\n✅ Extracted {len(actions)} action(s):")
print("="*80)

for i, action in enumerate(actions, 1):
    print(f"\nAction {i}:")
    print(f"  Action Type: {action.get('action_type', 'N/A')}")
    print(f"  Platform: {action.get('platform', 'N/A')}")
    print(f"  Requires Approval: {action.get('requires_approval', 'N/A')}")
    print(f"  Risk Level: {action.get('risk_level', 'N/A')}")
    print(f"\n  Full Action Data:")
    import json
    print(json.dumps(action, indent=4))

if len(actions) == 0:
    print("\n⚠️ NO ACTIONS EXTRACTED - Pattern matching failed!")
    print("\nLet me read the plan content to debug:")
    with open(test_plan, 'r', encoding='utf-8') as f:
        content = f.read()
    print("\n" + "="*80)
    print("Plan Content:")
    print("="*80)
    print(content[:1000])  # First 1000 chars
