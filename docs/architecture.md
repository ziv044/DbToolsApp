# DbTools Fullstack Architecture Document

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-01-17 | 1.0 | Initial architecture document | Winston (Architect) |

---

## 1. Introduction

This document outlines the complete fullstack architecture for DbTools, a multi-tenant SQL Server management platform. It covers backend systems, frontend implementation, and their integration, serving as the single source of truth for AI-driven development.

DbTools consolidates functionality from tools like RedGate, SentryOne, and SolarWinds DPA into a unified web platform for DBAs. The MVP focuses exclusively on SQL Server management with a database-per-tenant isolation model.

### 1.1 Starter Template

**N/A - Greenfield project**

This is a new project built from scratch using Python Flask (backend) and React with Vite (frontend).

---

## 2. High Level Architecture

### 2.1 Technical Summary

DbTools follows a **modular monolith** architecture deployed as a traditional server application on Windows. The frontend is a React SPA communicating with a Flask REST API backend. Multi-tenancy is achieved through database-per-tenant isolation, where each customer gets their own PostgreSQL database. Background workers handle metric collection from SQL Server instances and job scheduling via APScheduler. The architecture prioritizes simplicity for MVP while maintaining clear module boundaries for future scaling.

### 2.2 Platform and Infrastructure

**Platform:** Windows Server (On-Premises/Self-Hosted)
**Key Services:**
- PostgreSQL 16 (Application Database)
- Python Flask (REST API)
- React + Vite (Frontend SPA)
- Waitress (Production WSGI Server)
- APScheduler (Job Scheduling)

**Deployment:** Single Windows Server host with Nginx/IIS reverse proxy

### 2.3 Repository Structure

**Structure:** Single repository with separate frontend/backend folders
**Monorepo Tool:** N/A (simple folder separation)
**Package Organization:**
```
DbToolsApp/
├── backend/          # Flask API + Workers
├── frontend/         # React SPA
├── docs/             # Documentation
└── scripts/          # Utility scripts
```

### 2.4 High Level Architecture Diagram

```mermaid
graph TB
    subgraph "User Layer"
        Browser[Web Browser]
    end

    subgraph "Frontend"
        React[React SPA<br/>Vite + TypeScript]
    end

    subgraph "Backend Services"
        API[Flask REST API<br/>Port 5000]
        MetricWorker[Metric Collector<br/>Worker]
        JobWorker[Job Scheduler<br/>APScheduler Worker]
    end

    subgraph "Data Layer"
        SystemDB[(dbtools_system<br/>PostgreSQL)]
        TenantDB[(dbtools_tenant_*<br/>PostgreSQL)]
    end

    subgraph "External"
        SQLServers[(Target SQL Server<br/>Instances)]
    end

    Browser --> React
    React -->|REST API| API
    API --> SystemDB
    API --> TenantDB
    API -->|pyodbc| SQLServers
    MetricWorker --> TenantDB
    MetricWorker -->|pyodbc| SQLServers
    JobWorker --> TenantDB
    JobWorker -->|pyodbc| SQLServers
```

### 2.5 Architectural Patterns

- **Modular Monolith:** Single deployable with clear module boundaries - _Rationale:_ Simplicity for MVP while enabling future service extraction
- **Repository Pattern:** Abstract data access from SQLAlchemy ORM - _Rationale:_ Testability and flexibility for future database changes
- **Service Layer Pattern:** Business logic separated from API routes - _Rationale:_ Reusable logic between API and background workers
- **Database-per-Tenant:** Isolated PostgreSQL database per customer - _Rationale:_ Maximum data isolation, simplified backup/restore per tenant
- **Component-Based UI:** React components with TypeScript - _Rationale:_ Maintainability, type safety, and reusability
- **Server State Management:** TanStack Query for API data - _Rationale:_ Automatic caching, background refetching, optimistic updates

---

## 3. Tech Stack

| Category | Technology | Version | Purpose | Rationale |
|----------|------------|---------|---------|-----------|
| Frontend Language | TypeScript | 5.x | Type-safe frontend development | Catch errors at compile time, better IDE support |
| Frontend Framework | React | 18.x | UI component library | Industry standard, large ecosystem, hooks-based |
| Build Tool | Vite | 5.x | Frontend bundling and dev server | Fast HMR, native ESM, excellent DX |
| UI Component Library | shadcn/ui | Latest | Accessible component primitives | Copy-paste components, full customization control |
| CSS Framework | Tailwind CSS | 3.x | Utility-first styling | Rapid development, consistent design, small bundle |
| State Management | TanStack Query + Zustand | 5.x / 4.x | Server and client state | TanStack for API, Zustand for UI state |
| Backend Language | Python | 3.11+ | Backend development | Team expertise, excellent SQL Server libraries |
| Backend Framework | Flask | 3.x | REST API framework | Lightweight, flexible, extensive extensions |
| ORM | SQLAlchemy | 2.x | Database abstraction | Mature, well-documented, async support |
| Database | PostgreSQL | 16 | Application data storage | Robust, multi-database support, JSON capabilities |
| SQL Server Connector | pyodbc | 5.x | SQL Server connectivity | Native ODBC, Windows Auth support |
| Job Scheduler | APScheduler | 3.x | Background job scheduling | No Redis dependency, persistent job store |
| Encryption | cryptography (Fernet) | Latest | Credential encryption | Symmetric encryption, standard library |
| API Style | REST | - | API architecture | Simplicity, wide tooling support |
| Backend Testing | pytest | 8.x | Unit and integration testing | Fixtures, parametrization, plugins |
| Frontend Testing | Vitest + Testing Library | Latest | Component and unit testing | Vite-native, React Testing Library patterns |
| Migrations | Alembic | 1.x | Database schema migrations | SQLAlchemy integration, version control |
| WSGI Server | Waitress | Latest | Production server | Windows-compatible, production-ready |

---

## 4. Data Models

### 4.1 Tenant (System Database)

**Purpose:** Represents a customer organization in the multi-tenant system

```typescript
interface Tenant {
  id: string;              // UUID
  name: string;            // Display name
  slug: string;            // URL-safe identifier, database suffix
  status: 'active' | 'suspended' | 'pending';
  settings: TenantSettings;
  createdAt: Date;
  updatedAt: Date;
}

interface TenantSettings {
  timezone: string;
  alertEmail?: string;
  retentionDays: number;
}
```

**Relationships:**
- One Tenant → One dedicated PostgreSQL database (dbtools_tenant_{slug})

---

### 4.2 Server

**Purpose:** Represents a monitored SQL Server instance

```typescript
interface Server {
  id: string;              // UUID
  name: string;            // Display name
  hostname: string;        // Server hostname or IP
  port: number;            // Default 1433
  instanceName?: string;   // Named instance
  authType: 'sql' | 'windows';
  username?: string;       // For SQL auth
  encryptedPassword?: string;  // Fernet encrypted
  status: 'online' | 'offline' | 'warning' | 'unknown';
  lastChecked?: Date;
  createdAt: Date;
  updatedAt: Date;
}
```

