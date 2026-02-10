# PATH C Production Hardening - Status Summary

## Achievements ✅

1. **Monitoring Dashboard**: Cloud Monitoring dashboard deployed with 10+ widgets
2. **HTTPS Ingress**: Google-managed SSL certificate provisioning (pending completion)
3. **Operations Runbook**: Comprehensive PRODUCTION_OPERATIONS.md created
4. **Backup System**: GCS backups configured (6-hour CronJob)
5. **API Server Autoscaling**: HPA configured (2-10 replicas)

## Critical Issue Discovered 🛑

### Volume Conflict: ReadWriteOnce PVCs with Multiple Pods

**Problem**: Orchestrator + Filesystem Watcher both need access to vaults/logs PVCs
- PVCs created as `ReadWriteOnce` (single node only)
- Tried pod affinity to colocate - failed due to resource constraints
- Switching to `ReadWriteMany` requires:
  - Delete existing PVCs (data loss!)
  - Recreate with Filestore storage class
  - Higher cost (~$0.24/GB/month vs $0.04/GB/month)

**Decision Required**: Accept data loss and switch to RWX, OR redesign architecture

## Recommended Solution ✅

**Simplify Architecture**: Remove orchestrator deployment entirely

```yaml
# CURRENT (Complex)
orchestrator pod → writes to PVC
watcher-filesystem pod → reads from PVC
api-server pods → read Dashboard

# RECOMMENDED (Simple)
orchestrator runs in background on LOCAL machine
watchers → write to GCS directly (no PVC)
api-server → reads from GCS
```

**Benefits**:
- Eliminates PVC conflicts
- Lower costs (no Filestore needed)
- Simpler deployment
- **Aligns with Platinum Tier**: Orchestrator runs locally anyway!

**Implementation**:
1. Delete `orchestrator` deployment from GKE
2. Run orchestrator.py locally (PowerShell)
3. Update watchers to write tasks to GCS
4. Update API server to read from GCS

## Path Forward

### Option A: Continue with GKE-only (Complex)
- Delete PVCs (lose current data)
- Recreate as ReadWriteMany (Filestore)
- Higher costs, complex setup
- Not aligned with Platinum architecture

### Option B: Hybrid Local+Cloud (Simple) ✅
- Keep orchestrator local
- Deploy only watchers + API server to GKE
- Lower costs, simpler architecture
- **Already matches Platinum Tier requirements!**

## Recommendation

> **Choose Option B**: Pivot to hybrid architecture NOW before PATH A

This actually completes both:
- PATH C (Production Hardening): Simpler = More reliable
- PATH A head-start (Platinum): Local orchestrator already required

## Next Steps (Option B)

1. Delete orchestrator deployment from GKE
2. Configure watchers to write to Cloud Storage
3. Run local orchestrator with vault sync
4. Test end-to-end flow
5. Mark PATH C complete
6. Start PATH A (vault sync, already underway!)

---

**Status**: Blocked on decision
**Blocker**: PVC architecture incompatible with multi-pod deployment
**Resolution**: Switch to hybrid local+cloud architecture (recommended)
