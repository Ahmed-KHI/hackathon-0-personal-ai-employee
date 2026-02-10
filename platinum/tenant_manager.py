"""
Tenant Manager - Multi-Tenant Architecture for Personal AI Employee
Handles tenant lifecycle, isolation, and configuration
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TenantManager:
    """Manages multi-tenant isolation and configuration"""
    
    def __init__(self, base_path: str = "./vaults"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        self.config_path = Path("platinum/tenants.json")
        self.tenants = self._load_tenants()
    
    def _load_tenants(self) -> Dict:
        """Load tenant configuration"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_tenants(self):
        """Save tenant configuration"""
        self.config_path.parent.mkdir(exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.tenants, f, indent=2)
    
    def create_tenant(self, tenant_id: str, config: Optional[Dict] = None) -> Dict:
        """
        Create a new tenant with isolated environment
        
        Args:
            tenant_id: Unique tenant identifier
            config: Optional tenant configuration (name, API keys, etc.)
        
        Returns:
            Dict with tenant info and vault paths
        """
        if tenant_id in self.tenants:
            raise ValueError(f"Tenant {tenant_id} already exists")
        
        logger.info(f"Creating tenant: {tenant_id}")
        
        # Create tenant vault directory
        tenant_vault = self.base_path / tenant_id
        tenant_vault.mkdir(parents=True, exist_ok=True)
        
        # Create all required folders
        folders = [
            "Needs_Action",
            "In_Progress",
            "Plans",
            "Done",
            "Pending_Approval",
            "Approved",
            "Rejected",
            "Logs",
            "Briefings",
            "agent_skills"
        ]
        
        for folder in folders:
            (tenant_vault / folder).mkdir(exist_ok=True)
        
        # Create tenant-specific task queue
        task_queue = Path(f"task_queue/{tenant_id}")
        for subfolder in ["inbox", "pending", "completed", "approvals"]:
            (task_queue / subfolder).mkdir(parents=True, exist_ok=True)
        
        # Create tenant audit log directory
        audit_dir = Path(f"audit_logs/{tenant_id}")
        audit_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize tenant configuration
        tenant_config = {
            "tenant_id": tenant_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "status": "active",
            "vault_path": str(tenant_vault),
            "task_queue_path": str(task_queue),
            "audit_log_path": str(audit_dir),
            "config": config or {},
            "quotas": {
                "max_tasks_per_day": 1000,
                "max_api_calls_per_hour": 500,
                "max_storage_mb": 1000
            },
            "features": {
                "social_media": True,
                "email": True,
                "calendar": True,
                "finance": False,  # Premium feature
                "encryption": False  # Platinum feature
            }
        }
        
        # Save tenant configuration
        self.tenants[tenant_id] = tenant_config
        self._save_tenants()
        
        # Create tenant-specific secrets directory
        secrets_dir = Path(f"secrets/{tenant_id}")
        secrets_dir.mkdir(parents=True, exist_ok=True)
        
        # Create README for tenant
        readme_content = f"""# Tenant: {tenant_id}

**Created**: {tenant_config['created_at']}
**Status**: {tenant_config['status']}

## Vault Structure
```
{tenant_vault}/
  ├── Needs_Action/     (incoming tasks)
  ├── In_Progress/      (claimed tasks)
  ├── Plans/            (generated plans)
  ├── Done/             (completed tasks)
  ├── Pending_Approval/ (awaiting HITL)
  ├── Approved/         (approved actions)
  ├── Rejected/         (rejected actions)
  ├── Logs/             (execution logs)
  ├── Briefings/        (CEO briefings)
  └── agent_skills/     (AI agent skills)
```

## Configuration
See: `platinum/tenants.json`

## API Keys
Stored in: `secrets/{tenant_id}/`

## Audit Logs
Located at: `{audit_dir}/`
"""
        
        with open(tenant_vault / "README.md", 'w') as f:
            f.write(readme_content)
        
        logger.info(f"✅ Tenant {tenant_id} created successfully")
        logger.info(f"   Vault: {tenant_vault}")
        logger.info(f"   Task Queue: {task_queue}")
        logger.info(f"   Audit Logs: {audit_dir}")
        
        return tenant_config
    
    def get_tenant(self, tenant_id: str) -> Optional[Dict]:
        """Get tenant configuration"""
        return self.tenants.get(tenant_id)
    
    def list_tenants(self) -> List[Dict]:
        """List all tenants"""
        return list(self.tenants.values())
    
    def update_tenant(self, tenant_id: str, config: Dict) -> Dict:
        """Update tenant configuration"""
        if tenant_id not in self.tenants:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        self.tenants[tenant_id]["config"].update(config)
        self.tenants[tenant_id]["updated_at"] = datetime.utcnow().isoformat() + "Z"
        self._save_tenants()
        
        logger.info(f"✅ Tenant {tenant_id} updated")
        return self.tenants[tenant_id]
    
    def deactivate_tenant(self, tenant_id: str):
        """Deactivate a tenant (soft delete)"""
        if tenant_id not in self.tenants:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        self.tenants[tenant_id]["status"] = "inactive"
        self.tenants[tenant_id]["deactivated_at"] = datetime.utcnow().isoformat() + "Z"
        self._save_tenants()
        
        logger.info(f"✅ Tenant {tenant_id} deactivated")
    
    def delete_tenant(self, tenant_id: str, confirm: bool = False):
        """
        Permanently delete tenant (DANGEROUS!)
        Requires explicit confirmation
        """
        if not confirm:
            raise ValueError("Must explicitly confirm tenant deletion (confirm=True)")
        
        if tenant_id not in self.tenants:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        tenant_config = self.tenants[tenant_id]
        
        # Delete vault
        vault_path = Path(tenant_config["vault_path"])
        if vault_path.exists():
            shutil.rmtree(vault_path)
        
        # Delete task queue
        task_queue_path = Path(tenant_config["task_queue_path"])
        if task_queue_path.exists():
            shutil.rmtree(task_queue_path)
        
        # Archive audit logs (don't delete for compliance)
        audit_path = Path(tenant_config["audit_log_path"])
        if audit_path.exists():
            archive_path = Path(f"audit_logs/_archived/{tenant_id}")
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(audit_path), str(archive_path))
            logger.info(f"📦 Audit logs archived to {archive_path}")
        
        # Remove from config
        del self.tenants[tenant_id]
        self._save_tenants()
        
        logger.warning(f"🗑️  Tenant {tenant_id} permanently deleted")
    
    def get_tenant_stats(self, tenant_id: str) -> Dict:
        """Get usage statistics for tenant"""
        if tenant_id not in self.tenants:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        tenant_config = self.tenants[tenant_id]
        vault_path = Path(tenant_config["vault_path"])
        
        stats = {
            "tenant_id": tenant_id,
            "status": tenant_config["status"],
            "tasks_in_progress": len(list((vault_path / "In_Progress").glob("*.md"))),
            "tasks_completed": len(list((vault_path / "Done").glob("*.md"))),
            "pending_approvals": len(list((vault_path / "Pending_Approval").glob("*.md"))),
            "plans_generated": len(list((vault_path / "Plans").glob("*.md"))),
            "briefings_created": len(list((vault_path / "Briefings").glob("*.md")))
        }
        
        # Calculate storage usage
        total_size = sum(f.stat().st_size for f in vault_path.rglob("*") if f.is_file())
        stats["storage_mb"] = round(total_size / (1024 * 1024), 2)
        
        return stats


if __name__ == "__main__":
    # Example usage
    manager = TenantManager()
    
    # Create a test tenant
    tenant = manager.create_tenant(
        tenant_id="tenant_001",
        config={
            "name": "Acme Corporation",
            "admin_email": "admin@acme.com",
            "tier": "platinum"
        }
    )
    
    print("\n✅ Tenant created:")
    print(json.dumps(tenant, indent=2))
    
    # Get stats
    stats = manager.get_tenant_stats("tenant_001")
    print("\n📊 Tenant stats:")
    print(json.dumps(stats, indent=2))
