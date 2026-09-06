# PeoplePay360 — Full Codebase Report

This document explains **every coding file** in the repo and **how data is fetched**: browser → FastAPI → PostgreSQL.

Companion doc: `FEATURE_MAPPING.md` is feature-oriented. This file is **file-oriented** plus the live data path.

---

## 1. How the system works

```
Browser (Vite React, usually http://127.0.0.1:5174)
    │
    │  axios apiClient  →  /api/v1/...
    │  Authorization: Bearer <JWT>
    ▼
Vite proxy  (frontend/vite.config.ts)
    │  /api  →  http://127.0.0.1:8000
    ▼
FastAPI  (backend/app/main.py)
    │  JWT in app/api/deps.py
    │  routes in app/api/routes/*.py
    ▼
Repositories  (backend/app/repositories/postgres_repos.py)
    │  SQLAlchemy 2 + psycopg2
    ▼
PostgreSQL  (Aiven / local)
    │  tables in named schemas: identity, organization, hr,
    │  attendance, leave_management, payroll_config, payroll, audit
    ▲
Prisma  (database/prisma/schema.prisma)
    └── schema documentation / Studio only
        FastAPI does NOT use Prisma Client at runtime
```

**Standard frontend pattern**

1. Page imports `apiClient`, `unwrapList`, or `unwrapData` from `frontend/src/api/client.ts`.
2. `useEffect` calls `load()` → `apiClient.get/post/put/patch(...)`.
3. Axios interceptor already returns `response.data`. Helpers then unwrap `{ data }`, `{ data: { items } }`, or `{ items }`.
4. Mutations call the API, then `load()` again.

**Standard backend pattern**

1. Route handler in `backend/app/api/routes/<module>.py`.
2. Auth via `Depends(get_current_user)` or `require_min_role("HR")`.
3. `Postgres*Repository()` reads/writes tables through SQLAlchemy `SessionLocal`.
4. Response shape: `{ success, data, message }` (see `app/core/response.py`).

**Auth storage (browser)**

| What | React state | localStorage |
|------|-------------|--------------|
| JWT | `token` | `peoplepay_token` |
| Role | `role` (`ADMIN` / `HR` / `EMPLOYEE`) | `peoplepay_role` |
| User | `user` | `peoplepay_user` |
| Employee | `employee` | `peoplepay_employee` |

---

## 2. Repo layout

| Folder | Role |
|--------|------|
| `frontend/` | React 19 + Vite + TypeScript UI |
| `backend/` | FastAPI API, payroll engine, SQLAlchemy repos |
| `database/` | Prisma schema for the same PostgreSQL database |
| `FEATURE_MAPPING.md` | Feature checklist |
| `CODEBASE_REPORT.md` | This file |

Ignored / not documented as app code: `node_modules`, `frontend/.verify`, Chrome profiles, lockfile internals, `__pycache__`, `.env` secrets.

---

## 3. Frontend — every coding file

Paths are relative to `frontend/`.

### 3.1 Entry, routing, API, auth

#### `src/main.tsx`

Mounts `<App />`. Optional `?theme=` query writes theme to `localStorage` / `data-theme`.

**Data:** none.

#### `src/App.tsx`

Router + guards.

| Path | Who can open | Page |
|------|----------------|------|
| `/landing` | public | Landing |
| `/register` | public | Register |
| `/login` | public | Login |
| `/` | logged-in | Dashboard |
| `/employees` | ADMIN, HR | EmployeeList |
| `/organization` | ADMIN, HR | Organization |
| `/contracts` | ADMIN, HR | ContractList |
| `/schedules` | ADMIN, HR | ScheduleList |
| `/attendance` | all roles | AttendanceList |
| `/leave` | all roles | LeaveList |
| `/payroll` | all roles | PayrollList |
| `/payroll-config` | ADMIN, HR | SalaryConfig |
| `/reports` | ADMIN, HR | Reports |
| `/notifications` | all roles | Notifications |
| `/audit` | ADMIN, HR | AuditLogs |
| `/settings` | all roles | Settings |
| `/ai-agent` | ADMIN, HR | AIAgent |

`ProtectedRoute` requires `role` + `token`, else `/landing`.  
`RoleRoute` requires an allowed role, else `/`.

**Data:** none (guards only read AuthContext).

#### `src/App.css`

Old Vite template styles. **Not imported.**

**Data:** none.

#### `src/index.css`