**Relationships:**
- Server belongs to many Groups (many-to-many)
- Server has many MetricSnapshots
- Server has many JobExecutions

---

### 4.3 ServerGroup

**Purpose:** Logical grouping of servers for policy application

```typescript
interface ServerGroup {
  id: string;
  name: string;
  description?: string;
  color?: string;          // UI display color
  createdAt: Date;
  updatedAt: Date;
}
```

**Relationships:**
- Group has many Servers (many-to-many via server_group_members)
- Group has many Policies applied to it

---

### 4.4 Policy

**Purpose:** Automated task definition applied to server groups

```typescript
interface Policy {
  id: string;
  name: string;
  description?: string;
  type: 'backup' | 'maintenance' | 'custom';
  enabled: boolean;
  schedule: CronSchedule;
  configuration: PolicyConfig;
  createdAt: Date;
  updatedAt: Date;
}

interface CronSchedule {
  expression: string;      // Cron expression
  timezone: string;
}

interface PolicyConfig {
  // Backup policy
  backupType?: 'full' | 'differential' | 'log';
  backupPath?: string;
  retentionDays?: number;

  // Maintenance policy
  indexRebuildThreshold?: number;
  updateStatistics?: boolean;

  // Custom policy
  sqlScript?: string;
}
```

**Relationships:**
- Policy applies to many Groups (many-to-many via policy_group_assignments)
- Policy generates many JobExecutions

---

### 4.5 Job

**Purpose:** Scheduled job instance derived from policies

```typescript
interface Job {
  id: string;
  policyId: string;
  serverId: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  scheduledAt: Date;
  startedAt?: Date;
  completedAt?: Date;
  result?: JobResult;
  createdAt: Date;
}

interface JobResult {
  success: boolean;
  message?: string;
  duration?: number;       // milliseconds
  details?: Record<string, any>;
}
```

**Relationships:**
- Job belongs to Policy
- Job belongs to Server

---

### 4.6 MetricSnapshot

**Purpose:** Point-in-time performance metrics from SQL Server

```typescript
interface MetricSnapshot {
  id: string;
  serverId: string;
  collectedAt: Date;
  metrics: ServerMetrics;
}

interface ServerMetrics {
  cpuPercent: number;
  memoryUsedMB: number;
  memoryTotalMB: number;
  activeConnections: number;
  blockedProcesses: number;
  batchRequestsPerSec: number;
  pageLifeExpectancy: number;
  diskIOPercent?: number;
}
```

---

### 4.7 Alert

**Purpose:** System-generated notifications based on thresholds

```typescript
interface Alert {
  id: string;
  serverId: string;
  type: 'cpu' | 'memory' | 'connection' | 'blocking' | 'offline' | 'job_failure';
  severity: 'info' | 'warning' | 'critical';
  message: string;
  acknowledged: boolean;
  acknowledgedAt?: Date;
  createdAt: Date;
}
```

---

### 4.8 Entity Relationship Diagram

```mermaid
erDiagram
    Server ||--o{ MetricSnapshot : "has many"
    Server ||--o{ Job : "has many"
    Server ||--o{ Alert : "has many"
    Server }o--o{ ServerGroup : "belongs to many"
    ServerGroup }o--o{ Policy : "has many"
    Policy ||--o{ Job : "generates"

    Server {
        uuid id PK
        string name
        string hostname
        int port
        string status
    }

    ServerGroup {
        uuid id PK
        string name
        string description
    }

    Policy {
        uuid id PK
        string name
        string type
        boolean enabled
        json schedule
        json configuration
    }

    Job {
        uuid id PK
        uuid policy_id FK
        uuid server_id FK
        string status
        datetime scheduled_at
    }

    MetricSnapshot {
        uuid id PK
        uuid server_id FK
        datetime collected_at
        json metrics
    }

    Alert {
        uuid id PK
        uuid server_id FK
        string type
        string severity
        boolean acknowledged
    }
```

---

## 5. API Specification

### 5.1 REST API Overview

```yaml
openapi: 3.0.0
info:
  title: DbTools API
  version: 1.0.0
  description: REST API for DbTools SQL Server Management Platform
servers:
  - url: http://localhost:5000/api
    description: Development server
```

### 5.2 Common Headers

All requests must include:
```
X-Tenant-Slug: {tenant_slug}    # Required for tenant context
Content-Type: application/json
```

### 5.3 API Endpoints

#### Tenants (System-level)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tenants` | List all tenants |
| POST | `/tenants` | Create new tenant (provisions database) |
| GET | `/tenants/{slug}` | Get tenant details |
| PATCH | `/tenants/{slug}` | Update tenant settings |

#### Servers

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/servers` | List all servers |
| POST | `/servers` | Register new server |
| GET | `/servers/{id}` | Get server details |
| PATCH | `/servers/{id}` | Update server |
| DELETE | `/servers/{id}` | Remove server |
| POST | `/servers/{id}/test-connection` | Test SQL Server connectivity |
| GET | `/servers/{id}/metrics` | Get server metrics (query params: from, to, interval) |

#### Server Groups

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/groups` | List all groups |
| POST | `/groups` | Create new group |
| GET | `/groups/{id}` | Get group with servers |
| PATCH | `/groups/{id}` | Update group |
| DELETE | `/groups/{id}` | Delete group |
| POST | `/groups/{id}/servers` | Add servers to group |
| DELETE | `/groups/{id}/servers/{serverId}` | Remove server from group |

#### Policies

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/policies` | List all policies |
| POST | `/policies` | Create new policy |
| GET | `/policies/{id}` | Get policy details |
| PATCH | `/policies/{id}` | Update policy |
| DELETE | `/policies/{id}` | Delete policy |
| POST | `/policies/{id}/enable` | Enable policy |
| POST | `/policies/{id}/disable` | Disable policy |
| POST | `/policies/{id}/groups` | Assign groups to policy |

#### Jobs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/jobs` | List jobs (query params: status, serverId, policyId, from, to) |
| GET | `/jobs/{id}` | Get job details with result |
| POST | `/jobs/{id}/cancel` | Cancel pending/running job |
| POST | `/jobs/run-now` | Trigger immediate job execution |

#### Metrics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/metrics/dashboard` | Dashboard summary metrics |
| GET | `/metrics/servers/{id}/history` | Historical metrics for server |

#### Alerts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/alerts` | List alerts (query params: severity, acknowledged, serverId) |
| POST | `/alerts/{id}/acknowledge` | Acknowledge alert |
| POST | `/alerts/acknowledge-all` | Acknowledge all alerts |

### 5.4 Request/Response Examples

#### Create Server
```json
// POST /api/servers
// Request
{
  "name": "Production SQL 01",
  "hostname": "sql-prod-01.internal",
  "port": 1433,
  "authType": "sql",
  "username": "dbtools_monitor",
  "password": "secure-password"
}

// Response 201
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Production SQL 01",
  "hostname": "sql-prod-01.internal",
  "port": 1433,
  "authType": "sql",
  "username": "dbtools_monitor",
  "status": "unknown",
  "createdAt": "2026-01-17T10:00:00Z",
  "updatedAt": "2026-01-17T10:00:00Z"
}
```

