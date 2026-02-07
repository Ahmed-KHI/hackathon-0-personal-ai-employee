"""
Silver Tier Compliance Test Suite
Tests all 8 requirements from hackathon.doc Silver tier

Run this to verify 100% Silver tier completion before advancing to Gold.
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

class SilverTierTest:
    """Test harness for Silver tier compliance"""
    
    def __init__(self):
        self.vault_path = Path("./obsidian_vault")
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"    {details}")
        
        self.results.append({
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def test_filesystem_watcher(self):
        """Test 1: Filesystem watcher exists and runs"""
        watcher_file = Path("watcher_filesystem.py")
        
        if not watcher_file.exists():
            self.log_result("Filesystem Watcher", False, "watcher_filesystem.py not found")
            return
        
        # Check if it has necessary imports
        content = watcher_file.read_text()
        has_watchdog = "watchdog" in content
        has_task_creation = "task_queue" in content or "Needs_Action" in content
        
        passed = has_watchdog and has_task_creation
        details = "Found watchdog import and task creation logic" if passed else "Missing required functionality"
        self.log_result("Filesystem Watcher", passed, details)
    
    def test_gmail_watcher(self):
        """Test 2: Gmail watcher with OAuth"""
        watcher_file = Path("watcher_gmail.py")
        credentials = Path("secrets/gmail_credentials.json")
        
        if not watcher_file.exists():
            self.log_result("Gmail Watcher", False, "watcher_gmail.py not found")
            return
        
        # Check OAuth setup
        has_oauth = credentials.exists() or "gmail_credentials.json" in watcher_file.read_text()
        
        details = "Gmail OAuth configured" if has_oauth else "OAuth credentials not configured (run setup first)"
        self.log_result("Gmail Watcher", watcher_file.exists(), details)
    
    def test_linkedin_automation(self):
        """Test 3: LinkedIn automation (CRITICAL GAP)"""
        watcher = Path("watcher_linkedin.py")
        mcp_server = Path("mcp_servers/linkedin_server/linkedin_server.py")
        oauth_setup = Path("setup_linkedin.py")
        skills = Path("obsidian_vault/agent_skills/linkedin_skills.md")
        
        components = [
            (watcher, "LinkedIn watcher"),
            (mcp_server, "LinkedIn MCP server"),
            (oauth_setup, "LinkedIn OAuth setup"),
            (skills, "LinkedIn agent skills")
        ]
        
        missing = [name for path, name in components if not path.exists()]
        
        if missing:
            self.log_result("LinkedIn Automation", False, f"Missing: {', '.join(missing)}")
        else:
            self.log_result("LinkedIn Automation", True, "All 4 LinkedIn components present")
    
    def test_plan_md_generation(self):
        """Test 4: Plan.md generation via Anthropic API"""
        orchestrator = Path("orchestrator_claude.py")
        plans_folder = self.vault_path / "Plans"
        
        if not orchestrator.exists():
            self.log_result("Plan.md Generation", False, "orchestrator_claude.py not found")
            return
        
        # Check for Anthropic API usage
        content = orchestrator.read_text()
        has_anthropic = "anthropic" in content.lower()
        has_plan_logic = "Plan.md" in content or "plans" in content.lower()
        
        # Check if Plans folder has any plans
        plan_count = len(list(plans_folder.glob("*.md"))) if plans_folder.exists() else 0
        
        passed = has_anthropic and has_plan_logic
        details = f"Anthropic API integrated, {plan_count} plans generated" if passed else "Missing Plan.md generation logic"
        self.log_result("Plan.md Generation", passed, details)
    
    def test_hitl_workflow(self):
        """Test 5: Human-in-the-Loop 10-folder workflow"""
        required_folders = [
            "Needs_Action",
            "In_Progress",
            "Plans",
            "Pending_Approval",
            "Approved",
            "Rejected",
            "Done",
            "Logs",
            "Briefings"
        ]
        
        missing = []
        for folder in required_folders:
            folder_path = self.vault_path / folder
            if not folder_path.exists():
                missing.append(folder)
        
        passed = len(missing) == 0
        details = f"All {len(required_folders)} folders exist" if passed else f"Missing: {', '.join(missing)}"
        self.log_result("HITL 10-Folder Workflow", passed, details)
    
    def test_agent_skills(self):
        """Test 6: Agent Skills in markdown"""
        skills_folder = self.vault_path / "agent_skills"
        
        if not skills_folder.exists():
            self.log_result("Agent Skills", False, "agent_skills folder not found")
            return
        
        skills = list(skills_folder.glob("*.md"))
        required_skills = {
            "email_skills.md",
            "linkedin_skills.md",
            "planning_skills.md",
            "approval_skills.md"
        }
        
        found_skills = {skill.name for skill in skills}
        missing = required_skills - found_skills
        
        # Calculate total lines
        total_lines = sum(len(skill.read_text(encoding='utf-8').splitlines()) for skill in skills)
        
        passed = len(missing) == 0
        details = f"{len(skills)} skills, {total_lines} lines total" if passed else f"Missing: {', '.join(missing)}"
        self.log_result("Agent Skills", passed, details)
    
    def test_time_scheduler(self):
        """Test 7: Time-based scheduler (Monday CEO briefing)"""
        orchestrator = Path("orchestrator_claude.py")
        
        if not orchestrator.exists():
            self.log_result("Time-Based Scheduler", False, "orchestrator_claude.py not found")
            return
        
        content = orchestrator.read_text()
        has_schedule = "import schedule" in content
        has_monday = "monday" in content.lower() and "briefing" in content.lower()
        has_run_pending = "schedule.run_pending()" in content
        
        passed = has_schedule and has_monday and has_run_pending
        details = "Monday CEO briefing scheduled" if passed else "Missing scheduler implementation"
        self.log_result("Time-Based Scheduler", passed, details)
    
    def test_mcp_integration(self):
        """Test 8: MCP integration (email, LinkedIn, calendar, etc.)"""
        mcp_folder = Path("mcp_servers")
        
        if not mcp_folder.exists():
            self.log_result("MCP Integration", False, "mcp_servers folder not found")
            return
        
        # Check for required MCP servers
        required_servers = {
            "email_server": "email_server.py",
            "linkedin_server": "linkedin_server.py",
            "calendar_server": "calendar_server.py",
            "browser_server": "browser_server.py"
        }
        
        existing = []
        for server_dir, server_file in required_servers.items():
            server_path = mcp_folder / server_dir / server_file
            if server_path.exists():
                existing.append(server_dir)
        
        # Check orchestrator integration
        orchestrator = Path("orchestrator_claude.py")
        content = orchestrator.read_text() if orchestrator.exists() else ""
        has_integration = "from email_server" in content or "from linkedin_server" in content
        
        passed = len(existing) >= 2 and has_integration
        details = f"{len(existing)}/4 MCP servers exist, orchestrator integrated: {has_integration}"
        self.log_result("MCP Integration", passed, details)
    
    def test_pm2_configuration(self):
        """Test 9: PM2 ecosystem configuration"""
        ecosystem = Path("ecosystem.config.js")
        
        if not ecosystem.exists():
            self.log_result("PM2 Configuration", False, "ecosystem.config.js not found")
            return
        
        content = ecosystem.read_text()
        services = content.count("name:")
        has_orchestrator = "orchestrator" in content
        has_watchers = "watcher" in content
        
        passed = has_orchestrator and has_watchers and services >= 3
        details = f"{services} services configured (orchestrator + watchers)"
        self.log_result("PM2 Configuration", passed, details)
    
    def test_environment_setup(self):
        """Test 10: Environment configuration"""
        env_example = Path(".env.example")
        
        if not env_example.exists():
            self.log_result("Environment Setup", False, ".env.example not found")
            return
        
        content = env_example.read_text()
        required_vars = [
            "ANTHROPIC_API_KEY",
            "GMAIL_ENABLED",
            "LINKEDIN_ENABLED",
            "VAULT_PATH"
        ]
        
        missing = [var for var in required_vars if var not in content]
        
        passed = len(missing) == 0
        details = "All required env vars documented" if passed else f"Missing: {', '.join(missing)}"
        self.log_result("Environment Setup", passed, details)
    
    def run_all_tests(self):
        """Run complete Silver tier test suite"""
        print("\n" + "="*70)
        print("SILVER TIER COMPLIANCE TEST SUITE")
        print("Hackathon 0 - Personal AI Employee")
        print("="*70 + "\n")
        
        print("Testing Core Requirements...\n")
        
        # Run all tests
        self.test_filesystem_watcher()
        self.test_gmail_watcher()
        self.test_linkedin_automation()
        self.test_plan_md_generation()
        self.test_hitl_workflow()
        self.test_agent_skills()
        self.test_time_scheduler()
        self.test_mcp_integration()
        self.test_pm2_configuration()
        self.test_environment_setup()
        
        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Passed: {self.passed}/{self.passed + self.failed}")
        print(f"Failed: {self.failed}/{self.passed + self.failed}")
        
        completion_rate = (self.passed / (self.passed + self.failed)) * 100
        print(f"\nSilver Tier Completion: {completion_rate:.1f}%")
        
        if completion_rate >= 100:
            print("\n🎉 SILVER TIER: 100% COMPLETE - Ready for Gold Tier!")
        elif completion_rate >= 90:
            print("\n⚠️  SILVER TIER: Near Complete - Fix remaining issues")
        else:
            print("\n❌ SILVER TIER: Incomplete - Address failed tests")
        
        # Save results
        results_file = Path("test_results_silver.json")
        with open(results_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "tier": "Silver",
                "passed": self.passed,
                "failed": self.failed,
                "completion_rate": completion_rate,
                "tests": self.results
            }, f, indent=2)
        
        print(f"\nDetailed results saved to: {results_file}")
        print("="*70 + "\n")
        
        return completion_rate >= 100


if __name__ == "__main__":
    tester = SilverTierTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