Global tokens, typography, shared form classes (`.formInput`, `.formLabel`).

**Data:** none.

#### `src/api/client.ts`

Axios instance for the whole app.

- Base URL: `VITE_API_BASE_URL` or `/api/v1` (proxied to port 8000).
- Request interceptor adds `Authorization: Bearer <token>`.
- Success interceptor returns `response.data`.
- 401 clears session and sends the user to `/login`.
- Helpers: `setAuthToken`, `unwrapList`, `unwrapData`, `downloadPayslipPdf` (raw blob GET).

**Data:** this file does not call a specific business endpoint itself; every page call goes through it.  
`downloadPayslipPdf` → **GET** `/payroll/payslips/{id}/pdf`.

#### `src/contexts/AuthContext.tsx`

Auth provider used by the whole app.

| Call | When | Then |
|------|------|------|
| **POST** `/auth/login` | `login(email, password)` | Stores token, role, user, employee |
| **GET** `/auth/me` | Mount if a token exists | Refreshes role / user / employee |

`logout()` clears React state and the four localStorage keys.

---

### 3.2 Layouts

#### `src/layouts/AppLayout.tsx` + `AppLayout.module.css`

Logged-in chrome: Sidebar + Header + `<Outlet />`.

**Data:** none.

#### `src/layouts/Sidebar.tsx` + `Sidebar.module.css`

Role-filtered nav, PeoplePay360 logo (`/brand/logo.png`), user footer, logout.

**Data:** none (reads `useAuth()` only).

#### `src/layouts/Header.tsx` + `Header.module.css`

Theme toggle + notification bell.

| Call | Source | Use |
|------|--------|-----|
| **GET** `/notifications/inbox` | `apiClient` → `unwrapList` | Unread badge vs `localStorage.lastReadNotifTimestamp` |

On `/notifications` it marks the inbox read locally and sets count to 0.

---

### 3.3 Pages (screens that fetch data)

#### `src/pages/Landing/Landing.tsx` + `Landing.module.css`

Marketing page. Logo, features, CTAs to `/login` and `/register`.

**Data:** none (static).

#### `src/pages/Login.tsx` + `Login.module.css`

Sign-in form + demo account chips (Admin / HR / Employee).

| Call | How | Backend | Database |
|------|-----|---------|----------|
| **POST** `/auth/login` | `useAuth().login()` | `backend/app/api/routes/auth.py` | `identity.users`, `identity.user_roles`, `identity.roles`, `hr.employees` (read); `users.last_login_at` (write) |

#### `src/pages/Register/Register.tsx`

Self-registration. Uses `Login.module.css` for layout.

| Call | How | Backend | Database |
|------|-----|---------|----------|
| **POST** `/auth/register` | `apiClient` | `auth.py` | Writes `identity.users`, `identity.user_roles`, `hr.employees`, `leave_management.leave_allocations` |

#### `src/pages/Register/Register.module.css`

Register-only styles. **Currently unused** (Register imports Login styles).

**Data:** none.

#### `src/pages/Dashboard.tsx` + `Dashboard.module.css`

KPI home: headcount, attendance, leave, payroll, notifications.

| Call | How | Backend | Database |
|------|-----|---------|----------|
| **GET** `/dashboard` | `apiClient` → `unwrapData` | `dashboard.py` | Reads `hr.employees`, `attendance.attendance_records`, `leave_management.leave_requests`, `payroll.payruns`, `hr.contracts`, `hr.notifications`, `organization.departments` |

#### `src/pages/Employees/EmployeeList.tsx` + `EmployeeList.module.css`

Employee table: search, filters, create, edit, deactivate. ADMIN/HR only.

| Call | Backend | Database |
|------|---------|----------|
| **GET** `/employees?page_size=500&search=` | `employees.py` | `hr.employees` (+ joins to dept/position/contracts) |
| **GET** `/departments` | `organization.py` | `organization.departments` |
| **GET** `/job-positions` | `organization.py` | `organization.job_positions` |
| **POST** `/employees` | `employees.py` | Writes `identity.users`, `hr.employees`, leave allocations, `hr.employment_history`, `attendance.employee_schedules` |
| **PUT** `/employees/{id}` | `employees.py` | Updates `hr.employees` (+ history / schedule) |
| **PATCH** `/employees/{id}/deactivate` | `employees.py` | `hr.employees.status`, `identity.users.status` |

#### `src/pages/Organization/Organization.tsx`

