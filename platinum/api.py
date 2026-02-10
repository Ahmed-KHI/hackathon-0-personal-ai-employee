"""
Simple API for Personal AI Employee Management
FastAPI-based REST API for monitoring and control
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from platinum.tenant_manager import TenantManager
from platinum.compliance_logger import ComplianceLogger

app = FastAPI(
    title="Personal AI Employee API",
    description="Platinum Tier Management API",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize managers
tenant_manager = TenantManager()

# Models
class TenantCreate(BaseModel):
    tenant_id: str
    name: str
    admin_email: str
    tier: str = "platinum"

class TaskCreate(BaseModel):
    title: str
    content: str
    priority: str = "medium"

# Authentication (simple API key for now)
API_KEY = "platinum-api-key-2026"  # In production: use proper auth

def verify_api_key(x_api_key: str = Header()):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

# Routes
@app.get("/")
def read_root():
    return {
        "service": "Personal AI Employee API",
        "version": "1.0.0",
        "tier": "Platinum",
        "status": "operational"
    }

@app.get("/health")
def health_check():
    """Health check endpoint for Kubernetes"""
    return {
        "status": "healthy",
        "timestamp": "2026-02-10T22:00:00Z"
    }

@app.get("/api/tenants")
def list_tenants(api_key: str = Depends(verify_api_key)):
    """List all tenants"""
    tenants = tenant_manager.list_tenants()
    return {
        "total": len(tenants),
        "tenants": tenants
    }

@app.post("/api/tenants")
def create_tenant(tenant: TenantCreate, api_key: str = Depends(verify_api_key)):
    """Create a new tenant"""
    try:
        config = {
            "name": tenant.name,
            "admin_email": tenant.admin_email,
            "tier": tenant.tier
        }
        result = tenant_manager.create_tenant(tenant.tenant_id, config)
        return {
            "status": "success",
            "tenant": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/tenants/{tenant_id}")
def get_tenant(tenant_id: str, api_key: str = Depends(verify_api_key)):
    """Get tenant details"""
    tenant = tenant_manager.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@app.get("/api/tenants/{tenant_id}/stats")
def get_tenant_stats(tenant_id: str, api_key: str = Depends(verify_api_key)):
    """Get tenant usage statistics"""
    try:
        stats = tenant_manager.get_tenant_stats(tenant_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/tenants/{tenant_id}/tasks")
def create_task(
    tenant_id: str,
    task: TaskCreate,
    api_key: str = Depends(verify_api_key)
):
    """Create a new task for tenant"""
    tenant = tenant_manager.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Create task file in tenant's Needs_Action folder
    vault_path = Path(tenant['vault_path'])
    tasks_dir = vault_path / "Needs_Action"
    
    import time
    task_id = f"API_TASK_{int(time.time())}"
    task_file = tasks_dir / f"{task_id}.md"
    
    task_content = f"""---
task_id: {task_id}
created: {time.strftime('%Y-%m-%dT%H:%M:%SZ')}
priority: {task.priority}
source: api
---

# {task.title}

{task.content}
"""
    
    task_file.write_text(task_content, encoding='utf-8')
    
    # Log to compliance
    compliance = ComplianceLogger(tenant_id)
    compliance.log_action(
        action="task_created_via_api",
        details={"task_id": task_id, "title": task.title},
        risk_level="low"
    )
    
    return {
        "status": "success",
        "task_id": task_id,
        "message": f"Task created in {tasks_dir}"
    }

@app.get("/api/tenants/{tenant_id}/audit")
def get_audit_trail(
    tenant_id: str,
    start_date: str,
    end_date: str,
    api_key: str = Depends(verify_api_key)
):
    """Get audit trail for tenant"""
    try:
        compliance = ComplianceLogger(tenant_id)
        entries = compliance.get_audit_trail(start_date, end_date)
        return {
            "tenant_id": tenant_id,
            "start_date": start_date,
            "end_date": end_date,
            "total_entries": len(entries),
            "entries": entries
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/tenants/{tenant_id}/compliance-report")
def get_compliance_report(
    tenant_id: str,
    start_date: str,
    end_date: str,
    api_key: str = Depends(verify_api_key)
):
    """Generate SOC2 compliance report"""
    try:
        compliance = ComplianceLogger(tenant_id)
        report = compliance.generate_compliance_report(start_date, end_date)
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/metrics")
def get_metrics(api_key: str = Depends(verify_api_key)):
    """Get system-wide metrics (Prometheus compatible)"""
    tenants = tenant_manager.list_tenants()
    
    total_tasks_in_progress = 0
    total_tasks_completed = 0
    total_pending_approvals = 0
    
    for tenant in tenants:
        if tenant['status'] == 'active':
            stats = tenant_manager.get_tenant_stats(tenant['tenant_id'])
            total_tasks_in_progress += stats['tasks_in_progress']
            total_tasks_completed += stats['tasks_completed']
            total_pending_approvals += stats['pending_approvals']
    
    return {
        "total_tenants": len(tenants),
        "active_tenants": len([t for t in tenants if t['status'] == 'active']),
        "total_tasks_in_progress": total_tasks_in_progress,
        "total_tasks_completed": total_tasks_completed,
        "total_pending_approvals": total_pending_approvals
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
