# Query Analytics Dashboard - Brownfield Enhancement Architecture

## Document Info

| Field | Value |
|-------|-------|
| **Feature** | Query Analytics Dashboard |
| **Type** | Brownfield Enhancement |
| **Version** | 1.0 |
| **Date** | 2026-01-18 |
| **Author** | Winston (Architect) |
| **Status** | Ready for Implementation |

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-01-18 | 1.0 | Initial architecture document | Winston (Architect) |

---

## 1. Introduction

### 1.1 Purpose

This document defines the architecture for adding a **Query Analytics Dashboard** to DbTools - a Grafana-like visualization layer that provides expert SQL Server DBA observability for running queries.

### 1.2 Scope

The enhancement adds:
1. **Dashboard Panel Framework** - Reusable visualization components (Pie, Bar, Stacked Bar, Table, Time Series)
2. **Expert DBA Dashboards** - Pre-built analytics dashboards for query monitoring
3. **Data Model Extensions** - Additional fields for query context (login, host, application, blocking)
4. **API Layer** - Aggregation endpoints for dashboard data

### 1.3 Goals

- Provide at-a-glance visibility into SQL Server query activity
- Identify blocking chains instantly
- Surface top resource consumers (CPU, I/O, duration)
- Enable breakdown analysis by database, login, host, and application
- Deliver value from collected query data to customers

### 1.4 Non-Goals (MVP)

- User-customizable dashboard layouts (fixed expert layouts only)
- Multi-server aggregate views (single server focus)
- Query plan analysis
- Historical trend comparisons

---

## 2. Existing System Analysis

### 2.1 Current Architecture

| Component | Technology | Status |
|-----------|------------|--------|
| Backend | Python 3.11+ / Flask 3.x / SQLAlchemy 2.x | Stable |
| Frontend | React 19 / TypeScript / Vite / Tailwind CSS 4 | Stable |
| Charts | Recharts 3.6.0 | Already in use |
| State | TanStack Query 5.x / Zustand 5.x | Already in use |
| Database | PostgreSQL 16 | Stable |

### 2.2 Current Data Model

`RunningQuerySnapshot` at `backend/app/models/tenant.py` captures:
- session_id, request_id, database_name
- query_text, start_time, duration_ms
- status, wait_type, wait_time_ms
- cpu_time_ms, logical_reads, physical_reads, writes

### 2.3 Data Gap Analysis

**Missing fields for breakdowns:**

| Field | Source | Purpose |
|-------|--------|---------|
| `login_name` | sys.dm_exec_sessions | Per-login breakdown |
| `host_name` | sys.dm_exec_sessions | Per-host breakdown |
| `program_name` | sys.dm_exec_sessions | Per-application breakdown |
| `blocking_session_id` | sys.dm_exec_requests | Blocking chain visualization |

---

## 3. Design Decisions

### 3.1 Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Dashboard customization | Fixed expert layouts | Simpler, ensures best practices |
| Time range selection | Custom date picker + presets | Full flexibility |
| Server scope | Single server focus | Cleaner UX, simpler queries |
| Chart library | Recharts (existing) | Already in bundle, sufficient |
| Panel architecture | Generic wrapper + specialized panels | Consistency, reusability |

### 3.2 Trade-offs

| Trade-off | Decision | Impact |
|-----------|----------|--------|
| Always join dm_exec_sessions | Accept +1-2ms overhead | Required for breakdowns |
| Nullable new columns | Accept NULL for historical data | No data migration needed |
| Top 10 limits on breakdowns | Accept, group rest as "Other" | Performance, cleaner UI |

---

## 4. Data Model Changes

### 4.1 Extended RunningQuerySnapshot