#### Create Policy
```json
// POST /api/policies
// Request
{
  "name": "Daily Full Backup",
  "type": "backup",
  "enabled": true,
  "schedule": {
    "expression": "0 2 * * *",
    "timezone": "America/New_York"
  },
  "configuration": {
    "backupType": "full",
    "backupPath": "\\\\backup-server\\sqlbackups\\{server}\\{database}",
    "retentionDays": 30
  }
}

// Response 201
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "Daily Full Backup",
  "type": "backup",
  "enabled": true,
  "schedule": { ... },
  "configuration": { ... },
  "createdAt": "2026-01-17T10:00:00Z"
}
```

### 5.5 Error Response Format

```typescript
interface ApiError {
  error: {
    code: string;           // e.g., "VALIDATION_ERROR", "NOT_FOUND"
    message: string;        // Human-readable message
    details?: {
      field?: string;
      reason?: string;
    }[];
    timestamp: string;
    requestId: string;
  }
}
```

---

## 6. Components

### 6.1 Backend Components

#### API Gateway (Flask Blueprints)

**Responsibility:** Handle HTTP requests, routing, request validation, response formatting

**Key Interfaces:**
- REST endpoints under `/api/*`
- Tenant middleware for multi-tenant context
- Error handling middleware

**Dependencies:** Services layer, Tenant Manager

**Technology:** Flask Blueprints, marshmallow for validation

---

#### Service Layer

**Responsibility:** Business logic, orchestration between repositories and external systems

**Key Interfaces:**
- `ServerService`: CRUD + connection testing
- `GroupService`: Group management + membership
- `PolicyService`: Policy CRUD + scheduling coordination
- `JobService`: Job lifecycle management
- `MetricService`: Metric storage and aggregation
- `AlertService`: Alert generation and management

**Dependencies:** Repositories, SQL Server Connector, Tenant Manager

**Technology:** Plain Python classes

---

#### Repository Layer

**Responsibility:** Data access abstraction, query building

**Key Interfaces:**
- `BaseRepository[T]`: Generic CRUD operations
- Entity-specific repositories with custom queries

**Dependencies:** SQLAlchemy, Tenant database sessions

**Technology:** SQLAlchemy ORM

---

#### Tenant Manager

**Responsibility:** Multi-tenant database connection management, database provisioning

**Key Interfaces:**
- `get_session(slug)`: Get scoped session for tenant
- `provision_database(slug)`: Create new tenant database
- `run_migrations(slug)`: Apply Alembic migrations

**Dependencies:** PostgreSQL, Alembic

**Technology:** SQLAlchemy engines, connection pooling

---

#### SQL Server Connector

**Responsibility:** Execute queries against target SQL Server instances

**Key Interfaces:**
- `test_connection(server)`: Verify connectivity
- `execute_query(server, sql)`: Run arbitrary SQL
- `collect_metrics(server)`: Gather performance metrics
- `run_backup(server, config)`: Execute backup command

**Dependencies:** pyodbc, ODBC Driver 18

**Technology:** pyodbc with connection pooling

---

#### Background Workers

**Responsibility:** Async processing outside request/response cycle

**Components:**
- `MetricCollector`: Polls servers for metrics on interval
- `JobScheduler`: APScheduler-based job execution
- `AlertProcessor`: Evaluates thresholds, generates alerts

**Dependencies:** Services, Tenant Manager, SQL Server Connector

**Technology:** APScheduler, threading

---

### 6.2 Frontend Components

#### API Client Layer

**Responsibility:** HTTP communication with backend

**Key Interfaces:**
- Axios instance with tenant header injection
- Service modules per domain (serverService, groupService, etc.)
- TanStack Query hooks for data fetching

**Technology:** Axios, TanStack Query

---

#### State Management

**Responsibility:** Client-side state management

**Key Interfaces:**
- `useTenantStore`: Current tenant context
- `useUIStore`: Sidebar state, modals, toasts
- TanStack Query for all server state

**Technology:** Zustand (client state), TanStack Query (server state)

---

#### Page Components

**Responsibility:** Route-level page composition

**Pages:**
- Dashboard, Servers, Groups, Policies, Jobs, Alerts

**Technology:** React Router, lazy loading

---

#### UI Components

**Responsibility:** Reusable UI building blocks

**Categories:**
- `ui/`: shadcn/ui primitives (Button, Card, Dialog, etc.)
- `layout/`: Header, Sidebar, PageContainer
- `common/`: StatusBadge, DataTable, ConfirmDialog
- Domain-specific: ServerCard, PolicyForm, JobTimeline

**Technology:** shadcn/ui, Tailwind CSS, Radix UI

---

### 6.3 Component Diagram

```mermaid
graph TB
    subgraph Frontend
        Pages[Page Components]
        Hooks[Custom Hooks]
        UIComponents[UI Components]
        Stores[State Stores]
        APIClient[API Client]

        Pages --> Hooks
        Pages --> UIComponents
        Hooks --> APIClient
        Hooks --> Stores
    end

    subgraph Backend
        Blueprints[API Blueprints]
        Middleware[Tenant Middleware]
        Services[Service Layer]
        Repos[Repository Layer]
        TenantMgr[Tenant Manager]
        SQLConnector[SQL Server Connector]
        Workers[Background Workers]

        Blueprints --> Middleware
        Middleware --> Services
        Services --> Repos
        Services --> SQLConnector
        Repos --> TenantMgr
        Workers --> Services
    end

    subgraph Data
        SystemDB[(System DB)]
        TenantDBs[(Tenant DBs)]
        SQLServers[(SQL Servers)]
    end

    APIClient -->|HTTP| Blueprints
    TenantMgr --> SystemDB
    TenantMgr --> TenantDBs
    SQLConnector --> SQLServers
```

---

## 7. Database Schema

### 7.1 System Database (dbtools_system)

```sql
-- Tenant Registry
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    settings JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_tenants_slug ON tenants(slug);
CREATE INDEX idx_tenants_status ON tenants(status);
```

### 7.2 Tenant Database Schema (dbtools_tenant_{slug})