Departments and job positions. Reuses `LeaveList.module.css`.

| Call | Backend | Database |
|------|---------|----------|
| **GET** `/departments` | `organization.py` | `organization.departments` |
| **GET** `/job-positions` | `organization.py` | `organization.job_positions` |
| **POST** `/departments` | `organization.py` | Insert `organization.departments` |
| **POST** `/job-positions` | `organization.py` | Insert `organization.job_positions` |

#### `src/pages/Contracts/ContractList.tsx` + `ContractList.module.css`

Contracts list + create modal (employee, wage, salary structure, schedule).

| Call | Backend | Database |
|------|---------|----------|
| **GET** `/contracts?page_size=500` | `contracts.py` | `hr.contracts`, `hr.employees` |
| **GET** `/employees?page_size=500` | `employees.py` | `hr.employees` |
| **GET** `/payroll/salary-structures` | `payroll.py` | `payroll_config.salary_structures` |
| **GET** `/schedules` | `schedules.py` | `attendance.schedules` |
| **POST** `/contracts` | `contracts.py` | Writes `hr.contracts`, optional `attendance.employee_schedules`; audit log |

#### `src/pages/Schedules/ScheduleList.tsx`

Working schedules. Reuses `LeaveList.module.css`.

| Call | Backend | Database |
|------|---------|----------|
| **GET** `/schedules` | `schedules.py` | `attendance.schedules` |
| **POST** `/schedules` | `schedules.py` | Insert `attendance.schedules` (Mon–Sun time columns) |

#### `src/pages/Attendance/AttendanceList.tsx` + `AttendanceList.module.css`

Employee check-in/out. HR can filter by date/person and correct records.

| Call | Backend | Database |
|------|---------|----------|
| **GET** `/attendance?page_size=500&date=&employee_id=` | `attendance.py` | `attendance.attendance_records`, `hr.employees` (employees see own rows) |
| **GET** `/employees?page_size=500` | `employees.py` | `hr.employees` (HR only, for the filter) |
| **POST** `/attendance/check-in` | `attendance.py` | Insert/update `attendance.attendance_records` |
| **POST** `/attendance/check-out` or `/attendance/{id}/check-out` | `attendance.py` | Update check-out + hours |
| **POST** `/attendance/{id}/correct` | `attendance.py` | HR overwrite + `audit.audit_logs` |

#### `src/pages/Leave/LeaveList.tsx` + `LeaveList.module.css`

Balances, apply, approve/reject.

| Call | Backend | Database |
|------|---------|----------|
| **GET** `/leave/requests?page_size=200` | `leave.py` | `leave_management.leave_requests` (+ employee / type) |
| **GET** `/time-off/types` | `leave.py` (`types_router`) | `leave_management.leave_types` |
| **GET** `/leave/allocations?employee_id=` | `leave.py` | `leave_management.leave_allocations` |
| **POST** `/leave/requests` | `leave.py` | Insert request + `hr.notifications` |
| **POST** `/leave/requests/{id}/approve` | `leave.py` | Update request + deduct allocation + notify + audit |
| **POST** `/leave/requests/{id}/reject` | `leave.py` | Update request + notify + audit |

#### `src/pages/Payroll/PayrollList.tsx` + `PayrollList.module.css`

HR: payrun lifecycle. Employee: own payslips + PDF.

| Call | Role | Backend | Database |
|------|------|---------|----------|
| **GET** `/payroll/payruns?page_size=50` | HR | `payroll.py` | `payroll.payruns` |
| **GET** `/payroll/payslips?page_size=50` | Employee | `payroll.py` | `payroll.payslips` (own) |
| **POST** `/payroll/payruns` | HR | `payroll.py` | `payroll.payruns`, `payroll.payrun_employees` |
| **POST** `/payroll/payruns/{id}/compute` | HR | `payroll.py` → `PayrollEngine` | Writes payslips, lines, traces, snapshots, warnings |
| **POST** `/payroll/payruns/{id}/validate` | HR | `payroll.py` | `payruns.status`, `payslips.status` |
| **POST** `/payroll/payruns/{id}/pay` | HR | `payroll.py` | `payments`, `payslip_deliveries`, notifications |
| **GET** `/payroll/payruns/{id}` | HR | `payroll.py` | Payrun + slips + warnings + history |
| **GET** `/payroll/payslips/{id}` | both | `payroll.py` | Payslip + lines + payments |
| **GET** `/payroll/payslips/{id}/pdf` | both | `payroll.py` + `payslip_pdf.py` | Same payslip rows → PDF blob |

