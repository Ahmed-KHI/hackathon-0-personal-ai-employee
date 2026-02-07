"""
Test Suite - Basic Smoke Tests

Run these tests to validate Bronze tier deployment.
"""

import json
import os
from pathlib import Path


def test_directory_structure():
    """Verify all required directories exist."""
    required_dirs = [
        ".github",
        "obsidian_vault",
        "obsidian_vault/agent_skills",
        "watchers",
        "orchestration",
        "mcp_servers/email_server",
        "mcp_servers/browser_server",
        "mcp_servers/calendar_server",
        "mcp_servers/slack_server",
        "mcp_servers/odoo_server",
        "task_queue/inbox",
        "task_queue/pending",
        "task_queue/approvals",
        "task_queue/completed",
        "audit_logs",
        "secrets",
        "logs"
    ]
    
    for dir_path in required_dirs:
        assert Path(dir_path).exists(), f"Missing directory: {dir_path}"
    
    print("✓ All required directories exist")


def test_critical_files():
    """Verify critical files exist."""
    required_files = [
        ".github/copilot-instructions.md",
        ".gitignore",
        ".env.example",
        "README.md",
        "requirements.txt",
        "obsidian_vault/Dashboard.md",
        "obsidian_vault/Company_Handbook.md",
        "obsidian_vault/Business_Goals.md",
        "obsidian_vault/agent_skills/email_skills.md",
        "obsidian_vault/agent_skills/finance_skills.md",
        "obsidian_vault/agent_skills/social_skills.md",
        "obsidian_vault/agent_skills/planning_skills.md",
        "obsidian_vault/agent_skills/approval_skills.md",
        "watchers/base_watcher.py",
        "watchers/filesystem_watcher.py",
        "orchestration/orchestrator.py",
        "orchestration/audit_logger.py",
        "orchestration/ralph_loop.py"
    ]
    
    for file_path in required_files:
        assert Path(file_path).exists(), f"Missing file: {file_path}"
    
    print("✓ All critical files exist")


def test_vault_integrity():
    """Verify vault files are valid Markdown."""
    vault_files = [
        "obsidian_vault/Dashboard.md",
        "obsidian_vault/Company_Handbook.md",
        "obsidian_vault/Business_Goals.md"
    ]
    
    for file_path in vault_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert len(content) > 100, f"{file_path} is too short"
            assert content.startswith('#'), f"{file_path} doesn't start with Markdown header"
    
    print("✓ Vault files are valid Markdown")


def test_agent_skills():
    """Verify all agent skills are present and formatted."""
    skills = [
        "email_skills.md",
        "finance_skills.md",
        "social_skills.md",
        "planning_skills.md",
        "approval_skills.md"
    ]
    
    for skill in skills:
        skill_path = Path("obsidian_vault/agent_skills") / skill
        assert skill_path.exists(), f"Missing skill: {skill}"
        
        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert len(content) > 500, f"{skill} is too short"
            assert "Purpose" in content or "CRITICAL" in content
    
    print("✓ All agent skills present and formatted")


def test_gitignore():
    """Verify .gitignore includes critical exclusions."""
    with open(".gitignore", 'r') as f:
        gitignore = f.read()
    
    critical_exclusions = [".env", "secrets/", "*.token", "__pycache__"]
    
    for exclusion in critical_exclusions:
        assert exclusion in gitignore, f".gitignore missing: {exclusion}"
    
    print("✓ .gitignore properly configured")


def test_env_example():
    """Verify .env.example has required variables."""
    with open(".env.example", 'r') as f:
        env_example = f.read()
    
    required_vars = [
        "VAULT_PATH",
        "ANTHROPIC_API_KEY",
        "RALPH_LOOP_MAX_ITERATIONS",
        "DEPLOYMENT_TIER"
    ]
    
    for var in required_vars:
        assert var in env_example, f".env.example missing: {var}"
    
    print("✓ .env.example properly configured")


def test_copilot_instructions():
    """Verify GitHub Copilot instructions are authoritative."""
    with open(".github/copilot-instructions.md", 'r', encoding='utf-8') as f:
        instructions = f.read()
    
    critical_rules = [
        "replace Obsidian vault with a database",
        "replace file-based task queue",
        "claim-by-move",
        "Dashboard.md` from anywhere except",
        "Ralph Wiggum Stop-Hook"
    ]
    
    for rule in critical_rules:
        assert rule in instructions, f"Copilot instructions missing critical rule: {rule}"
    
    print("✓ GitHub Copilot instructions are complete")


def test_task_queue_readme():
    """Verify task queue README explains claim-by-move."""
    with open("task_queue/README.md", 'r') as f:
        readme = f.read()
    
    assert "claim-by-move" in readme.lower()
    assert "ONE task" in readme or "one task" in readme
    
    print("✓ Task queue README explains architecture")


def run_all_tests():
    """Run all validation tests."""
    print("\n" + "="*60)
    print("PERSONAL AI EMPLOYEE - VALIDATION TESTS (BRONZE TIER)")
    print("="*60 + "\n")
    
    tests = [
        test_directory_structure,
        test_critical_files,
        test_vault_integrity,
        test_agent_skills,
        test_gitignore,
        test_env_example,
        test_copilot_instructions,
        test_task_queue_readme
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: Unexpected error: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    if failed == 0:
        print("🎉 All tests passed! System is ready for Bronze tier deployment.\n")
        print("Next steps:")
        print("1. Copy .env.example to .env and configure")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Run filesystem watcher: python watchers/filesystem_watcher.py")
        print("4. Run orchestrator: python orchestration/orchestrator.py")
        print("5. Create a test task in task_queue/inbox/")
        return 0
    else:
        print(f"⚠️  {failed} test(s) failed. Fix issues before deployment.\n")
        return 1


if __name__ == "__main__":
    exit(run_all_tests())
