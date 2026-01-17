# DbTools Product Requirements Document (PRD)

## Document Info

| Field | Value |
|-------|-------|
| **Product** | DbTools |
| **Version** | 0.1 |
| **Status** | Draft |
| **Last Updated** | 2026-01-17 |
| **Author** | PM (John) |

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-01-17 | 0.1 | Initial PRD draft | PM (John) |

---

## Goals

- **Unified DBA Platform**: Provide a single web-based platform that consolidates functionality currently spread across multiple tools (SSMS, RedGate, SentryOne, SolarWinds DPA)
- **Server Group Management**: Enable DBAs to onboard SQL Server instances, organize them with custom labels/groups, and manage them collectively
- **Policy-Based Automation**: Allow one-click deployment of configurable policies (backup, maintenance, alerts) across server groups
- **Lightweight Data Collection**: Establish a reliable, low-overhead monitoring infrastructure that collects metrics from target SQL instances without impacting production performance
- **Scalable Architecture**: Build on PostgreSQL backend with decoupled application server, enabling horizontal scaling and advanced analytics in future phases
- **Serve All DBA Scales**: Support both solo DBAs managing few instances and enterprise teams managing hundreds of servers
- **Multi-Tenant Platform**: Support multiple customers with completely isolated databases, enabling SaaS delivery model

---

## Background Context

Database Administrators today face a fragmented tooling landscape. Managing SQL Server environments typically requires juggling multiple tools: SSMS for ad-hoc queries, RedGate for deployments, SentryOne or SolarWinds DPA for performance monitoring, and custom PowerShell scripts for automation. This fragmentation creates operational overhead, inconsistent practices across environments, and difficulty enforcing organizational policies at scale.

DbTools addresses this by providing a modern, unified web platform purpose-built for SQL Server management. The MVP focuses on establishing rock-solid fundamentals: reliable server onboarding, flexible grouping/labeling, and lightweight data collection infrastructure. This foundation-first approach ensures that future advanced features (automated pipelines, predictive analytics, AI-driven troubleshooting) are built on trustworthy data. The architecture intentionally separates the application server from the PostgreSQL data store, enabling independent scaling of collection, storage, and analysis tiers.

The platform is designed as a multi-tenant SaaS solution, with each customer receiving their own isolated PostgreSQL database. This database-per-tenant architecture ensures complete data isolation, simplifies compliance, and enables seamless migration to dedicated infrastructure for premium customers.

---

## Requirements

### Functional Requirements

| ID | Requirement |
|----|-------------|
| **FR1** | The system shall allow operators to create and manage tenants, each with isolated databases |
| **FR2** | The system shall allow users to onboard SQL Server instances by providing connection details (host, port, authentication method, credentials) |
| **FR3** | The system shall validate connectivity and permissions during server onboarding and report any issues |
| **FR4** | The system shall automatically deploy required monitoring objects (stored procedures, tables, jobs) to target SQL Server instances during onboarding |
| **FR5** | The system shall allow users to create, edit, and delete Server Groups with custom names and descriptions |
| **FR6** | The system shall allow users to assign labels/tags to individual servers for flexible categorization |
| **FR7** | The system shall allow users to assign servers to one or more Server Groups |
| **FR8** | The system shall provide a Policy management interface to create, configure, and version policies (e.g., Backup Policy, Maintenance Policy) |
| **FR9** | The system shall allow users to deploy policies to Server Groups with one-click application |
| **FR10** | The system shall collect performance and health metrics from target SQL instances on configurable intervals |
| **FR11** | The system shall store all collected metrics in the PostgreSQL database with appropriate retention policies |
| **FR12** | The system shall provide a dashboard displaying server health status, group summaries, and key metrics |
| **FR13** | The system shall provide alerting capabilities when collected metrics exceed defined thresholds |
| **FR14** | The system shall display real-time server status (online/offline/degraded) for all monitored instances |
| **FR15** | The system shall provide an activity log/audit trail of all administrative actions (server adds, policy deployments, configuration changes) |
| **FR16** | The system shall provide a Job Scheduler module for scheduling and managing recurring tasks (data collection, policy execution, maintenance operations) |
| **FR17** | The Job Scheduler shall support flexible scheduling options: cron expressions, intervals, one-time execution, and event-triggered jobs |
| **FR18** | The Job Scheduler shall provide a visual UI for creating, editing, pausing, and monitoring scheduled jobs |
| **FR19** | The Job Scheduler shall display job execution history with status, duration, and error details |
| **FR20** | The Job Scheduler shall support job dependencies (Job B runs after Job A completes successfully) |
| **FR21** | The Job Scheduler shall allow job prioritization and concurrency limits to prevent resource contention |
| **FR22** | The Job Scheduler shall provide retry policies with configurable attempts and backoff strategies |
| **FR23** | The system shall support multiple customer tenants, each with completely isolated data |
| **FR24** | Each tenant shall have their own set of servers, groups, policies, jobs, and users |
| **FR25** | The system shall prevent any cross-tenant data access at the application and database level |
| **FR26** | The system shall support migrating a tenant's complete data to a dedicated database instance |
| **FR27** | Super-admin users shall be able to manage tenants (create, suspend, migrate, delete) |
| **FR28** | Each tenant shall have their own admin who can manage users within their tenant |
| **FR29** | The system shall automatically provision a new database when a tenant is created |
| **FR30** | The system shall run database migrations on all tenant databases during upgrades |
| **FR31** | The system shall support tenant database backup and restore operations |
| **FR32** | Super-admin dashboard shall display tenant list with database size, server count, and status |

### Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| **NFR1** | Data collection agents shall consume less than 1% CPU and 50MB memory on target SQL Server instances under normal operation |
| **NFR2** | The application server shall support horizontal scaling to handle 500+ monitored SQL instances per node |
| **NFR3** | The web UI shall load dashboard views within 3 seconds for up to 100 servers displayed |
| **NFR4** | The system shall use secure connections (TLS/SSL) for all communication between application server and target SQL instances |
| **NFR5** | Credentials for target SQL instances shall be encrypted at rest using industry-standard encryption (AES-256) |
| **NFR6** | The system shall support SQL Server versions 2016, 2017, 2019, and 2022 |
| **NFR7** | The system shall be deployable on Windows Server or Linux environments |
| **NFR8** | The PostgreSQL database shall support configurable data retention (default: 30 days metrics, 1 year audit logs) |
| **NFR9** | The system shall provide 99.5% uptime for the monitoring infrastructure (collection not dependent on UI availability) |
| **NFR10** | The web application shall be responsive and functional on modern browsers (Chrome, Edge, Firefox - latest 2 versions) |
| **NFR11** | Tenant data isolation shall be enforced at the database level, not just application level |
| **NFR12** | Tenant migration shall be achievable with zero data loss and minimal downtime (<1 hour) |

---

## User Interface Design Goals

### Overall UX Vision

DbTools should feel like a **modern DevOps control center** - clean, professional, and data-dense without feeling cluttered. The interface should prioritize **at-a-glance status awareness** (which servers are healthy, which need attention) while providing **progressive disclosure** for deeper investigation.

The aesthetic should convey **trust and reliability** - this is enterprise infrastructure tooling, not a consumer app. Think: Datadog, Grafana, or Azure Portal rather than flashy SaaS marketing sites.

### Key Interaction Paradigms

| Paradigm | Description |
|----------|-------------|
| **Dashboard-First** | Users land on a health overview; drill down into specifics |
| **Bulk Operations** | Select multiple servers/groups, apply actions (deploy policy, run job) |
| **Search & Filter** | Quickly find servers by name, tag, group, or status |
| **Inline Editing** | Edit labels, group assignments, and quick settings without page navigation |
| **Contextual Actions** | Right-click or action menus on server rows for common operations |
| **Real-Time Updates** | Live status indicators, auto-refreshing metrics (polling) |
| **Wizard Flows** | Guided multi-step processes for onboarding servers and creating policies |

### Core Screens and Views

| Screen | Purpose |
|--------|---------|
| **Main Dashboard** | Overview: server count by status, group summaries, recent alerts, system health |
| **Server List** | Filterable/searchable table of all monitored SQL instances with status indicators |
| **Server Detail** | Individual server view: metrics, policies applied, jobs, connection info, activity |
| **Server Groups** | Manage groups: create, edit, assign servers, view group-level metrics |
| **Policies** | Policy library: create, version, deploy to groups, view deployment history |
| **Job Scheduler** | Visual job management: calendar/timeline view, job list, execution history, create/edit wizard |
| **Alerts** | Active alerts, alert history, alert rules configuration |
| **Settings** | System configuration, data retention |
| **Activity Log** | Audit trail of all administrative actions |
| **Tenant Management** | (Admin) Create/manage tenants |

### Accessibility

**WCAG AA** - Standard accessibility compliance for enterprise software:
- Keyboard navigation for all functions
- Screen reader compatible
- Sufficient color contrast
- Focus indicators

### Branding

| Element | Suggestion |
|---------|------------|
| **Color Palette** | Professional blues/grays with status colors (green=healthy, yellow=warning, red=critical) |
| **Typography** | Clean sans-serif (Inter, Roboto, or system fonts) |
| **Icons** | Consistent icon library (Lucide, Heroicons, or similar) |
| **Tone** | Technical but approachable - DBAs are power users |

### Target Platforms

**Web Responsive** - Primary focus on desktop (1280px+) where DBAs do their work, with functional tablet support for on-call scenarios. Mobile is low priority for MVP.

---

## Technical Assumptions

### Repository Structure: Monorepo

```
DbToolsApp/
├── backend/           # Python Flask API
├── frontend/          # React application
├── db/                # Database migrations, seeds
├── docs/              # Documentation (PRD, Architecture, etc.)
├── scripts/           # Utility scripts, deployment
└── tests/             # Shared test utilities
```

### Multi-Tenancy Architecture: Database-per-Tenant

```
PostgreSQL Server
├── dbtools_system          # Central: tenant registry, super-admin, system config
├── dbtools_tenant_acme     # ACME Corp's complete isolated database
├── dbtools_tenant_contoso  # Contoso's complete isolated database
└── dbtools_tenant_fabrikam # Fabrikam's complete isolated database
```

| Component | Behavior |
|-----------|----------|
| **System DB** | Stores tenant list, super-admin users, subscription/license info |
| **Tenant DBs** | Identical schema, completely isolated data per customer |
| **Auth Flow** | Select tenant → connect to tenant DB (no auth in MVP) |
| **Connection** | Dynamic connection switching based on X-Tenant-Slug header |
| **Migration** | `pg_dump dbtools_tenant_xyz` → restore to dedicated server |

### Service Architecture: Modular Monolith

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React 18 + TypeScript + Vite | SPA with modern build tooling |
| **Backend API** | Python Flask 3.x | REST API, business logic |
| **Job Scheduler** | APScheduler | Task scheduling & execution |
| **Data Collector** | Python workers | Lightweight SQL Server metric collection |
| **Database** | PostgreSQL 15+ | Primary data store |

### Tech Stack Details

| Component | Choice | Notes |
|-----------|--------|-------|
| **Python Version** | 3.11+ | Latest stable with performance improvements |
| **Flask** | 3.x | With Flask-SQLAlchemy, Flask-Migrate |
| **React** | 18.x | With TypeScript, React Router, TanStack Query |
| **UI Library** | Shadcn/ui | Component library for consistent UX |
| **State Management** | React Context + TanStack Query | Server state via Query, minimal client state |
| **PostgreSQL** | 15+ | localhost:5432 |
| **System Database** | dbtools_system | Tenant registry |
| **Tenant Database Naming** | dbtools_tenant_{slug} | Per-tenant isolation |
| **SQL Server Connectivity** | pyodbc / pymssql | Connect to target SQL instances |
| **Job Scheduler** | APScheduler | Flask-native, sufficient for MVP scale |
| **API Format** | REST + JSON | OpenAPI/Swagger documentation |

### Development Database

```yaml
Host: localhost
Port: 5432
Database: DbToolsApp (legacy) / dbtools_system (new)
User: postgres
Password: 1234
```

### Testing Requirements