#### `src/pages/Payroll/SalaryConfig.tsx`

Salary structures and rules. Reuses `PayrollList.module.css`.

| Call | Backend | Database |
|------|---------|----------|
| **GET** `/payroll/salary-structures` | `payroll.py` | `payroll_config.salary_structures` |
| **GET** `/payroll-config/salary-rules` | `payroll_config.py` | `payroll_config.salary_rules` |
| **POST / PUT** `/payroll-config/salary-structures` | `payroll_config.py` | `salary_structures` |
| **POST / PUT** `/payroll-config/salary-rules` | `payroll_config.py` | `salary_rules`, `salary_rule_versions` |
| **POST** `/payroll-config/salary-structures/{id}/rules` | `payroll_config.py` | `salary_structure_rules` |

#### `src/pages/Reports/Reports.tsx`

HR analytics. Reuses `Dashboard.module.css`.

| Call | Backend | Database |
|------|---------|----------|
| **GET** `/reports?department_id=` | `reports.py` | employees, attendance, leave, payslips, contracts, departments |
| **GET** `/departments` | `organization.py` | `organization.departments` |

#### `src/pages/Notifications/Notifications.tsx`

Inbox. HR/Admin can send. Reuses `EmployeeList.module.css`.

| Call | Backend | Database |
|------|---------|----------|
| **GET** `/notifications/inbox` | `notifications.py` | `hr.notifications` (targeted) |
| **GET** `/departments` | `organization.py` | `organization.departments` (send form) |
| **GET** `/employees?page_size=500` | `employees.py` | `hr.employees` (send form) |
| **POST** `/notifications` | `notifications.py` | Insert `hr.notifications` |

#### `src/pages/Settings/Settings.tsx`

Read-only session card.

| Call | Backend | Database |
|------|---------|----------|
| **GET** `/auth/me` | `auth.py` | `identity.users`, `hr.employees`, roles |

Falls back to AuthContext if the request fails.

#### `src/pages/AIAgent/AIAgent.tsx` + `AIAgent.module.css`

Pick an employee, show an AI performance report.

| Call | Backend | Database |
|------|---------|----------|
| **GET** `/employees?page_size=500` | `employees.py` | `hr.employees` |
| **GET** `/ai/employee-analysis/{id}` | `ai.py` → `ai_agent.py` | Direct SQLAlchemy: employee, attendance, leave, contracts, payslips; optional Ollama (`qwen3`) |

#### `src/pages/Audit/AuditLogs.tsx`

Searchable audit table. Reuses `PayrollList.module.css`.

| Call | Backend | Database |
|------|---------|----------|
| **GET** `/audit?page_size=200&search=&event_type=` | `audit.py` | `audit.audit_logs` (+ user email join) |

---

### 3.4 Hooks and utils

#### `src/hooks/useTheme.ts`

Light/dark. Reads/writes `localStorage.theme`, sets `document.documentElement[data-theme]`.

**Data:** none (local only).

#### `src/hooks/usePointerVars.ts`

Pointer position → CSS vars on landing/login backgrounds.

**Data:** none.

#### `src/utils/currencyUtils.ts`

`numberToWords()` for INR amounts on print templates.

**Data:** none.

---

### 3.5 UI / brand / print components

None of these call the API. They receive props from pages.

| File | Function |
|------|----------|
| `src/components/ui/Button/Button.tsx` + `.module.css` | Shared button (variants, sizes, loading) |
| `src/components/ui/Card/Card.tsx` + `.module.css` | Card, header, title, content |
| `src/components/ui/Badge/Badge.tsx` + `.module.css` | Status pills |
| `src/components/ui/Modal/Modal.tsx` + `.module.css` | Dialog + backdrop |
| `src/components/brand/ThemeToggle.tsx` + `.module.css` | Landing/login theme button (`useTheme`) |
| `src/components/brand/MagneticButton.tsx` | Pointer-follow CTA on marketing pages |
| `src/components/cinematic/CinematicScene.tsx` + `.module.css` | Starfield/aurora background |
| `src/components/print/ContractPrintTemplate.tsx` + `.module.css` | Printable contract layout — **not wired to a page yet** |
| `src/components/print/PayslipPrintTemplate.tsx` + `.module.css` | Printable payslip — **not wired**; live download uses server PDF |