```python
class RunningQuerySnapshot(TenantBase):
    __tablename__ = 'running_query_snapshots'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    server_id = Column(UUID(as_uuid=True), ForeignKey('servers.id', ondelete='CASCADE'), nullable=False)
    collected_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    # Query identification
    session_id = Column(Integer, nullable=False)
    request_id = Column(Integer, nullable=True)
    database_name = Column(String(128), nullable=True)

    # NEW: Session context for breakdowns
    login_name = Column(String(128), nullable=True)
    host_name = Column(String(128), nullable=True)
    program_name = Column(String(128), nullable=True)

    # Query text
    query_text = Column(Text, nullable=True)

    # Timing
    start_time = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)

    # Status & waits
    status = Column(String(30), nullable=True)
    wait_type = Column(String(60), nullable=True)
    wait_time_ms = Column(Integer, nullable=True)

    # NEW: Blocking information
    blocking_session_id = Column(Integer, nullable=True)

    # Resource usage
    cpu_time_ms = Column(Integer, nullable=True)
    logical_reads = Column(Integer, nullable=True)
    physical_reads = Column(Integer, nullable=True)
    writes = Column(Integer, nullable=True)

    # Indexes
    __table_args__ = (
        Index('ix_running_queries_server_time', 'server_id', 'collected_at'),
        Index('ix_running_queries_blocking', 'server_id', 'blocking_session_id'),
        Index('ix_running_queries_database', 'server_id', 'database_name'),
        Index('ix_running_queries_login', 'server_id', 'login_name'),
    )
```

### 4.2 Migration

```python
def upgrade():
    op.add_column('running_query_snapshots',
        sa.Column('login_name', sa.String(128), nullable=True))
    op.add_column('running_query_snapshots',
        sa.Column('host_name', sa.String(128), nullable=True))
    op.add_column('running_query_snapshots',
        sa.Column('program_name', sa.String(128), nullable=True))
    op.add_column('running_query_snapshots',
        sa.Column('blocking_session_id', sa.Integer, nullable=True))

    op.create_index('ix_running_queries_blocking', 'running_query_snapshots',
        ['server_id', 'blocking_session_id'])
    op.create_index('ix_running_queries_database', 'running_query_snapshots',
        ['server_id', 'database_name'])
    op.create_index('ix_running_queries_login', 'running_query_snapshots',
        ['server_id', 'login_name'])
```

---

## 5. Collector Changes

### 5.1 Updated SQL Query

```sql
SELECT
    r.session_id,
    r.request_id,
    r.blocking_session_id,
    DB_NAME(r.database_id) AS database_name,
    s.login_name,
    s.host_name,
    s.program_name,
    SUBSTRING(t.text,
        (r.statement_start_offset/2) + 1,
        ((CASE WHEN r.statement_end_offset = -1
             THEN LEN(CONVERT(NVARCHAR(MAX), t.text)) * 2
             ELSE r.statement_end_offset
        END) - r.statement_start_offset) / 2 + 1) AS query_text,
    r.start_time,
    DATEDIFF(MILLISECOND, r.start_time, GETDATE()) AS duration_ms,
    r.status,
    r.wait_type,
    r.wait_time AS wait_time_ms,
    r.cpu_time AS cpu_time_ms,
    r.logical_reads,
    r.reads AS physical_reads,
    r.writes
FROM sys.dm_exec_requests r
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) t
JOIN sys.dm_exec_sessions s ON r.session_id = s.session_id
WHERE r.session_id > 50
  AND r.session_id != @@SPID
  AND r.sql_handle IS NOT NULL
ORDER BY r.start_time
```

### 5.2 Performance Impact

| Aspect | Before | After | Impact |
|--------|--------|-------|--------|
| Query Complexity | Conditional JOIN | Always JOIN | +1-2ms |
| Data Transfer | ~200 bytes/row | ~350 bytes/row | +75% per row |
| SQL Server Load | Minimal | Minimal | Negligible |

---

## 6. API Design