| Level | Approach | Tools |
|-------|----------|-------|
| **Unit Tests** | Required for business logic | pytest (backend), Jest (frontend) |
| **Integration Tests** | API endpoint testing | pytest + test database |
| **E2E Tests** | Critical user flows only (MVP) | Playwright or Cypress |
| **Manual Testing** | UI/UX validation | Checklist-based |

**Coverage Target**: 70% backend, 50% frontend for MVP

### Additional Technical Assumptions

- **Authentication**: Deferred to post-MVP (open access with tenant selection for now)
- **SQL Server Auth**: Support both SQL Authentication and Windows Authentication
- **Secrets Management**: Environment variables for MVP
- **Logging**: Structured JSON logging (Python `structlog` or similar)
- **Containerization**: Deferred to post-MVP
- **CI/CD**: GitHub Actions for automated testing and builds
- **Data Collection Interval**: Configurable, default 60 seconds for metrics
- **Timezone Handling**: All timestamps stored in UTC, displayed in user's local timezone

### Deferred to Post-MVP

- Docker/Docker Compose
- JWT Authentication & RBAC
- User management
- SSO/LDAP integration
- Error tracking (Sentry)

---

## Epic List

| Epic | Title | Goal |
|------|-------|------|
| **Epic 1** | Foundation & Multi-Tenancy | Project setup, database-per-tenant infrastructure, tenant provisioning, React shell |
| **Epic 2** | Server Management & Groups | Tenant-scoped server onboarding, groups, labels, monitoring object deployment |
| **Epic 3** | Data Collection & Dashboard | Lightweight collectors, tenant-isolated metrics storage, health dashboard |
| **Epic 4** | Policies, Scheduler & Alerts | Policy management, visual job scheduler, deployment automation, alerting, audit log |

---

## Epic 1: Foundation & Multi-Tenancy

### Epic Goal

Establish project infrastructure with Flask backend, React frontend, and PostgreSQL connectivity. Implement database-per-tenant architecture with provisioning. Users select their tenant from a dropdown, and all data is scoped accordingly. No authentication in MVP - security added in future phase.

---

### Story 1.1: Project Setup & Repository Structure

**As a** developer,
**I want** a properly structured monorepo with Flask backend and React frontend,
**so that** I have a solid foundation to build features upon.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Repository follows monorepo structure: `/backend`, `/frontend`, `/docs`, `/scripts` |
| 2 | Backend: Flask 3.x project with virtual environment and requirements.txt |
| 3 | Backend: Flask configuration supports dev/prod environments via environment variables |
| 4 | Frontend: React 18 + TypeScript + Vite project initialized |
| 5 | Frontend: ESLint + Prettier configured for consistent code style |
| 6 | `/api/health` endpoint returns `{"status": "healthy"}` with 200 OK |
| 7 | Setup script (`scripts/setup.sh` or `.ps1`) to initialize local environment |
| 8 | README.md with manual setup instructions |
| 9 | `.env.example` file documenting required environment variables |

---

### Story 1.2: System Database & Tenant Data Model

**As a** developer,
**I want** a system database that tracks all tenants,
**so that** the platform can manage multiple isolated customers.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | `dbtools_system` database created with Flask-Migrate managing schema |
| 2 | `tenants` table: id, slug (unique), name, status (active/suspended), created_at, updated_at |
| 3 | Tenant slug must be alphanumeric with hyphens, 3-50 characters |
| 4 | Database connection string configurable via environment variable |
| 5 | Initial migration creates all system tables |
| 6 | Seed script creates a default demo tenant for development |
| 7 | SQLAlchemy models defined with proper constraints |

---

### Story 1.3: Tenant Provisioning API

**As an** operator,
**I want** to create new tenants via API,
**so that** each customer gets their own isolated database automatically.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | `POST /api/tenants` creates tenant record in system database |
| 2 | API automatically creates new PostgreSQL database `dbtools_tenant_{slug}` |
| 3 | API runs all tenant migrations on newly created database |
| 4 | Tenant database includes base tables: settings, activity_log |
| 5 | Returns 201 with tenant details on success |
| 6 | Returns 409 if slug already exists |
| 7 | Returns 400 with validation errors for invalid input |
| 8 | `GET /api/tenants` lists all tenants with status |
| 9 | `DELETE /api/tenants/{slug}` marks tenant as deleted (soft delete) |
| 10 | Provisioning is transactional - rollback DB creation on failure |

---

### Story 1.4: Tenant Database Schema (Template)

**As a** developer,
**I want** a standardized schema for tenant databases,
**so that** all tenants have consistent table structures.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Tenant migration template includes: settings, activity_log tables |
| 2 | Settings table: key (unique), value (JSON), updated_at |
| 3 | Activity_log table: id, action, entity_type, entity_id, details (JSON), created_at |
| 4 | Migrations versioned and can be run on all tenant DBs via script |
| 5 | Script to apply pending migrations to all active tenants |
| 6 | Foreign key constraints and indexes properly defined |

---

### Story 1.5: Tenant Selection & Context Middleware

**As a** user,
**I want** to select which tenant I'm working with,
**so that** all my actions are scoped to that tenant's data.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | API accepts `X-Tenant-Slug` header to identify tenant context |
| 2 | Middleware validates tenant exists and is active |
| 3 | Middleware establishes connection to correct tenant database |
| 4 | Database connection available via Flask `g` object in routes |
| 5 | Returns 400 if header missing on tenant-scoped endpoints |
| 6 | Returns 404 if tenant not found |
| 7 | Returns 403 if tenant is suspended |
| 8 | System-level endpoints (`/api/tenants`) don't require tenant header |
| 9 | Tenant context logged for all requests |

---

### Story 1.6: React Application Shell

**As a** user,
**I want** a basic application layout with navigation,
**so that** I can access different features of the platform.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Application shell with sidebar navigation |
| 2 | Header with tenant selector dropdown (fetches from `/api/tenants`) |
| 3 | Selecting tenant stores choice in localStorage and sets header for all API calls |
| 4 | Sidebar menu items: Dashboard, Servers, Groups, Policies, Jobs, Settings (placeholders) |
| 5 | Main content area with React Router outlet |
| 6 | Dashboard page shows "Welcome to {tenant_name}" placeholder |
| 7 | Responsive layout functional on 1280px+ screens |
| 8 | Loading spinner while tenant list loads |
| 9 | Error state if API unavailable |