---

### 3.6 Frontend config files

| File | Function |
|------|----------|
| `package.json` | Scripts (`dev`, `build`) and deps (React, axios, router, recharts) |
| `vite.config.ts` | Dev server port 5174; **proxies `/api` → `http://127.0.0.1:8000`** |
| `tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json` | TypeScript project split |
| `.oxlintrc.json` | Linter |
| `index.html` | HTML shell |
| `public/brand/logo.png` | Logo used on landing, login, register, sidebar |

---

## 4. Backend — every coding file

Paths are relative to `backend/`. Empty `__init__.py` files are package markers only.

### 4.1 App entry and core

#### `app/main.py`

Creates the FastAPI app, CORS, timing header, health check, mounts every router under `/api/v1`.

**Data:** **GET** `/api/health` runs `SELECT 1` on PostgreSQL via SQLAlchemy `engine`.

#### `app/core/config.py`

Settings from `backend/.env`: `DATABASE_URL`, JWT, CORS, INR, `Asia/Kolkata`, page sizes.

**Data:** none (config only).

#### `app/core/database.py`

SQLAlchemy engine + `SessionLocal`. Rewrites `postgres://` → `postgresql://` for Aiven URLs.

**This is the live DB connection used by every repository.**

#### `app/core/security.py`

bcrypt hash/verify, JWT create/decode, role normalize (`ADMIN` / `HR` / `EMPLOYEE`).

**Data:** none (crypto helpers). Used by `auth.py` and `deps.py`.

#### `app/core/response.py`

`success_response`, paginated wrappers, `error_response`.

**Data:** none.

#### `app/core/exceptions.py`

Named exception classes. Most routes raise `HTTPException` instead.

**Data:** none.

#### `app/api/deps.py`

JWT bearer → user + employee + app role.

| Reads | Repository | Tables |
|-------|------------|--------|
| User by JWT `sub` | `PostgresUserRepository.find_by_id` | `identity.users` |
| Roles | `get_role_names` | `identity.user_roles`, `identity.roles` |
| Employee | `PostgresEmployeeRepository` | `hr.employees` |

Exports `get_current_user`, `require_role`, `require_min_role`.

---

### 4.2 Domain models

#### `app/models/domain.py`

SQLAlchemy models for all live tables (same 33 tables as Prisma, plus `audit.audit_logs`).

This is what repositories query. It is **not** Prisma-generated.

---

### 4.3 Repositories (how the API talks to the DB)

#### `app/repositories/base.py`

Abstract CRUD: `find_all`, `find_by_id`, `create`, `update`, `delete`.

#### `app/repositories/postgres_repos.py` — **live persistence**

| Class | Tables |
|-------|--------|
| `PostgresEmployeeRepository` | `hr.employees` |
| `PostgresDepartmentRepository` | `organization.departments` |
| `PostgresJobPositionRepository` | `organization.job_positions` |
| `PostgresContractRepository` | `hr.contracts` |
| `PostgresAttendanceRepository` | `attendance.attendance_records` |
| `PostgresLeaveRepository` | `leave_types`, `leave_allocations`, `leave_requests` |
| `PostgresPayrollRepository` | All `payroll_config.*` and `payroll.*` tables |
| `PostgresNotificationRepository` | `hr.notifications`, `hr.notification_reads` |
| `PostgresScheduleRepository` | `attendance.schedules`, `attendance.employee_schedules` |
| `PostgresEmploymentHistoryRepository` | `hr.employment_history` |
| `PostgresUserRepository` | `identity.users`, `roles`, `user_roles` |
| `PostgresAuditRepository` | `audit.audit_logs` |
| `PostgresBankAccountRepository` | Stub (empty; no bank table in schema) |

#### `app/repositories/dummy/store.py` + `dummy/repositories.py`

Legacy in-memory JSON from `app/data/*.json`. **Not imported by routes.** Production always uses Postgres repos.

---

### 4.4 API routes (what the frontend hits)

All paths below are under **`/api/v1`**.

#### `app/api/routes/auth.py`

| Method | Path | DB |
|--------|------|-----|
| POST | `/auth/login` | Read users/roles/employee; write `last_login_at` |
| POST | `/auth/register` | Write user, role, employee, default leave allocations |
| GET | `/auth/me` | Read current user + employee + role |
| GET | `/auth/demo-accounts` | Hardcoded demo emails (no DB) |

#### `app/api/routes/employees.py`