```sql
-- Servers
CREATE TABLE servers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL DEFAULT 1433,
    instance_name VARCHAR(100),
    auth_type VARCHAR(20) NOT NULL,
    username VARCHAR(100),
    encrypted_password TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'unknown',
    last_checked TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_servers_status ON servers(status);
CREATE INDEX idx_servers_hostname ON servers(hostname);

-- Server Groups
CREATE TABLE server_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    color VARCHAR(7),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Server-Group Membership (Many-to-Many)
CREATE TABLE server_group_members (
    server_id UUID NOT NULL REFERENCES servers(id) ON DELETE CASCADE,
    group_id UUID NOT NULL REFERENCES server_groups(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (server_id, group_id)
);

CREATE INDEX idx_sgm_server ON server_group_members(server_id);
CREATE INDEX idx_sgm_group ON server_group_members(group_id);

-- Policies
CREATE TABLE policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT true,
    schedule JSONB NOT NULL,
    configuration JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_policies_type ON policies(type);
CREATE INDEX idx_policies_enabled ON policies(enabled);

-- Policy-Group Assignments (Many-to-Many)
CREATE TABLE policy_group_assignments (
    policy_id UUID NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
    group_id UUID NOT NULL REFERENCES server_groups(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (policy_id, group_id)
);

CREATE INDEX idx_pga_policy ON policy_group_assignments(policy_id);
CREATE INDEX idx_pga_group ON policy_group_assignments(group_id);

-- Jobs
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID REFERENCES policies(id) ON DELETE SET NULL,
    server_id UUID NOT NULL REFERENCES servers(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_server ON jobs(server_id);
CREATE INDEX idx_jobs_policy ON jobs(policy_id);
CREATE INDEX idx_jobs_scheduled ON jobs(scheduled_at);

-- Metric Snapshots
CREATE TABLE metric_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_id UUID NOT NULL REFERENCES servers(id) ON DELETE CASCADE,
    collected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    metrics JSONB NOT NULL
);

CREATE INDEX idx_metrics_server ON metric_snapshots(server_id);
CREATE INDEX idx_metrics_collected ON metric_snapshots(collected_at DESC);
CREATE INDEX idx_metrics_server_time ON metric_snapshots(server_id, collected_at DESC);

-- Partitioning for metrics (optional, for high-volume)
-- Consider partitioning by month if data volume is high

-- Alerts
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_id UUID NOT NULL REFERENCES servers(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    acknowledged BOOLEAN NOT NULL DEFAULT false,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_alerts_server ON alerts(server_id);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_acknowledged ON alerts(acknowledged);
CREATE INDEX idx_alerts_created ON alerts(created_at DESC);
```

---

## 8. Frontend Architecture

### 8.1 Component Organization

```
frontend/src/
├── components/
│   ├── ui/                    # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── dropdown-menu.tsx
│   │   ├── input.tsx
│   │   ├── select.tsx
│   │   ├── table.tsx
│   │   ├── tabs.tsx
│   │   ├── toast.tsx
│   │   └── ...
│   ├── layout/
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   ├── PageContainer.tsx
│   │   └── MainLayout.tsx
│   ├── common/
│   │   ├── StatusBadge.tsx
│   │   ├── DataTable.tsx
│   │   ├── ConfirmDialog.tsx
│   │   ├── LoadingSpinner.tsx
│   │   └── EmptyState.tsx
│   ├── dashboard/
│   │   ├── ServerHealthCard.tsx
│   │   ├── AlertsSummary.tsx
│   │   ├── JobsTimeline.tsx
│   │   └── MetricsChart.tsx
│   ├── servers/
│   │   ├── ServerCard.tsx
│   │   ├── ServerForm.tsx
│   │   ├── ServerList.tsx
│   │   └── ConnectionTestButton.tsx
│   ├── groups/
│   │   ├── GroupCard.tsx
│   │   ├── GroupForm.tsx
│   │   └── ServerSelector.tsx
│   ├── policies/
│   │   ├── PolicyCard.tsx
│   │   ├── PolicyForm.tsx
│   │   ├── CronBuilder.tsx
│   │   └── GroupAssignment.tsx
│   └── jobs/
│       ├── JobCard.tsx
│       ├── JobTimeline.tsx
│       └── JobDetails.tsx
```

### 8.2 Component Template

```typescript
// Example: components/servers/ServerCard.tsx
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { StatusBadge } from '@/components/common/StatusBadge';
import { Server } from '@/types/server';

interface ServerCardProps {
  server: Server;
  onEdit?: () => void;
  onDelete?: () => void;
}

export function ServerCard({ server, onEdit, onDelete }: ServerCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg">{server.name}</CardTitle>
        <StatusBadge status={server.status} />
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          {server.hostname}:{server.port}
        </p>
        {/* Actions */}
      </CardContent>
    </Card>
  );
}
```

### 8.3 State Management

#### TanStack Query for Server State

```typescript
// hooks/useServers.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { serverService } from '@/services/serverService';

export function useServers() {
  return useQuery({
    queryKey: ['servers'],
    queryFn: serverService.getAll,
    staleTime: 30 * 1000,        // 30 seconds
    refetchInterval: 60 * 1000,  // Refetch every minute
  });
}

export function useServer(id: string) {
  return useQuery({
    queryKey: ['servers', id],
    queryFn: () => serverService.getById(id),
    enabled: !!id,
  });
}

export function useCreateServer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: serverService.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['servers'] });
    },
  });
}
```

#### Zustand for UI State

```typescript
// stores/uiStore.ts
import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  toggleSidebar: () => void;

  activeModal: string | null;
  openModal: (modal: string) => void;
  closeModal: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

  activeModal: null,
  openModal: (modal) => set({ activeModal: modal }),
  closeModal: () => set({ activeModal: null }),
}));
```

#### Tenant Store

```typescript
// stores/tenantStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface TenantState {
  currentTenant: string | null;
  setTenant: (slug: string) => void;
  clearTenant: () => void;
}

export const useTenantStore = create<TenantState>()(
  persist(
    (set) => ({
      currentTenant: null,
      setTenant: (slug) => set({ currentTenant: slug }),
      clearTenant: () => set({ currentTenant: null }),
    }),
    { name: 'dbtools-tenant' }
  )
);
```

### 8.4 Routing Architecture

```typescript
// App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';

// Lazy load pages
const Dashboard = lazy(() => import('@/pages/Dashboard'));
const Servers = lazy(() => import('@/pages/Servers'));
const Groups = lazy(() => import('@/pages/Groups'));
const Policies = lazy(() => import('@/pages/Policies'));
const Jobs = lazy(() => import('@/pages/Jobs'));
const Alerts = lazy(() => import('@/pages/Alerts'));

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="servers" element={<Servers />} />
          <Route path="servers/:id" element={<ServerDetails />} />
          <Route path="groups" element={<Groups />} />
          <Route path="groups/:id" element={<GroupDetails />} />
          <Route path="policies" element={<Policies />} />
          <Route path="policies/:id" element={<PolicyDetails />} />
          <Route path="jobs" element={<Jobs />} />
          <Route path="alerts" element={<Alerts />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
```

### 8.5 API Client Setup

```typescript
// services/api.ts
import axios from 'axios';
import { useTenantStore } from '@/stores/tenantStore';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Inject tenant header on every request
apiClient.interceptors.request.use((config) => {
  const tenant = useTenantStore.getState().currentTenant;
  if (tenant) {
    config.headers['X-Tenant-Slug'] = tenant;
  }
  return config;
});

// Handle errors globally
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.error?.message || 'An error occurred';
    // Toast notification could go here
    console.error('API Error:', message);
    return Promise.reject(error);
  }
);
```