---

### Story 1.7: Tenant Management UI

**As an** operator,
**I want** a simple UI to manage tenants,
**so that** I can onboard customers easily.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Admin page accessible via `/admin/tenants` route |
| 2 | Tenant list table: name, slug, status, created date, actions |
| 3 | "Create Tenant" button opens modal with: name, slug fields |
| 4 | Form validates slug format before submission |
| 5 | Success toast notification after tenant creation |
| 6 | Refresh tenant list after creation |
| 7 | Suspend/Activate toggle button per tenant row |
| 8 | Delete button with confirmation dialog (soft delete) |

---

## Epic 2: Server Management & Groups

### Epic Goal

Enable users to onboard SQL Server instances into DbTools by providing connection details. Organize servers into flexible groups with custom labels. Validate connectivity during onboarding and deploy lightweight monitoring objects to target instances. Users can view, search, and manage their server fleet through an intuitive interface.

---

### Story 2.1: Server Data Model & API

**As a** user,
**I want** to store SQL Server connection information,
**so that** DbTools can connect to and monitor my instances.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Tenant DB includes `servers` table: id, name, host, port (default 1433), instance_name (nullable), auth_type (sql/windows), username, password_encrypted, status, created_at, updated_at |
| 2 | Password stored encrypted using Fernet symmetric encryption (key from env) |
| 3 | `POST /api/servers` creates new server entry |
| 4 | `GET /api/servers` returns list of all servers for tenant |
| 5 | `GET /api/servers/{id}` returns server details (password excluded) |
| 6 | `PUT /api/servers/{id}` updates server details |
| 7 | `DELETE /api/servers/{id}` soft-deletes server |
| 8 | API validates required fields: name, host, auth_type |
| 9 | Server name must be unique within tenant |
| 10 | Supports named instances (host\instance format or separate field) |

---

### Story 2.2: Server Connection Validation

**As a** user,
**I want** to test connectivity when adding a server,
**so that** I know the connection details are correct before saving.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | `POST /api/servers/test-connection` tests connectivity without saving |
| 2 | Uses pyodbc/pymssql to attempt connection to SQL Server |
| 3 | Returns success with SQL Server version and edition on connect |
| 4 | Returns failure with descriptive error (timeout, auth failed, unreachable) |
| 5 | Connection test has 10-second timeout |
| 6 | Validates minimum SQL Server version (2016+) |
| 7 | Checks if connected user has required permissions (VIEW SERVER STATE) |
| 8 | `POST /api/servers` can include `validate: true` to test before saving |
| 9 | If validation fails with `validate: true`, server is not created |

---

### Story 2.3: Server Onboarding UI

**As a** user,
**I want** a form to add new SQL Server instances,
**so that** I can onboard servers into DbTools.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | "Add Server" button opens onboarding modal/wizard |
| 2 | Form fields: Display Name, Host, Port (default 1433), Instance Name (optional) |
| 3 | Auth type selector: SQL Authentication, Windows Authentication |
| 4 | Username and Password fields (password masked) |
| 5 | "Test Connection" button validates before saving |
| 6 | Shows connection result: success (version info) or error message |
| 7 | "Save" button disabled until connection test passes |
| 8 | Form validation with inline error messages |
| 9 | Success toast and redirect to server list on save |
| 10 | Cancel button closes modal without saving |

---

### Story 2.4: Server List View

**As a** user,
**I want** to see all my SQL Server instances in a list,
**so that** I can quickly view and manage my server fleet.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Server list page at `/servers` route |
| 2 | Table columns: Name, Host/Instance, Status, Groups (tags), Version, Added Date |
| 3 | Status indicator: Online (green), Offline (red), Unknown (gray) |
| 4 | Search box filters by name, host, or group |
| 5 | Sortable columns (click header to sort) |
| 6 | Row click navigates to server detail page |
| 7 | Bulk select checkboxes for multi-server actions |
| 8 | "Add Server" button in header |
| 9 | Empty state with prompt to add first server |
| 10 | Pagination or virtual scroll for large lists (50+ servers) |

---

### Story 2.5: Server Detail View

**As a** user,
**I want** to see detailed information about a single server,
**so that** I can review its configuration and status.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Server detail page at `/servers/{id}` route |
| 2 | Header: Server name, status badge, edit/delete actions |
| 3 | Connection info card: Host, Port, Instance, Auth Type, Version, Edition |
| 4 | Groups card: List of assigned groups with remove option |
| 5 | Labels card: List of labels with add/remove capability |
| 6 | Activity section: Recent activity log entries for this server |
| 7 | "Test Connection" button to re-validate connectivity |
| 8 | "Edit" button opens edit modal (same as onboarding form) |
| 9 | "Delete" button with confirmation dialog |
| 10 | Breadcrumb navigation back to server list |

---

### Story 2.6: Server Groups Data Model & API

**As a** user,
**I want** to organize servers into groups,
**so that** I can manage related servers together and apply policies to groups.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Tenant DB includes `server_groups` table: id, name, description, created_at |
| 2 | Tenant DB includes `server_group_members` junction table: server_id, group_id |
| 3 | Servers can belong to multiple groups (many-to-many) |
| 4 | `POST /api/groups` creates new group |
| 5 | `GET /api/groups` returns all groups with member count |
| 6 | `GET /api/groups/{id}` returns group with list of member servers |
| 7 | `PUT /api/groups/{id}` updates group name/description |
| 8 | `DELETE /api/groups/{id}` deletes group (servers remain, just unassigned) |
| 9 | `POST /api/groups/{id}/servers` adds servers to group (accepts array of server_ids) |
| 10 | `DELETE /api/groups/{id}/servers/{server_id}` removes server from group |
| 11 | Group name must be unique within tenant |

---

### Story 2.7: Server Groups UI