### 6.1 Endpoint Overview

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/analytics/queries/running` | Currently running queries |
| GET | `/api/analytics/queries/top` | Top N by metric |
| GET | `/api/analytics/queries/blocking-chains` | Active blocking chains |
| GET | `/api/analytics/breakdowns/by-database` | Distribution by database |
| GET | `/api/analytics/breakdowns/by-login` | Distribution by login |
| GET | `/api/analytics/breakdowns/by-host` | Distribution by host |
| GET | `/api/analytics/breakdowns/by-application` | Distribution by app |
| GET | `/api/analytics/breakdowns/by-wait-type` | Wait type distribution |
| GET | `/api/analytics/timeseries/query-count` | Query count over time |
| GET | `/api/analytics/timeseries/avg-duration` | Avg duration over time |
| GET | `/api/analytics/timeseries/total-cpu` | Total CPU over time |

### 6.2 Common Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `server_id` | UUID | required | Target server |
| `start` | ISO datetime | now - 1h | Range start |
| `end` | ISO datetime | now | Range end |

### 6.3 Response Formats

**PieData (Breakdowns):**
```json
{
  "dimension": "database",
  "data": [
    {"label": "SalesDB", "value": 245},
    {"label": "InventoryDB", "value": 123}
  ],
  "total": 489
}
```

**BarData (Top Queries):**
```json
{
  "metric": "cpu",
  "data": [
    {"label": "SELECT * FROM Orders...", "value": 45230, "session_id": 55}
  ],
  "unit": "ms"
}
```

**BlockingChain:**
```json
{
  "chains": [
    {
      "session_id": 55,
      "login_name": "batch_user",
      "query_text": "UPDATE Customers...",
      "duration_ms": 45000,
      "blocked": [
        {
          "session_id": 62,
          "login_name": "web_user",
          "blocked": []
        }
      ]
    }
  ],
  "total_blocked_sessions": 1
}
```

**TimeSeriesData:**
```json
{
  "metric": "query_count",
  "interval": "5m",
  "data": [
    {"time": "2026-01-18T10:00:00Z", "value": 45},
    {"time": "2026-01-18T10:05:00Z", "value": 52}
  ],
  "unit": "queries"
}
```

---

## 7. Frontend Architecture

### 7.1 New Files

```
frontend/src/
├── components/
│   ├── panels/
│   │   ├── index.ts
│   │   ├── Panel.tsx
│   │   ├── PiePanel.tsx
│   │   ├── BarPanel.tsx
│   │   ├── StackedBarPanel.tsx
│   │   ├── TablePanel.tsx
│   │   ├── TimeSeriesPanel.tsx
│   │   └── BlockingTreePanel.tsx
│   └── analytics/
│       ├── DateRangePicker.tsx
│       ├── ServerSelector.tsx
│       └── QueryDetailModal.tsx
├── pages/
│   └── Analytics/
│       ├── index.tsx
│       ├── QueryDashboard.tsx
│       └── hooks/
│           └── useAnalyticsData.ts
├── services/
│   └── analyticsService.ts
└── types/
    └── analytics.ts