```typescript
// services/serverService.ts
import { apiClient } from './api';
import { Server, CreateServerInput, UpdateServerInput } from '@/types/server';

export const serverService = {
  getAll: async (): Promise<Server[]> => {
    const { data } = await apiClient.get('/servers');
    return data;
  },

  getById: async (id: string): Promise<Server> => {
    const { data } = await apiClient.get(`/servers/${id}`);
    return data;
  },

  create: async (input: CreateServerInput): Promise<Server> => {
    const { data } = await apiClient.post('/servers', input);
    return data;
  },

  update: async (id: string, input: UpdateServerInput): Promise<Server> => {
    const { data } = await apiClient.patch(`/servers/${id}`, input);
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/servers/${id}`);
  },

  testConnection: async (id: string): Promise<{ success: boolean; message: string }> => {
    const { data } = await apiClient.post(`/servers/${id}/test-connection`);
    return data;
  },
};
```

---

## 9. Backend Architecture

### 9.1 Flask Application Structure

```python
# app/__init__.py - App Factory
from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.extensions import db, migrate
from app.middleware.tenant import TenantMiddleware
from app.api import register_blueprints


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)

    # Register tenant middleware
    TenantMiddleware(app)

    # Register API blueprints
    register_blueprints(app)

    # Error handlers
    register_error_handlers(app)

    return app
```

### 9.2 Multi-Tenant Database Management

```python
# app/core/tenant_manager.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from flask import current_app
import threading


class TenantManager:
    """Manages database connections for multi-tenant architecture."""

    def __init__(self):
        self._engines = {}
        self._lock = threading.Lock()

    def get_tenant_db_url(self, slug: str) -> str:
        """Construct database URL for tenant."""
        host = current_app.config['TENANT_DB_HOST']
        port = current_app.config['TENANT_DB_PORT']
        user = current_app.config['TENANT_DB_USER']
        password = current_app.config['TENANT_DB_PASSWORD']
        return f"postgresql://{user}:{password}@{host}:{port}/dbtools_tenant_{slug}"

    def get_engine(self, slug: str):
        """Get or create engine for tenant (with connection pooling)."""
        if slug not in self._engines:
            with self._lock:
                if slug not in self._engines:
                    url = self.get_tenant_db_url(slug)
                    self._engines[slug] = create_engine(
                        url,
                        pool_size=5,
                        max_overflow=10,
                        pool_pre_ping=True
                    )
        return self._engines[slug]

    def get_session(self, slug: str):
        """Get scoped session for tenant."""
        engine = self.get_engine(slug)
        session_factory = sessionmaker(bind=engine)
        return scoped_session(session_factory)

    def provision_database(self, slug: str) -> None:
        """Create new tenant database and run migrations."""
        system_engine = create_engine(current_app.config['DATABASE_URL'])

        with system_engine.connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT")
            conn.execute(text(f"CREATE DATABASE dbtools_tenant_{slug}"))

        # Run Alembic migrations
        self._run_migrations(slug)

    def _run_migrations(self, slug: str):
        """Apply Alembic migrations to tenant database."""
        from alembic.config import Config
        from alembic import command

        alembic_cfg = Config("migrations/alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", self.get_tenant_db_url(slug))
        command.upgrade(alembic_cfg, "head")


# Global instance
tenant_manager = TenantManager()
```

### 9.3 Tenant Middleware

```python
# app/middleware/tenant.py
from flask import request, g
from functools import wraps

from app.extensions import db
from app.models.system import Tenant
from app.core.tenant_manager import tenant_manager


class TenantMiddleware:
    """Middleware to resolve tenant from request headers."""

    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        app.before_request(self.resolve_tenant)
        app.teardown_request(self.cleanup_tenant)

    def resolve_tenant(self):
        # Skip for health check and tenant management endpoints
        if request.path.startswith('/api/health') or request.path == '/api/tenants':
            return

        slug = request.headers.get('X-Tenant-Slug')
        if not slug:
            return {'error': {'code': 'MISSING_TENANT', 'message': 'X-Tenant-Slug header required'}}, 400

        tenant = db.session.query(Tenant).filter_by(slug=slug, status='active').first()
        if not tenant:
            return {'error': {'code': 'INVALID_TENANT', 'message': 'Tenant not found'}}, 404

        g.tenant = tenant
        g.tenant_session = tenant_manager.get_session(slug)

    def cleanup_tenant(self, exception=None):
        session = getattr(g, 'tenant_session', None)
        if session:
            session.remove()