**As a** user,
**I want** a UI to create and manage server groups,
**so that** I can organize my fleet logically.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Groups page at `/groups` route |
| 2 | Group list: Name, Description, Server Count, Actions |
| 3 | "Create Group" button opens modal: Name, Description fields |
| 4 | Click group row expands or navigates to group detail |
| 5 | Group detail shows member server list |
| 6 | "Add Servers" button opens server picker modal (multi-select) |
| 7 | Remove server from group with X button per row |
| 8 | Edit group name/description inline or via modal |
| 9 | Delete group with confirmation (warns about policy implications) |
| 10 | Empty state prompts to create first group |

---

### Story 2.8: Server Labels/Tags

**As a** user,
**I want** to add custom labels to servers,
**so that** I can categorize and filter servers flexibly.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Tenant DB includes `labels` table: id, name (unique), color (hex) |
| 2 | Tenant DB includes `server_labels` junction table: server_id, label_id |
| 3 | `GET /api/labels` returns all labels |
| 4 | `POST /api/labels` creates new label with name and optional color |
| 5 | Labels auto-created when assigned if they don't exist |
| 6 | `POST /api/servers/{id}/labels` assigns labels (array of names) |
| 7 | `DELETE /api/servers/{id}/labels/{label_id}` removes label |
| 8 | Server list can filter by label(s) |
| 9 | Labels displayed as colored chips/badges on server rows |
| 10 | Label input with autocomplete on server detail page |

---

### Story 2.9: Deploy Monitoring Objects to SQL Server

**As a** user,
**I want** DbTools to deploy required monitoring objects to my SQL Servers,
**so that** data collection can begin.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | `POST /api/servers/{id}/deploy` deploys monitoring objects to target |
| 2 | Creates `DbTools` schema on target SQL Server |
| 3 | Deploys stored procedures for metric collection (CPU, memory, waits, etc.) |
| 4 | Deploys configuration table for collection settings |
| 5 | Returns deployment status: success or error with details |
| 6 | Deployment is idempotent (can re-run safely) |
| 7 | Validates target has required permissions before deployment |
| 8 | Server status changes to "Monitored" after successful deployment |
| 9 | `GET /api/servers/{id}/deployment-status` returns current state |
| 10 | UI shows deployment status and "Deploy" button on server detail |
| 11 | Deployment script version tracked for future upgrades |

---

## Epic 3: Data Collection & Dashboard

### Epic Goal

Implement a lightweight, reliable metric collection system that gathers performance and health data from monitored SQL Server instances. Store metrics efficiently in tenant PostgreSQL databases with configurable retention. Provide a real-time dashboard showing fleet health at a glance, with the ability to drill down into individual server metrics.

---

### Story 3.1: Metrics Data Model

**As a** developer,
**I want** a well-designed schema for storing collected metrics,
**so that** we can efficiently store and query time-series data.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Tenant DB includes `metric_types` table: id, name, unit, description |
| 2 | Tenant DB includes `metrics` table: id, server_id, metric_type_id, value (numeric), collected_at (timestamp) |
| 3 | Tenant DB includes `server_snapshots` table: id, server_id, cpu_percent, memory_percent, connection_count, status, collected_at |
| 4 | Index on (server_id, collected_at) for efficient time-range queries |
| 5 | Partitioning strategy documented for future scale (by month) |
| 6 | Seed metric types: cpu_percent, memory_percent, disk_io_reads, disk_io_writes, wait_time_ms, connection_count, batch_requests_sec |
| 7 | Collected_at stored in UTC |
| 8 | Retention policy field in tenant settings (default 30 days) |

---

### Story 3.2: Collection Configuration API

**As a** user,
**I want** to configure data collection intervals and settings,
**so that** I can balance data granularity with resource usage.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Tenant DB includes `collection_config` table: server_id, interval_seconds, enabled, metrics_enabled (JSON array) |
| 2 | Default interval: 60 seconds |
| 3 | `GET /api/servers/{id}/collection-config` returns current config |
| 4 | `PUT /api/servers/{id}/collection-config` updates config |
| 5 | Minimum interval: 30 seconds (prevent overload) |
| 6 | Maximum interval: 3600 seconds (1 hour) |
| 7 | Can enable/disable specific metric types per server |
| 8 | `POST /api/servers/{id}/collection/start` enables collection |
| 9 | `POST /api/servers/{id}/collection/stop` disables collection |
| 10 | Config changes take effect on next collection cycle |

---

### Story 3.3: Metric Collector Service

**As the** system,
**I want** a background service that collects metrics from SQL Servers,
**so that** monitoring data flows continuously into the database.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Background worker process runs independently of Flask web app |
| 2 | Worker queries system DB for all active tenants |
| 3 | For each tenant, queries tenant DB for servers with collection enabled |
| 4 | Connects to each SQL Server and executes collection stored procedures |
| 5 | Collects: CPU %, Memory %, Connection Count, Batch Requests/sec, Wait Stats |
| 6 | Stores results in tenant's metrics/snapshots tables |
| 7 | Collection per server completes in <5 seconds |
| 8 | Failed collection logged with error, doesn't stop other servers |
| 9 | Updates server status (online/offline) based on connectivity |
| 10 | Worker handles server additions/removals without restart |
| 11 | Configurable worker concurrency (default: 10 parallel connections) |
| 12 | Graceful shutdown on SIGTERM |

---

### Story 3.4: SQL Server Metric Collection Queries

**As a** developer,
**I want** optimized T-SQL queries for metric collection,
**so that** we gather useful data with minimal impact on target servers.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | CPU utilization query using sys.dm_os_ring_buffers or sys.dm_os_sys_info |
| 2 | Memory utilization from sys.dm_os_sys_memory |
| 3 | Connection count from sys.dm_exec_connections |
| 4 | Batch requests/sec from sys.dm_os_performance_counters |
| 5 | Top wait stats from sys.dm_os_wait_stats (top 10 waits) |
| 6 | Disk I/O from sys.dm_io_virtual_file_stats |
| 7 | All queries tested on SQL Server 2016, 2017, 2019, 2022 |
| 8 | Queries complete in <1 second on idle system |
| 9 | Queries require only VIEW SERVER STATE permission |
| 10 | Collection queries packaged as stored procedures in DbTools schema |

---