```

### 7.2 Panel Components

| Component | Recharts Base | Purpose |
|-----------|---------------|---------|
| Panel | N/A | Generic wrapper (loading, error, empty) |
| PiePanel | PieChart | Distribution charts |
| BarPanel | BarChart | Top N rankings |
| StackedBarPanel | BarChart (stacked) | Multi-series categories |
| TablePanel | N/A (custom) | Sortable data tables |
| TimeSeriesPanel | LineChart | Metrics over time |
| BlockingTreePanel | N/A (custom) | Hierarchical blocking tree |

### 7.3 Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Query Analytics                    [Server Dropdown] [Date Range Picker]  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────┐  ┌────────────────────────────────────────┐ │
│  │    BLOCKING CHAINS         │  │     CURRENTLY RUNNING QUERIES          │ │
│  │    (BlockingTreePanel)     │  │          (TablePanel)                  │ │
│  └────────────────────────────┘  └────────────────────────────────────────┘ │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │ TOP BY DURATION  │  │  TOP BY CPU      │  │  TOP BY I/O      │          │
│  │   (BarPanel)     │  │   (BarPanel)     │  │   (BarPanel)     │          │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘          │
│                                                                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                        │
│  │ BY DB   │  │BY LOGIN │  │BY HOST  │  │BY APP   │                        │
│  │(Pie)    │  │(Pie)    │  │(Pie)    │  │(Pie)    │                        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘                        │
│                                                                              │
│  ┌────────────────────────────────────────────┐  ┌─────────────────────┐   │
│  │        QUERY COUNT OVER TIME               │  │   WAIT TYPES        │   │
│  │         (TimeSeriesPanel)                  │  │    (PiePanel)       │   │
│  └────────────────────────────────────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.4 Data Fetching Strategy

| Query Type | Stale Time | Refetch Interval |
|------------|------------|------------------|
| Running Queries | 5s | 10s |
| Blocking Chains | 5s | 10s |
| Top Queries | 30s | - |
| Breakdowns | 30s | - |
| Time Series | 30s | - |

---

## 8. Implementation Plan

### 8.1 Phase 1: Data Foundation

| Story | Description | Files |
|-------|-------------|-------|
| 1.1 | Extend RunningQuerySnapshot model | `backend/app/models/tenant.py` |
| 1.2 | Update MetricCollector SQL query | `backend/workers/metric_collector.py` |
| 1.3 | Run migration on all tenant databases | Migration scripts |

### 8.2 Phase 2: API Layer

| Story | Description | Files |
|-------|-------------|-------|
| 2.1 | Analytics blueprint + running queries | `backend/app/api/analytics.py` |
| 2.2 | Blocking chains endpoint | `backend/app/api/analytics.py` |
| 2.3 | Top queries endpoint | `backend/app/api/analytics.py` |
| 2.4 | Breakdown endpoints (5) | `backend/app/api/analytics.py` |
| 2.5 | Time series endpoints | `backend/app/api/analytics.py` |

### 8.3 Phase 3: Frontend Panels

| Story | Description | Files |
|-------|-------------|-------|
| 3.1 | Panel + PiePanel + BarPanel | `frontend/src/components/panels/` |
| 3.2 | TablePanel + TimeSeriesPanel | `frontend/src/components/panels/` |
| 3.3 | BlockingTreePanel | `frontend/src/components/panels/` |
| 3.4 | DateRangePicker + ServerSelector | `frontend/src/components/analytics/` |

### 8.4 Phase 4: Dashboard Assembly

| Story | Description | Files |
|-------|-------------|-------|
| 4.1 | Analytics service + React Query hooks | `frontend/src/services/`, hooks |
| 4.2 | QueryDashboard page + routing | `frontend/src/pages/Analytics/` |
| 4.3 | QueryDetailModal | `frontend/src/components/analytics/` |
| 4.4 | Navigation integration + polish | Sidebar, routing |

### 8.5 Dependencies

```
1.1 Model ──► 1.2 Collector ──► 1.3 Migration
    │
    └──► 2.1-2.5 API Endpoints
              │
3.1-3.4 Panels ──► 4.1 Hooks ──► 4.2 Dashboard ──► 4.3-4.4 Polish
```

---

## 9. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Large data volumes slow aggregations | Medium | High | Indexes, LIMIT, consider materialized views |
| Blocking chain recursion too deep | Low | Medium | Max depth limit (10), circuit breaker |
| Date picker UX confusion | Low | Low | Clear presets, good defaults |
| Collector query performance | Low | Medium | Already tested <5ms overhead |

---

## 10. Success Criteria

- [ ] All 4 new fields captured by collector
- [ ] All 11 API endpoints functional and performant (<500ms)
- [ ] Dashboard renders all panels correctly
- [ ] Blocking chain visualization works for chains up to 10 deep
- [ ] Date range picker supports custom ranges up to 30 days
- [ ] Auto-refresh works for live data (10s interval)
- [ ] Query detail modal shows all information

---

## Appendix A: TypeScript Types

```typescript
interface PieData {
  label: string
  value: number
  color?: string
}

interface BarData {
  label: string
  value: number
  session_id?: number
}

interface TimeSeriesData {
  time: string
  value: number
  series?: string
}

interface TableData {
  columns: { key: string; label: string; sortable?: boolean }[]
  rows: Record<string, any>[]
  total_rows?: number
}

interface BlockingChain {
  session_id: number
  login_name: string
  host_name: string
  program_name: string
  database_name: string
  query_text: string
  duration_ms: number
  wait_type: string | null
  blocked: BlockingChain[]
}

interface DateRange {
  start: Date
  end: Date
}
```

---

## Appendix B: SQL Server DMV Reference

| DMV | Fields Used |
|-----|-------------|
| sys.dm_exec_requests | session_id, request_id, blocking_session_id, database_id, sql_handle, start_time, status, wait_type, wait_time, cpu_time, logical_reads, reads, writes, statement_start_offset, statement_end_offset |
| sys.dm_exec_sessions | session_id, login_name, host_name, program_name |
| sys.dm_exec_sql_text | text (query text via sql_handle) |

---

*Document generated by Winston (Architect) using BMAD brownfield-architecture-tmpl v2.0*