def require_tenant(f):
    """Decorator to ensure tenant context exists."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, 'tenant'):
            return {'error': {'code': 'NO_TENANT_CONTEXT', 'message': 'Tenant context required'}}, 400
        return f(*args, **kwargs)
    return decorated
```

### 9.4 Service Layer Pattern

```python
# app/services/server_service.py
from typing import List, Optional
from uuid import UUID

from app.models.tenant import Server
from app.repositories.server_repository import ServerRepository
from app.connectors.sqlserver import SQLServerConnector
from app.core.encryption import encrypt_password, decrypt_password


class ServerService:
    """Business logic for server management."""

    def __init__(self, session):
        self.repo = ServerRepository(session)
        self.connector = SQLServerConnector()

    def get_all(self) -> List[Server]:
        return self.repo.get_all()

    def get_by_id(self, server_id: UUID) -> Optional[Server]:
        return self.repo.get_by_id(server_id)

    def create(self, data: dict) -> Server:
        # Encrypt password before storage
        if data.get('password'):
            data['encrypted_password'] = encrypt_password(data.pop('password'))

        server = Server(**data)
        return self.repo.create(server)

    def update(self, server_id: UUID, data: dict) -> Optional[Server]:
        if data.get('password'):
            data['encrypted_password'] = encrypt_password(data.pop('password'))

        return self.repo.update(server_id, data)

    def delete(self, server_id: UUID) -> bool:
        return self.repo.delete(server_id)

    def test_connection(self, server_id: UUID) -> dict:
        server = self.get_by_id(server_id)
        if not server:
            return {'success': False, 'message': 'Server not found'}

        password = None
        if server.encrypted_password:
            password = decrypt_password(server.encrypted_password)

        result = self.connector.test_connection(
            hostname=server.hostname,
            port=server.port,
            instance=server.instance_name,
            auth_type=server.auth_type,
            username=server.username,
            password=password
        )

        # Update server status based on result
        new_status = 'online' if result['success'] else 'offline'
        self.repo.update(server_id, {'status': new_status, 'last_checked': datetime.utcnow()})

        return result
```

### 9.5 Repository Pattern

```python
# app/repositories/base.py
from typing import TypeVar, Generic, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""

    def __init__(self, session: Session, model_class: type):
        self.session = session
        self.model_class = model_class

    def get_all(self) -> List[T]:
        return self.session.query(self.model_class).all()

    def get_by_id(self, id: UUID) -> Optional[T]:
        return self.session.query(self.model_class).filter_by(id=id).first()

    def create(self, entity: T) -> T:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def update(self, id: UUID, data: dict) -> Optional[T]:
        entity = self.get_by_id(id)
        if entity:
            for key, value in data.items():
                setattr(entity, key, value)
            self.session.commit()
            self.session.refresh(entity)
        return entity

    def delete(self, id: UUID) -> bool:
        entity = self.get_by_id(id)
        if entity:
            self.session.delete(entity)
            self.session.commit()
            return True
        return False
```

### 9.6 Route Handlers

```python
# app/api/servers.py
from flask import Blueprint, request, g
from app.services.server_service import ServerService
from app.middleware.tenant import require_tenant

bp = Blueprint('servers', __name__, url_prefix='/api/servers')


@bp.route('', methods=['GET'])
@require_tenant
def list_servers():
    service = ServerService(g.tenant_session)
    servers = service.get_all()
    return [s.to_dict() for s in servers]


@bp.route('', methods=['POST'])
@require_tenant
def create_server():
    data = request.get_json()
    service = ServerService(g.tenant_session)
    server = service.create(data)
    return server.to_dict(), 201


@bp.route('/<uuid:server_id>', methods=['GET'])
@require_tenant
def get_server(server_id):
    service = ServerService(g.tenant_session)
    server = service.get_by_id(server_id)
    if not server:
        return {'error': {'code': 'NOT_FOUND', 'message': 'Server not found'}}, 404
    return server.to_dict()


@bp.route('/<uuid:server_id>/test-connection', methods=['POST'])
@require_tenant
def test_connection(server_id):
    service = ServerService(g.tenant_session)
    result = service.test_connection(server_id)
    return result
```

### 9.7 SQL Server Connector

```python
# app/connectors/sqlserver.py
import pyodbc
from typing import Optional, Dict, Any, List
from flask import current_app


class SQLServerConnector:
    """Handles connections to target SQL Server instances."""

    def _get_connection_string(
        self,
        hostname: str,
        port: int,
        instance: Optional[str],
        auth_type: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: str = 'master'
    ) -> str:
        driver = current_app.config['SQLSERVER_DRIVER']
        server = f"{hostname},{port}"
        if instance:
            server = f"{hostname}\\{instance}"

        conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};"

        if auth_type == 'windows':
            conn_str += "Trusted_Connection=yes;"
        else:
            conn_str += f"UID={username};PWD={password};"

        conn_str += "TrustServerCertificate=yes;"
        return conn_str

    def test_connection(self, **kwargs) -> Dict[str, Any]:
        try:
            conn_str = self._get_connection_string(**kwargs)
            timeout = current_app.config['SQLSERVER_TIMEOUT']

            conn = pyodbc.connect(conn_str, timeout=timeout)
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION")
            version = cursor.fetchone()[0]
            conn.close()

            return {'success': True, 'message': 'Connection successful', 'version': version}
        except pyodbc.Error as e:
            return {'success': False, 'message': str(e)}

    def collect_metrics(self, **kwargs) -> Dict[str, Any]:
        conn_str = self._get_connection_string(**kwargs)
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        metrics = {}

        # CPU Usage
        cursor.execute("""
            SELECT TOP 1
                SQLProcessUtilization as cpu_percent
            FROM sys.dm_os_ring_buffers
            WHERE ring_buffer_type = N'RING_BUFFER_SCHEDULER_MONITOR'
            ORDER BY timestamp DESC
        """)
        row = cursor.fetchone()
        metrics['cpu_percent'] = row[0] if row else 0

        # Memory
        cursor.execute("""
            SELECT
                total_physical_memory_kb / 1024 as total_mb,
                available_physical_memory_kb / 1024 as available_mb
            FROM sys.dm_os_sys_memory
        """)
        row = cursor.fetchone()
        if row:
            metrics['memory_total_mb'] = row[0]
            metrics['memory_used_mb'] = row[0] - row[1]

        # Connections
        cursor.execute("SELECT COUNT(*) FROM sys.dm_exec_sessions WHERE is_user_process = 1")
        metrics['active_connections'] = cursor.fetchone()[0]

        # Blocked processes
        cursor.execute("SELECT COUNT(*) FROM sys.dm_exec_requests WHERE blocking_session_id > 0")
        metrics['blocked_processes'] = cursor.fetchone()[0]

        conn.close()
        return metrics
```

### 9.8 Background Worker

```python
# workers/metric_collector.py
import time
import logging
from datetime import datetime

from app import create_app
from app.extensions import db
from app.models.system import Tenant
from app.core.tenant_manager import tenant_manager
from app.services.metric_service import MetricService
from app.services.server_service import ServerService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricCollector:
    """Background worker that collects metrics from all servers."""

    def __init__(self):
        self.app = create_app()
        self.interval = self.app.config['METRIC_COLLECTION_INTERVAL']

    def run(self):
        logger.info("Metric Collector started")
        while True:
            try:
                self.collect_all_metrics()
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
            time.sleep(self.interval)

    def collect_all_metrics(self):
        with self.app.app_context():
            # Get all active tenants
            tenants = db.session.query(Tenant).filter_by(status='active').all()

            for tenant in tenants:
                try:
                    self.collect_tenant_metrics(tenant)
                except Exception as e:
                    logger.error(f"Error collecting metrics for tenant {tenant.slug}: {e}")

    def collect_tenant_metrics(self, tenant):
        session = tenant_manager.get_session(tenant.slug)
        try:
            server_service = ServerService(session)
            metric_service = MetricService(session)

            servers = server_service.get_all()
            for server in servers:
                try:
                    metrics = server_service.connector.collect_metrics(
                        hostname=server.hostname,
                        port=server.port,
                        # ... other connection params
                    )
                    metric_service.record_snapshot(server.id, metrics)
                    logger.info(f"Collected metrics for {server.name}")
                except Exception as e:
                    logger.warning(f"Failed to collect metrics for {server.name}: {e}")
        finally:
            session.remove()


if __name__ == '__main__':
    collector = MetricCollector()
    collector.run()
```

---

## 10. Project Structure & Deployment

### 10.1 Unified Project Structure

```
DbToolsApp/
├── docs/                           # Documentation
│   ├── prd.md                      # Product Requirements
│   └── architecture.md             # This architecture document
├── backend/                        # Flask Backend Application
│   ├── app/
│   │   ├── __init__.py            # App factory
│   │   ├── config.py              # Configuration management
│   │   ├── extensions.py          # Flask extensions (SQLAlchemy, etc.)
│   │   ├── api/                   # API Blueprints
│   │   │   ├── __init__.py
│   │   │   ├── tenants.py         # Tenant management endpoints
│   │   │   ├── servers.py         # Server management endpoints
│   │   │   ├── groups.py          # Group management endpoints
│   │   │   ├── policies.py        # Policy management endpoints
│   │   │   ├── jobs.py            # Job management endpoints
│   │   │   ├── metrics.py         # Metrics endpoints
│   │   │   └── alerts.py          # Alert endpoints
│   │   ├── models/                # SQLAlchemy Models
│   │   │   ├── __init__.py
│   │   │   ├── system.py          # System DB models (Tenant)
│   │   │   └── tenant.py          # Tenant DB models
│   │   ├── services/              # Business Logic Layer
│   │   │   ├── __init__.py
│   │   │   ├── tenant_service.py
│   │   │   ├── server_service.py
│   │   │   ├── group_service.py
│   │   │   ├── policy_service.py
│   │   │   ├── job_service.py
│   │   │   ├── metric_service.py
│   │   │   └── alert_service.py
│   │   ├── repositories/          # Data Access Layer
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # Base repository
│   │   │   └── ...                # Entity-specific repos
│   │   ├── connectors/            # External Connections
│   │   │   ├── __init__.py
│   │   │   └── sqlserver.py       # SQL Server connector
│   │   ├── middleware/            # Request Middleware
│   │   │   ├── __init__.py
│   │   │   └── tenant.py          # Tenant resolution
│   │   ├── core/                  # Core Utilities
│   │   │   ├── __init__.py
│   │   │   ├── encryption.py      # Fernet encryption
│   │   │   ├── exceptions.py      # Custom exceptions
│   │   │   └── tenant_manager.py  # Multi-DB management
│   │   └── utils/                 # Helper Functions
│   │       ├── __init__.py
│   │       └── validators.py
│   ├── workers/                   # Background Workers
│   │   ├── __init__.py
│   │   ├── metric_collector.py    # Metric collection worker
│   │   ├── job_scheduler.py       # APScheduler worker
│   │   └── alert_processor.py     # Alert processing worker
│   ├── migrations/                # Alembic Migrations
│   │   ├── versions/
│   │   ├── env.py
│   │   └── alembic.ini
│   ├── tests/                     # Backend Tests
│   │   ├── unit/
│   │   ├── integration/
│   │   └── conftest.py
│   ├── requirements.txt           # Python dependencies
│   ├── requirements-dev.txt       # Dev dependencies
│   └── run.py                     # Application entry point
├── frontend/                       # React Frontend Application
│   ├── src/
│   │   ├── main.tsx               # React entry point
│   │   ├── App.tsx                # Root component
│   │   ├── components/            # Reusable UI Components
│   │   │   ├── ui/                # shadcn/ui components
│   │   │   ├── layout/            # Layout components
│   │   │   ├── dashboard/         # Dashboard widgets
│   │   │   ├── servers/           # Server components
│   │   │   ├── groups/            # Group components
│   │   │   ├── policies/          # Policy components
│   │   │   ├── jobs/              # Job scheduler components
│   │   │   └── common/            # Shared components
│   │   ├── pages/                 # Page Components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Servers.tsx
│   │   │   ├── Groups.tsx
│   │   │   ├── Policies.tsx
│   │   │   ├── Jobs.tsx
│   │   │   └── Alerts.tsx
│   │   ├── hooks/                 # Custom React Hooks
│   │   │   ├── useServers.ts
│   │   │   ├── useGroups.ts
│   │   │   ├── usePolicies.ts
│   │   │   └── useJobs.ts
│   │   ├── services/              # API Client Services
│   │   │   ├── api.ts             # Axios instance
│   │   │   ├── serverService.ts
│   │   │   ├── groupService.ts
│   │   │   └── ...
│   │   ├── stores/                # Zustand State Stores
│   │   │   ├── tenantStore.ts
│   │   │   ├── serverStore.ts
│   │   │   └── uiStore.ts
│   │   ├── types/                 # TypeScript Types
│   │   │   ├── server.ts
│   │   │   ├── group.ts
│   │   │   ├── policy.ts
│   │   │   └── api.ts
│   │   ├── lib/                   # Utilities
│   │   │   ├── utils.ts
│   │   │   └── constants.ts
│   │   └── styles/                # Global Styles
│   │       └── globals.css
│   ├── public/                    # Static Assets
│   ├── tests/                     # Frontend Tests
│   │   ├── components/
│   │   └── setup.ts
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── package.json
├── scripts/                        # Development Scripts
│   ├── setup.sh                   # Initial setup script
│   ├── create_tenant.py           # Tenant provisioning
│   └── seed_data.py               # Development data seeding
├── .env.example                    # Environment template
├── .gitignore
└── README.md
```

### 10.2 Development Workflow

#### Prerequisites

```bash
# Required software
Python 3.11+
Node.js 20 LTS
PostgreSQL 16
SQL Server ODBC Driver 18

# Windows: Install SQL Server ODBC Driver
# Download from Microsoft and install

# Verify installations
python --version
node --version
psql --version
```

#### Initial Setup

```bash
# Clone repository
cd DbToolsApp

# Backend setup
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Create PostgreSQL databases
psql -U postgres
CREATE DATABASE dbtools_system;
\q

# Run migrations
flask db upgrade

# Frontend setup
cd ../frontend
npm install
```

#### Development Commands

```bash
# Start backend (from backend/)
venv\Scripts\activate
flask run --debug --port 5000

# Start workers (separate terminals)
python -m workers.metric_collector
python -m workers.job_scheduler

# Start frontend (from frontend/)
npm run dev

# Run all tests
# Backend
pytest

# Frontend
npm test

# Lint and format
# Backend
black .
flake8 .

# Frontend
npm run lint
npm run format
```

### 10.3 Environment Configuration

#### Backend (.env)

```bash
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production

# System Database (Tenant Registry)
DATABASE_URL=postgresql://postgres:1234@localhost:5432/dbtools_system

# Tenant Database Template
TENANT_DB_HOST=localhost
TENANT_DB_PORT=5432
TENANT_DB_USER=postgres
TENANT_DB_PASSWORD=1234

# Encryption (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
ENCRYPTION_KEY=your-fernet-key-here

# SQL Server Connection Defaults
SQLSERVER_DRIVER=ODBC Driver 18 for SQL Server
SQLSERVER_TIMEOUT=30

# Worker Configuration
METRIC_COLLECTION_INTERVAL=300
JOB_SCHEDULER_CHECK_INTERVAL=60
```

#### Frontend (.env.local)

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:5000/api

# Feature Flags
VITE_ENABLE_MOCK_DATA=false
```

### 10.4 Deployment Architecture

#### MVP Deployment Strategy

**Approach:** Simple deployment without Docker for MVP, focusing on local Windows Server deployment.

```
┌─────────────────────────────────────────────────────────────┐
│                    Windows Server Host                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────────────────┐    │
│  │   Nginx/IIS     │    │      PostgreSQL 16          │    │
│  │  Reverse Proxy  │    │  ┌─────────────────────┐    │    │
│  │                 │    │  │  dbtools_system     │    │    │
│  │  :80 → :5000    │    │  │  dbtools_tenant_*   │    │    │
│  │  :80 → :3000    │    │  └─────────────────────┘    │    │
│  └─────────────────┘    └─────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Application Services                    │   │
│  │  ┌─────────┐  ┌──────────┐  ┌──────────────────┐   │   │
│  │  │ Flask   │  │ Metric   │  │ Job Scheduler    │   │   │
│  │  │ API     │  │ Collector│  │ (APScheduler)    │   │   │
│  │  │ :5000   │  │ Worker   │  │ Worker           │   │   │
│  │  └─────────┘  └──────────┘  └──────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Static Frontend                         │   │
│  │  Built React app served via Nginx/IIS                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
          │
          │ pyodbc (ODBC Driver 18)
          ▼
┌─────────────────────────────────────────────────────────────┐
│               Target SQL Server Instances                    │
│     (Managed servers added by users in DbTools)             │
└─────────────────────────────────────────────────────────────┘
```

#### Deployment Process

```bash
# 1. Build frontend
cd frontend
npm run build
# Output: frontend/dist/

# 2. Copy build to static folder
xcopy /E /I frontend\dist backend\static

# 3. Production backend setup
cd backend
pip install -r requirements.txt
pip install waitress  # Production WSGI server

# 4. Run with Waitress (production)
waitress-serve --port=5000 run:app

# 5. Start workers as Windows Services (or scheduled tasks)
# Use NSSM or similar to run as services:
# - metric_collector.py
# - job_scheduler.py
```

#### Environments

| Environment | Frontend URL | Backend URL | Purpose |
|-------------|--------------|-------------|---------|
| Development | http://localhost:5173 | http://localhost:5000/api | Local development |
| Production | http://dbtools.internal | http://dbtools.internal/api | Live environment |

---

## 11. Security and Performance

### 11.1 Security Requirements

**Credential Security:**
- SQL Server passwords encrypted with Fernet (symmetric encryption)
- Encryption key stored in environment variable, not in code
- Passwords never logged or returned in API responses

**Input Validation:**
- All API inputs validated with marshmallow schemas
- SQL queries use parameterized statements (SQLAlchemy ORM)
- Hostname/IP validation before SQL Server connection attempts

**CORS Policy:**
```python
CORS(app, origins=['http://localhost:5173', 'http://dbtools.internal'])
```

**Future (Post-MVP):**
- Authentication with JWT or session-based auth
- Role-based access control
- Audit logging

### 11.2 Performance Optimization

**Backend Performance:**
- Connection pooling for PostgreSQL (SQLAlchemy)
- Lazy loading for tenant database connections
- Background workers for heavy operations (metrics, jobs)
- Metric data retention policy (configurable days)

**Frontend Performance:**
- Code splitting with React.lazy()
- TanStack Query caching (30s stale time)
- Optimistic updates for UI responsiveness
- Virtualized lists for large data sets (future)

**Database Performance:**
- Indexes on frequently queried columns (status, timestamps)
- JSONB for flexible configuration storage
- Consider partitioning metric_snapshots by time (high-volume)

---

## 12. Error Handling Strategy

### 12.1 Error Response Format

```typescript
interface ApiError {
  error: {
    code: string;           // Machine-readable code
    message: string;        // Human-readable message
    details?: {
      field?: string;
      reason?: string;
    }[];
    timestamp: string;
    requestId: string;
  }
}
```

### 12.2 Backend Error Handling

```python
# app/core/exceptions.py
class AppException(Exception):
    status_code = 500
    code = 'INTERNAL_ERROR'

    def __init__(self, message: str, details: list = None):
        self.message = message
        self.details = details
        super().__init__(message)

class ValidationError(AppException):
    status_code = 400
    code = 'VALIDATION_ERROR'

class NotFoundError(AppException):
    status_code = 404
    code = 'NOT_FOUND'

class ConnectionError(AppException):
    status_code = 502
    code = 'CONNECTION_ERROR'


# Error handler registration
@app.errorhandler(AppException)
def handle_app_exception(error):
    return {
        'error': {
            'code': error.code,
            'message': error.message,
            'details': error.details,
            'timestamp': datetime.utcnow().isoformat(),
            'requestId': g.get('request_id', 'unknown')
        }
    }, error.status_code
```

### 12.3 Frontend Error Handling

```typescript
// Global error handler for API calls
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const apiError = error.response?.data?.error;

    if (apiError) {
      toast.error(apiError.message);
    } else if (error.code === 'NETWORK_ERROR') {
      toast.error('Unable to connect to server');
    } else {
      toast.error('An unexpected error occurred');
    }

    return Promise.reject(error);
  }
);
```

---

## 13. Coding Standards

### 13.1 Critical Fullstack Rules

- **API Calls:** Never make direct HTTP calls - use the service layer
- **Environment Variables:** Access only through config objects
- **Error Handling:** All API routes must use the standard error handler
- **State Updates:** Never mutate state directly - use proper patterns
- **Tenant Context:** Always check for tenant context in tenant-scoped endpoints
- **Password Handling:** Never log, return, or store passwords in plain text

### 13.2 Naming Conventions

| Element | Frontend | Backend | Example |
|---------|----------|---------|---------|
| Components | PascalCase | - | `ServerCard.tsx` |
| Hooks | camelCase with 'use' | - | `useServers.ts` |
| API Routes | - | kebab-case | `/api/server-groups` |
| Database Tables | - | snake_case | `server_groups` |
| Python Functions | - | snake_case | `get_all_servers()` |
| TypeScript Functions | camelCase | - | `getServers()` |

---

## 14. Testing Strategy

### 14.1 Testing Pyramid

```
        E2E Tests (Playwright)
       /                      \
      Integration Tests (API)
     /                        \
Frontend Unit Tests    Backend Unit Tests
   (Vitest)               (pytest)
```

### 14.2 Backend Tests

```python
# tests/unit/test_server_service.py
import pytest
from unittest.mock import Mock, patch
from app.services.server_service import ServerService

class TestServerService:
    def test_create_server_encrypts_password(self):
        mock_session = Mock()
        service = ServerService(mock_session)

        with patch('app.services.server_service.encrypt_password') as mock_encrypt:
            mock_encrypt.return_value = 'encrypted'

            service.create({
                'name': 'Test Server',
                'hostname': 'localhost',
                'password': 'secret'
            })

            mock_encrypt.assert_called_once_with('secret')
```

### 14.3 Frontend Tests

```typescript
// tests/components/ServerCard.test.tsx
import { render, screen } from '@testing-library/react';
import { ServerCard } from '@/components/servers/ServerCard';

describe('ServerCard', () => {
  it('displays server name and status', () => {
    const server = {
      id: '1',
      name: 'Test Server',
      hostname: 'localhost',
      port: 1433,
      status: 'online',
    };

    render(<ServerCard server={server} />);

    expect(screen.getByText('Test Server')).toBeInTheDocument();
    expect(screen.getByText('online')).toBeInTheDocument();
  });
});
```

---

## Appendix: Checklist Results

_(To be populated after running architect-checklist)_