### Story 3.5: Metrics Retention & Cleanup

**As a** user,
**I want** old metrics automatically purged,
**so that** database storage remains manageable.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Retention period configurable per tenant (default 30 days) |
| 2 | `GET /api/settings/retention` returns current retention config |
| 3 | `PUT /api/settings/retention` updates retention period |
| 4 | Background job runs daily to delete expired metrics |
| 5 | Cleanup deletes in batches (10,000 rows) to avoid long locks |
| 6 | Cleanup job logs rows deleted per tenant |
| 7 | `GET /api/metrics/stats` returns storage statistics (row counts, date range) |
| 8 | Minimum retention: 1 day, Maximum: 365 days |

---

### Story 3.6: Server Health Status API

**As a** user,
**I want** to query current health status of servers,
**so that** I know which servers need attention.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | `GET /api/servers/health` returns health status for all servers |
| 2 | Health status: healthy, warning, critical, offline, unknown |
| 3 | Status based on latest snapshot: CPU >80% = warning, >95% = critical |
| 4 | Status based on latest snapshot: Memory >85% = warning, >95% = critical |
| 5 | Offline if no successful collection in last 5 minutes |
| 6 | Unknown if server never collected or collection disabled |
| 7 | Response includes: server_id, name, status, last_collected_at, cpu, memory |
| 8 | `GET /api/servers/{id}/health` returns single server health |
| 9 | Health thresholds configurable via tenant settings |

---

### Story 3.7: Main Dashboard UI

**As a** user,
**I want** a dashboard showing fleet health at a glance,
**so that** I can quickly identify servers needing attention.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Dashboard is the default landing page after tenant selection |
| 2 | Summary cards: Total Servers, Healthy, Warning, Critical, Offline |
| 3 | Cards are clickable - filter server list by that status |
| 4 | Server status grid/list showing all servers with status indicators |
| 5 | Color coding: Green (healthy), Yellow (warning), Red (critical), Gray (offline) |
| 6 | Auto-refresh every 30 seconds (configurable) |
| 7 | Manual refresh button |
| 8 | Group summary section: health breakdown per group |
| 9 | "Last updated" timestamp displayed |
| 10 | Empty state with prompt to add servers if none exist |

---

### Story 3.8: Server Metrics Charts

**As a** user,
**I want** to see historical metrics for a server,
**so that** I can analyze performance trends.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Server detail page includes "Metrics" tab |
| 2 | Time range selector: Last 1 hour, 6 hours, 24 hours, 7 days, 30 days |
| 3 | CPU utilization line chart over selected time range |
| 4 | Memory utilization line chart over selected time range |
| 5 | Connection count line chart |
| 6 | Charts use appropriate data aggregation (avg per 5 min for >24h) |
| 7 | `GET /api/servers/{id}/metrics?range=24h&metric=cpu` returns time series |
| 8 | Charts built with lightweight library (Chart.js or Recharts) |
| 9 | Tooltip shows exact value and timestamp on hover |
| 10 | Loading skeleton while data fetches |
| 11 | "No data" message if collection hasn't run |

---

### Story 3.9: Real-Time Status Updates

**As a** user,
**I want** server status to update without page refresh,
**so that** I always see current state.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Dashboard polls `/api/servers/health` every 30 seconds |
| 2 | Status changes trigger visual transition (fade/pulse animation) |
| 3 | Browser tab title shows alert count: "(3) DbTools" if 3 critical |
| 4 | Optional: Desktop notification on status change to critical (with permission) |
| 5 | Polling pauses when browser tab is hidden (visibility API) |
| 6 | Polling resumes immediately when tab becomes visible |
| 7 | Connection error shows banner, retries with exponential backoff |
| 8 | Server list view also updates status in real-time |

---

## Epic 4: Policies, Scheduler & Alerts

### Epic Goal

Build a comprehensive automation layer enabling users to define policies (backup, maintenance, etc.), schedule jobs with a modern visual interface, deploy policies to server groups with one click, and receive alerts when thresholds are exceeded. Complete the platform with an activity log for auditability and operational visibility.

---

### Story 4.1: Policy Data Model & API

**As a** user,
**I want** to create and manage reusable policies,
**so that** I can standardize operations across my SQL Server fleet.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Tenant DB includes `policies` table: id, name, type, description, configuration (JSON), version, is_active, created_at, updated_at |
| 2 | Policy types: backup, index_maintenance, integrity_check, custom_script |
| 3 | `POST /api/policies` creates new policy |
| 4 | `GET /api/policies` returns all policies with version info |
| 5 | `GET /api/policies/{id}` returns policy with full configuration |
| 6 | `PUT /api/policies/{id}` creates new version (immutable versioning) |
| 7 | `DELETE /api/policies/{id}` soft-deletes policy |
| 8 | Policy name must be unique within tenant |
| 9 | Configuration schema varies by type (validated on save) |
| 10 | `GET /api/policies/{id}/versions` returns version history |

---

### Story 4.2: Policy Configuration Schemas

**As a** user,
**I want** structured configuration options for each policy type,
**so that** I can define policies without writing raw scripts.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Backup policy config: backup_type (full/diff/log), destination_path, compression (bool), retention_days |
| 2 | Index maintenance config: fragmentation_threshold (%), rebuild_threshold (%), include_statistics (bool) |
| 3 | Integrity check config: check_type (physical/logical/both), include_indexes (bool) |
| 4 | Custom script config: script_content (T-SQL), timeout_seconds |
| 5 | JSON Schema validation for each policy type |
| 6 | `GET /api/policies/schemas` returns schemas for all policy types |
| 7 | API returns 400 with specific validation errors if config invalid |
| 8 | Default values populated for optional fields |

---

### Story 4.3: Policy UI - List & Create

**As a** user,
**I want** an interface to view and create policies,
**so that** I can manage my operational standards.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Policies page at `/policies` route |
| 2 | Policy list table: Name, Type, Version, Status (active/inactive), Deployed To (count), Actions |
| 3 | "Create Policy" button opens wizard/modal |
| 4 | Step 1: Select policy type from cards with descriptions |
| 5 | Step 2: Name, description, type-specific configuration form |
| 6 | Dynamic form fields based on policy type schema |
| 7 | Form validation with inline errors |
| 8 | "Save as Draft" and "Save & Activate" options |
| 9 | Success notification with link to policy detail |
| 10 | Filter/search by policy type and name |