List / get / create / update / deactivate employees, plus nested history, contracts, attendance, leave, payroll, notifications, analytics, recommendations, report.

**Repos:** Employee, Department, JobPosition, Contract, Attendance, Leave, Payroll, Notification, EmploymentHistory, User, Audit.

#### `app/api/routes/organization.py`

`dept_router` → `/departments` CRUD.  
`pos_router` → `/job-positions` CRUD.

**Tables:** `organization.departments`, `organization.job_positions`.

#### `app/api/routes/contracts.py`

List, get, create, update, renew, terminate, expiring list.

**Tables:** `hr.contracts`, `hr.employees`, optional `employee_schedules`, `notifications`, `audit_logs`.

#### `app/api/routes/schedules.py`

CRUD on `attendance.schedules` (day columns, not a separate days table at runtime).

#### `app/api/routes/attendance.py`

List (scoped by role), check-in, check-out, correct, approve/reject, active-employees.

**Tables:** `attendance.attendance_records`. Validation helper: `notifications/attendance_validation.py`.

#### `app/api/routes/leave.py`

`types_router` → `/time-off/types`.  
`leave_router` → allocations + requests + approve/reject/cancel.

**Tables:** `leave_management.*`, plus notifications and audit.

#### `app/api/routes/payroll.py`

Salary structures (read), payruns (create/compute/validate/pay/cancel), payslips, PDF, traces, snapshots, warnings.

**Compute path:** `PayrollEngine` in `app/payroll/engine.py`.

#### `app/api/routes/payroll_config.py`

Create/update structures and rules; attach rules to structures.

**Tables:** `payroll_config.salary_structures`, `salary_rules`, `salary_rule_versions`, `salary_structure_rules`.

#### `app/api/routes/notifications.py`

Inbox, get one, create (HR), mark read, deactivate.

**Tables:** `hr.notifications`, `hr.notification_reads`.

#### `app/api/routes/dashboard.py`

**GET** `/dashboard` and **GET** `/stats` (alias). Aggregates KPIs from employees, attendance, leave, payruns, contracts, notifications, departments.

#### `app/api/routes/reports.py`

**GET** `/reports` — HR analytics with optional department filter.

#### `app/api/routes/audit.py`

**GET** `/audit` — paginated `audit.audit_logs`.

#### `app/api/routes/ai.py`

**GET** `/ai/employee-analysis/{id}` — ADMIN/HR. Calls `app/services/ai_agent.py`.

---

### 4.5 Payroll engine

| File | Function |
|------|----------|
| `app/payroll/context.py` | Bundles employee, contract, schedule, rules, attendance, leave for one slip |
| `app/payroll/rules.py` | Evaluates FIXED / PERCENTAGE / FORMULA (no `eval`) |
| `app/payroll/calculator.py` | Builds one payslip: working days, attendance/leave impact, rule lines, gross/net |
| `app/payroll/validators.py` | Pre: duplicate slip, expired contract. Post: negative net |
| `app/payroll/trace.py` | Step-by-step explainable calculation |
| `app/payroll/engine.py` | `compute_payrun`: loop employees → calculate → persist slips/lines/traces/snapshots/warnings |

**Reads:** employees, contracts, schedules, attendance, leave, salary structures/rules/versions.  
**Writes:** `payslips`, `payslip_lines`, `payslip_calculation_trace`, `payslip_inputs`, `payslip_worked_days`, `payslip_snapshots`, `payroll_warnings`, `payrun_employees.calculation_status`.

---

### 4.6 Services and reports

| File | Function | Data |
|------|----------|------|
| `app/services/audit_service.py` | Write/read audit events | `audit.audit_logs` |
| `app/services/recommendation_service.py` | Demo recommendations (attendance / OT / leave) | In-process rules, not a model |
| `app/services/ai_agent.py` | Employee analysis; Ollama or mock | Direct SQLAlchemy queries |
| `app/notifications/attendance_validation.py` | Check-in/out gate (currently allows) | none |
| `app/reports/payslip_pdf.py` | ReportLab PDF for payslip download | Receives already-loaded payslip dicts |

---

### 4.7 Scripts and utilities

