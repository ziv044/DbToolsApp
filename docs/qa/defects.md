# DbTools QA Defect Tracking

## Test Session: 2026-01-17

### Testing Approach
Browser-based end-to-end testing against PRD requirements.

---

## Defect Summary

| ID | Epic | Feature | Severity | Status | Description |
|----|------|---------|----------|--------|-------------|
| DEF-001 | 2 | Servers Page | Critical | Fixed | Merge conflict markers in Servers.tsx caused build failure |
| DEF-002 | 4 | Policies/Jobs/Alerts | Critical | Fixed | Database tables missing - migrations not run on tenant DB |

---

## Fixed Defects

### DEF-001: Merge conflict in Servers.tsx
- **Epic**: 2 - Server Management
- **Feature**: Servers page
- **Severity**: Critical
- **Status**: Fixed
- **Steps to Reproduce**:
  1. Open app in browser
  2. Navigate to Servers page
- **Expected**: Page loads and shows server list
- **Actual**: Vite build error due to git conflict markers (<<<<<<< HEAD)
- **Error Messages**: `Pre-transform error: Unexpected token (23:3)`
- **Fix Applied**: Resolved merge conflict in `frontend/src/pages/Servers.tsx` - kept tenant-scoped query keys version
- **Verified**: [x]

### DEF-002: Missing tenant database tables
- **Epic**: 4 - Policies, Scheduler & Alerts
- **Feature**: Policies, Jobs, Alerts APIs
- **Severity**: Critical
- **Status**: Fixed
- **Steps to Reproduce**:
  1. Call any API: GET /api/policies, /api/jobs, /api/alerts
- **Expected**: Returns JSON with data
- **Actual**: 500 error - `relation "policies" does not exist`
- **Error Messages**: `sqlalchemy.exc.ProgrammingError: relation "policies" does not exist`
- **Fix Applied**: Ran tenant database migrations (007 -> 011) which created: policies, policy_versions, jobs, job_executions, policy_deployments, alert_rules, alerts tables
- **Verified**: [x]

---

## Epic 1: Foundation & Multi-Tenancy

### Test Checklist
- [x] App loads at http://localhost:5177
- [x] Tenant selector dropdown appears in header
- [x] Tenant list loads from API
- [x] Can select a tenant
- [x] Dashboard shows tenant name
- [x] Sidebar navigation works (Dashboard, Servers, Groups, Policies, Jobs, Settings)
- [ ] Admin > Tenants page accessible at /admin/tenants
- [ ] Can create new tenant
- [ ] Can suspend/activate tenant
- [ ] Can delete tenant (soft delete)

---

## Epic 2: Server Management & Groups

### Test Checklist
- [x] Servers page loads at /servers
- [x] Empty state shows if no servers
- [x] "Add Server" button works
- [ ] Add Server modal opens with fields: Name, Host, Port, Instance, Auth Type, Username, Password
- [ ] "Test Connection" button works
- [ ] Can save server after successful connection test
- [x] Server appears in list after creation
- [x] Server list shows: Name, Host, Status
- [ ] Can click server to view detail page
- [ ] Server detail shows connection info, groups, labels
- [ ] Can edit server
- [ ] Can delete server
- [x] Groups page loads at /groups
- [ ] Can create new group
- [ ] Can add servers to group
- [ ] Can remove servers from group
- [ ] Labels work on server detail page

---

## Epic 3: Data Collection & Dashboard

### Test Checklist
- [x] Dashboard shows summary cards (Total, Healthy, Warning, Critical, Offline, Unknown)
- [x] Cards are clickable (filter by status)
- [x] Server status grid displays
- [x] Auto-refresh works (configurable interval)
- [ ] Server detail has Metrics tab
- [ ] Metrics charts display (CPU, Memory, Connections)
- [ ] Time range selector works
- [x] Real-time status updates work

---

## Epic 4: Policies, Scheduler & Alerts

### Test Checklist
- [x] Policies page loads at /policies
- [ ] Can create new policy (backup, maintenance, etc.)
- [ ] Policy versioning works
- [ ] Can deploy policy to groups
- [x] Jobs page loads at /jobs
- [ ] Can create new job
- [ ] Job execution history displays
- [x] Alerts page loads at /alerts
- [x] Alert rules page loads at /alert-rules
- [ ] Can create alert rule
- [ ] Active alerts display
- [x] Activity log page loads at /activity

---

## API Verification Results (2026-01-17)

All backend APIs tested and working:

| Endpoint | Status | Notes |
|----------|--------|-------|
| GET /api/health | OK | Returns healthy |
| GET /api/tenants | OK | 1 tenant (demo) |
| GET /api/servers | OK | 1 server configured |
| GET /api/groups | OK | 0 groups |
| GET /api/labels | OK | 0 labels |
| GET /api/policies | OK | 0 policies |
| GET /api/jobs | OK | 0 jobs |
| GET /api/alerts | OK | 0 alerts |
| GET /api/alert-rules | OK | 0 rules |
| GET /api/activity | OK | 0 entries |
| GET /api/servers/health | OK | 1 server (unknown status) |
| GET /api/settings/retention | OK | 30 days retention |

---

## Next Steps

1. Continue browser testing of UI interactions
2. Test CRUD operations for each feature
3. Test connection testing with real SQL Server
4. Test policy creation and deployment
5. Test job scheduling and execution