---

### Story 4.4: Policy Deployment to Groups

**As a** user,
**I want** to deploy policies to server groups,
**so that** all servers in a group follow the same standards.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Tenant DB includes `policy_deployments` table: id, policy_id, policy_version, group_id, deployed_at, deployed_by |
| 2 | `POST /api/policies/{id}/deploy` deploys to specified group(s) |
| 3 | Request body: { group_ids: [1, 2, 3] } |
| 4 | Creates deployment record for each group |
| 5 | `GET /api/policies/{id}/deployments` returns deployment history |
| 6 | `GET /api/groups/{id}/policies` returns policies deployed to group |
| 7 | `DELETE /api/policies/{id}/deployments/{group_id}` removes deployment |
| 8 | Policy detail page shows "Deployed To" section with group list |
| 9 | "Deploy" button opens group picker modal |
| 10 | Deployment creates associated job schedule (see scheduler stories) |

---

### Story 4.5: Job Scheduler Data Model

**As a** developer,
**I want** a flexible job scheduling schema,
**so that** we can support various scheduling patterns.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Tenant DB includes `jobs` table: id, name, type, configuration (JSON), schedule_type, schedule_config (JSON), is_enabled, next_run_at, created_at |
| 2 | Tenant DB includes `job_executions` table: id, job_id, server_id, status, started_at, completed_at, result (JSON), error_message |
| 3 | Schedule types: once, interval, cron, event_triggered |
| 4 | Interval config: { interval_seconds: 3600 } |
| 5 | Cron config: { expression: "0 2 * * *" } (2 AM daily) |
| 6 | Job types: policy_execution, data_collection, custom_script, alert_check |
| 7 | Index on next_run_at for efficient scheduler queries |
| 8 | Jobs linked to policy deployments via job_id in policy_deployments |

---

### Story 4.6: Job Scheduler Engine

**As the** system,
**I want** a reliable scheduler that executes jobs on time,
**so that** automated operations run as configured.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Scheduler runs as background process using APScheduler |
| 2 | Polls for jobs where next_run_at <= now and is_enabled = true |
| 3 | Executes job based on type (calls appropriate handler) |
| 4 | Creates job_execution record on start with status = 'running' |
| 5 | Updates job_execution on completion with status = 'success' or 'failed' |
| 6 | Calculates and sets next_run_at based on schedule config |
| 7 | Supports job concurrency limits (default: 5 simultaneous) |
| 8 | Job execution timeout (default: 30 minutes) |
| 9 | Failed jobs logged with full error details |
| 10 | Scheduler recovers gracefully after restart (picks up missed jobs) |
| 11 | Handles multiple tenants (queries all tenant DBs) |

---

### Story 4.7: Job Scheduler API

**As a** user,
**I want** to manage scheduled jobs via API,
**so that** I can create, modify, and monitor automation.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | `POST /api/jobs` creates new scheduled job |
| 2 | `GET /api/jobs` returns all jobs with next_run_at and status |
| 3 | `GET /api/jobs/{id}` returns job with recent execution history |
| 4 | `PUT /api/jobs/{id}` updates job configuration and schedule |
| 5 | `DELETE /api/jobs/{id}` soft-deletes job |
| 6 | `POST /api/jobs/{id}/run` triggers immediate execution |
| 7 | `POST /api/jobs/{id}/enable` enables disabled job |
| 8 | `POST /api/jobs/{id}/disable` disables job (stops scheduling) |
| 9 | `GET /api/jobs/{id}/executions` returns paginated execution history |
| 10 | `GET /api/jobs/{id}/executions/{exec_id}` returns execution details |

---

### Story 4.8: Job Scheduler UI - Job List

**As a** user,
**I want** a visual interface to view all scheduled jobs,
**so that** I can monitor and manage automation at a glance.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Jobs page at `/jobs` route |
| 2 | Job list table: Name, Type, Schedule, Next Run, Last Run, Status, Actions |
| 3 | Status column shows: Enabled (green), Disabled (gray), Running (blue spinner) |
| 4 | "Create Job" button opens job creation wizard |
| 5 | Quick actions: Run Now, Enable/Disable, Edit, Delete |
| 6 | Filter by job type and status |
| 7 | Sort by next run time (default), name, or last run |
| 8 | Row click navigates to job detail |
| 9 | Visual indicator for jobs that failed last execution |
| 10 | Auto-refresh every 30 seconds |

---

### Story 4.9: Job Scheduler UI - Job Detail & Execution History

**As a** user,
**I want** to see detailed job information and execution history,
**so that** I can troubleshoot and verify job runs.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Job detail page at `/jobs/{id}` route |
| 2 | Header: Job name, type badge, status, "Run Now" button |
| 3 | Configuration section: Shows schedule and job-specific config |
| 4 | Execution history table: Start Time, Duration, Status, Server (if applicable) |
| 5 | Click execution row to see details: full result JSON, error message |
| 6 | Execution status: success (green), failed (red), running (blue), skipped (gray) |
| 7 | "Edit Job" button opens edit form |
| 8 | "Delete Job" with confirmation dialog |
| 9 | Timeline/calendar view option showing past and scheduled runs |
| 10 | Pagination for execution history (20 per page) |

---

### Story 4.10: Job Creation Wizard

**As a** user,
**I want** a guided interface to create scheduled jobs,
**so that** I can easily set up automation without confusion.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Multi-step wizard: Type → Configuration → Schedule → Review |
| 2 | Step 1: Select job type with descriptions |
| 3 | Step 2: Type-specific configuration (policy picker, script editor, etc.) |
| 4 | Step 3: Schedule configuration with visual helpers |
| 5 | Interval: Slider or input for minutes/hours |
| 6 | Cron: Pre-built templates (daily, weekly, monthly) + advanced cron input |
| 7 | Cron helper shows "Runs at: 2:00 AM every day" human-readable preview |
| 8 | Step 4: Review all settings before creation |
| 9 | "Test Run" option to execute immediately after creation |
| 10 | Back/Next navigation between steps |
| 11 | Form state preserved when navigating between steps |