| File | Function |
|------|----------|
| `scripts/seed_postgres.py` | No-op note: live DB is Prisma/Postgres, not JSON seed |
| `scripts/create_named_users.py` | Upserts demo Admin/HR/Employee users + employees |
| `scripts/setup_peoplepay360.py` | Notification tables if missing, bcrypt demo passwords, starter notifications |
| `check_db.py` | psycopg2 introspection (public schema) |
| `sample_db.py` | Sample row dump |
| `test_api.py` | HTTP smoke test against `/api/v1/employees` |
| `requirements.txt` | FastAPI, SQLAlchemy, psycopg2, PyJWT, bcrypt, ReportLab, httpx |

`app/data/*.json` — leftover dummy seed files. **Not used** by live routes.

`app/schemas/` — empty; routes take raw dict bodies.

---

## 5. Database

### 5.1 How schema is defined vs how the app queries

| Tool | Role |
|------|------|
| `database/prisma/schema.prisma` | Documents / introspects PostgreSQL (33 models, 8 schemas) |
| `database/prisma7.config.ts` | Prisma 7 config: schema path, `DATABASE_URL` |
| `database/package.json` | `npm run studio` → Prisma Studio |
| `backend/app/models/domain.py` | SQLAlchemy models the API actually uses |
| `backend/app/repositories/postgres_repos.py` | All runtime queries |

**Prisma Client is not imported in Python.** Changing Prisma without updating SQLAlchemy models will not change API behavior.

Connection string: `DATABASE_URL` in `backend/.env` (and `database/.env` for Studio).

### 5.2 Tables

| Schema | Table | Used for |
|--------|-------|----------|
| identity | `users` | Login accounts |
| identity | `roles` | ADMIN / HR / EMPLOYEE |
| identity | `user_roles` | User ↔ role |
| organization | `departments` | Org tree |
| organization | `job_positions` | Titles |
| hr | `employees` | People records |
| hr | `contracts` | Employment + wage + structure |
| hr | `employment_history` | Job-change log |
| hr | `notifications` | Inbox messages |
| hr | `notification_reads` | Read receipts |
| attendance | `schedules` | Weekly hours |
| attendance | `employee_schedules` | Who is on which schedule |
| attendance | `attendance_records` | Daily check-in/out |
| leave_management | `leave_types` | Casual / sick / etc. |
| leave_management | `leave_allocations` | Yearly balances |
| leave_management | `leave_requests` | Applications |
| payroll_config | `salary_structures` | Wage templates |
| payroll_config | `salary_rules` | Earnings / deductions |
| payroll_config | `salary_rule_versions` | Formula versions |
| payroll_config | `salary_structure_rules` | Structure ↔ rule |
| payroll | `payruns` | A payroll cycle |
| payroll | `payrun_employees` | Who is in the run |
| payroll | `payrun_status_history` | Status changes |
| payroll | `payslips` | One employee, one period |
| payroll | `payslip_lines` | Line items |
| payroll | `payslip_calculation_trace` | Explainability |
| payroll | `payslip_inputs` | Inputs used |
| payroll | `payslip_worked_days` | Day/hour buckets |
| payroll | `payslip_snapshots` | Frozen JSON snapshots |
| payroll | `payslip_deliveries` | Send log |
| payroll | `payroll_warnings` | Compute issues |
| payroll | `payments` | Paid-out records |
| audit | `audit_logs` | Who did what (SQLAlchemy; may be extra to Prisma list) |

---

## 6. Master map — page → API → file → table

| UI | Frontend file | HTTP | Backend file | Repository | Tables |
|----|---------------|------|--------------|------------|--------|
| Sign in | `Login.tsx` → `AuthContext` | POST `/auth/login` | `auth.py` | User, Employee | `users`, `user_roles`, `employees` |
| Register | `Register.tsx` | POST `/auth/register` | `auth.py` | User, Employee, Leave | `users`, `employees`, `leave_allocations` |
| Session | `AuthContext`, `Settings.tsx` | GET `/auth/me` | `auth.py` | User, Employee | `users`, `employees`, `roles` |
| Dashboard | `Dashboard.tsx` | GET `/dashboard` | `dashboard.py` | several | employees, attendance, leave, payruns, contracts, notifications |
| Employees | `EmployeeList.tsx` | GET/POST/PUT/PATCH `/employees` | `employees.py` | Employee (+ User, History) | `hr.employees`, `identity.users` |
| Org | `Organization.tsx` | GET/POST `/departments`, `/job-positions` | `organization.py` | Dept, Position | `organization.*` |
| Contracts | `ContractList.tsx` | GET/POST `/contracts` | `contracts.py` | Contract | `hr.contracts` |
| Schedules | `ScheduleList.tsx` | GET/POST `/schedules` | `schedules.py` | Schedule | `attendance.schedules` |
| Attendance | `AttendanceList.tsx` | GET/POST `/attendance*` | `attendance.py` | Attendance | `attendance.attendance_records` |
| Leave | `LeaveList.tsx` | GET/POST `/leave/*`, `/time-off/types` | `leave.py` | Leave | `leave_management.*` |
| Payruns / slips | `PayrollList.tsx` | `/payroll/payruns*`, `/payroll/payslips*` | `payroll.py` + `engine.py` | Payroll | `payroll.*`, `payroll_config.*` |
| Salary config | `SalaryConfig.tsx` | `/payroll-config/*`, `/payroll/salary-structures` | `payroll_config.py`, `payroll.py` | Payroll | `payroll_config.*` |
| Reports | `Reports.tsx` | GET `/reports` | `reports.py` | several | employees, attendance, leave, payslips |
| Notifications | `Header.tsx`, `Notifications.tsx` | GET/POST `/notifications*` | `notifications.py` | Notification | `hr.notifications` |
| Audit | `AuditLogs.tsx` | GET `/audit` | `audit.py` | Audit | `audit.audit_logs` |
| AI | `AIAgent.tsx` | GET `/ai/employee-analysis/{id}` | `ai.py` + `ai_agent.py` | direct SQLAlchemy | employees + related HR/payroll |
| Payslip PDF | `client.ts` `downloadPayslipPdf` | GET `/payroll/payslips/{id}/pdf` | `payroll.py` + `payslip_pdf.py` | Payroll | `payslips` + lines |

---

## 7. Worked examples (full path)

### Login

1. `Login.tsx` submits email/password.
2. `AuthContext.login` → **POST** `/api/v1/auth/login` via `apiClient`.
3. Vite proxies to FastAPI `auth.py`.
4. `PostgresUserRepository.find_by_email` → `identity.users`.
5. Password checked with bcrypt (`security.py`).
6. Roles from `identity.user_roles` + `identity.roles`.
7. Employee from `hr.employees` by `user_id`.
8. JWT returned; browser stores token + role + user + employee.
9. Later requests send `Authorization: Bearer …`; `deps.py` reloads user/employee from the same tables.

### Check-in

1. `AttendanceList.tsx` → **POST** `/attendance/check-in`.
2. `deps.get_current_user` resolves JWT → `users` + `employees`.
3. `attendance.py` writes today’s row in `attendance.attendance_records`.
4. Page reloads **GET** `/attendance` and redraws the table.

### Compute a payrun

1. HR on `PayrollList.tsx` → **POST** `/payroll/payruns` (creates draft + `payrun_employees`).
2. Then **POST** `/payroll/payruns/{id}/compute`.
3. `PayrollEngine` reads contract, schedule, attendance, leave, salary rules.
4. `calculator.py` + `rules.py` produce lines and net pay.
5. Writes `payslips`, `payslip_lines`, traces, snapshots, warnings.
6. Frontend refetches payrun list / detail.

### Approve leave

1. `LeaveList.tsx` → **POST** `/leave/requests/{id}/approve`.
2. `leave.py` updates `leave_requests`, decrements `leave_allocations`.
3. Creates `hr.notifications` for the employee.
4. `audit_service` inserts `audit.audit_logs`.

---

## 8. What is unused or easy to confuse

- **Dummy JSON repos** (`backend/app/repositories/dummy/*` and `backend/app/data/*.json`) are not on the live request path.
- **Prisma** does not serve API queries.
- **Print templates** in `frontend/src/components/print/` are not imported by pages; payslips download as server PDFs.
- **`App.css`** and **`Register.module.css`** are unused.
- **`PostgresBankAccountRepository`** is a stub.
- Some employee nested endpoints exist on the backend (`/employees/{id}/attendance`, etc.) but the current UI uses the shared list pages instead.

---

## 9. How to run the three layers

| Layer | Command (typical) | Port |
|-------|-------------------|------|
| Database | PostgreSQL via `DATABASE_URL` | 5432 (or Aiven) |
| Backend | `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` from `backend/` | 8000 |
| Frontend | `npm run dev` from `frontend/` | 5174 (or next free port) |

API docs: `http://127.0.0.1:8000/api/docs`.  
Health: `http://127.0.0.1:8000/api/health` (includes DB ping).