---

### Story 4.11: Alert Rules Data Model & API

**As a** user,
**I want** to define alert rules based on metrics,
**so that** I'm notified when servers need attention.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Tenant DB includes `alert_rules` table: id, name, metric_type, operator, threshold, severity, is_enabled, created_at |
| 2 | Tenant DB includes `alerts` table: id, rule_id, server_id, status (active/acknowledged/resolved), triggered_at, resolved_at |
| 3 | Operators: gt, gte, lt, lte, eq |
| 4 | Severity levels: info, warning, critical |
| 5 | `POST /api/alert-rules` creates new rule |
| 6 | `GET /api/alert-rules` returns all rules |
| 7 | `PUT /api/alert-rules/{id}` updates rule |
| 8 | `DELETE /api/alert-rules/{id}` deletes rule |
| 9 | `GET /api/alerts` returns active alerts |
| 10 | `POST /api/alerts/{id}/acknowledge` marks alert acknowledged |
| 11 | Alerts auto-resolve when condition no longer met |

---

### Story 4.12: Alert Evaluation Engine

**As the** system,
**I want** to evaluate alert rules against collected metrics,
**so that** alerts are triggered when thresholds are exceeded.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Alert evaluator runs after each metric collection cycle |
| 2 | Compares latest metrics against all enabled alert rules |
| 3 | Creates alert record when threshold breached |
| 4 | Does not duplicate alerts (one active alert per rule per server) |
| 5 | Resolves alert when metric returns to normal for 2 consecutive checks |
| 6 | Updates server health status based on active alerts |
| 7 | Logs alert state changes to activity log |
| 8 | Supports evaluation of aggregate metrics (avg over 5 min) |
| 9 | Alert evaluation completes within 1 second per tenant |

---

### Story 4.13: Alerts UI

**As a** user,
**I want** to view and manage alerts,
**so that** I can respond to and track issues.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Alerts page at `/alerts` route |
| 2 | Active alerts table: Severity icon, Server, Rule, Triggered At, Duration, Actions |
| 3 | Severity color coding: Info (blue), Warning (yellow), Critical (red) |
| 4 | "Acknowledge" button per alert |
| 5 | Bulk acknowledge selected alerts |
| 6 | Alert history tab showing resolved alerts |
| 7 | Filter by severity, server, status |
| 8 | Dashboard shows alert count badge on Alerts nav item |
| 9 | Alert detail modal: Full context, metric value, threshold, server link |
| 10 | "Manage Rules" link to alert rules configuration page |

---

### Story 4.14: Alert Rules Configuration UI

**As a** user,
**I want** an interface to create and manage alert rules,
**so that** I can customize alerting to my needs.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Alert Rules page at `/alerts/rules` route |
| 2 | Rules list: Name, Metric, Condition, Severity, Status, Actions |
| 3 | "Create Rule" opens form: Name, Metric (dropdown), Operator, Threshold, Severity |
| 4 | Pre-built rule templates: High CPU, High Memory, Connection Spike |
| 5 | Enable/disable toggle per rule |
| 6 | Edit and delete actions |
| 7 | "Preview" shows which servers would currently trigger |
| 8 | Validation: threshold must be positive number |
| 9 | Default rules created for new tenants (CPU >90%, Memory >90%) |

---

### Story 4.15: Activity Log

**As a** user,
**I want** an audit trail of all actions,
**so that** I can track changes and troubleshoot issues.

#### Acceptance Criteria

| # | Criteria |
|---|----------|
| 1 | Activity log page at `/activity` route |
| 2 | Log entries: Timestamp, Action, Entity Type, Entity Name, Details, User (when auth added) |
| 3 | Actions logged: server_added, server_deleted, group_created, policy_deployed, job_executed, alert_triggered, config_changed |
| 4 | Filter by action type, entity type, date range |
| 5 | Search by entity name or details |
| 6 | Paginated with 50 entries per page |
| 7 | Export to CSV option |
| 8 | Activity entries created automatically by relevant APIs |
| 9 | Server detail page shows activity filtered to that server |
| 10 | Retention follows tenant settings (default 90 days) |

---

## Next Steps

### UX Expert Prompt

> Review this PRD for DbTools, a multi-tenant SQL Server management platform. Focus on the UI/UX Design Goals section and Core Screens. Create wireframes or detailed UI specifications for the key screens: Dashboard, Server List, Server Detail, Job Scheduler, and Alerts. Consider the DBA persona (technical power users) and the emphasis on at-a-glance health monitoring with drill-down capability.

### Architect Prompt

> Review this PRD for DbTools and design the technical architecture. Key areas to address: (1) Database-per-tenant PostgreSQL implementation with dynamic connection routing, (2) Flask backend structure with SQLAlchemy multi-DB support, (3) Background worker architecture for metric collection and job scheduling using APScheduler, (4) React frontend structure with TypeScript, (5) API design following REST conventions. The MVP excludes Docker and authentication - focus on core functionality with clean extension points for future security layer.

---

## Appendix

### Deferred to Post-MVP

| Feature | Rationale |
|---------|-----------|
| Docker/Containerization | Simplify initial setup; add for production deployment |
| JWT Authentication & RBAC | Security layer; add after core functionality proven |
| User Management | Depends on auth; currently open access with tenant selection |
| SSO/LDAP Integration | Enterprise feature for later phase |
| Email/Slack Notifications | Alert delivery channels for later |
| Advanced Analytics | AI/ML features after data collection is solid |
| Tenant Migration Tools | UI for self-service migration |

### Glossary

| Term | Definition |
|------|------------|
| **Tenant** | A customer organization with isolated data |
| **Server** | A monitored SQL Server instance |
| **Server Group** | A collection of servers for organizational and policy purposes |
| **Policy** | A reusable configuration for automated operations (backup, maintenance) |
| **Job** | A scheduled task that executes policies or custom scripts |
| **Alert Rule** | A threshold-based condition that triggers alerts |
| **Metric** | A measured value from SQL Server (CPU, memory, etc.) |
