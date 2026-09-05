# PeoplePay360 - Complete Feature Mapping

## Table of Contents
1. [Frontend Pages & Features](#1-frontend-pages--features)
2. [Backend API Routes](#2-backend-api-routes--endpoints)
3. [Authentication & Security](#3-authentication--security)
4. [Payroll Engine & Calculation](#4-payroll-engine--calculation-system)
5. [Data Repositories](#5-data-repositories--persistence)
6. [Database Models](#6-database-models--domain-objects)
7. [Services & Business Logic](#7-services--business-logic)
8. [Reports & PDF Generation](#8-reports--pdf-generation)
9. [Frontend API Client](#9-frontend-api-client)
10. [UI Components](#10-frontend-ui-components)
11. [Setup & Scripts](#11-setup--initialization-scripts)
12. [Data Files](#12-data-files--json-schemas)

---

## 1. FRONTEND PAGES & FEATURES

### Dashboard
- **Main File:** `frontend/src/pages/Dashboard.tsx`
- **Styling:** `frontend/src/pages/Dashboard.module.css`
- **Backend Route:** `backend/app/api/routes/dashboard.py`
- **Features Implemented:**
  - Employee count by employment type
  - Department-wise employee distribution
  - Today's attendance stats (present, late, absent)
  - Pending leave requests
  - Payroll disbursement tracking
  - Contract expiry warnings (30, 60, 90 days)
  - Payroll warnings dashboard
  - 30-day attendance rate
  - Monthly payroll trend charts
  - Department-wise attendance statistics

### Login Page
- **Files:**
  - `frontend/src/pages/Login.tsx` (Logic)
  - `frontend/src/pages/Login.module.css` (Styling)
- **Backend Files:**
  - `backend/app/api/routes/auth.py` (Authentication endpoint)
  - `backend/app/core/security.py` (JWT & password handling)
- **Context File:** `frontend/src/contexts/AuthContext.tsx`
- **Features Implemented:**
  - Email/password authentication
  - JWT token generation and storage
  - Role-based access (ADMIN, HR, EMPLOYEE)
  - Session persistence via localStorage
  - Multi-role support
  - Password hash verification (bcrypt)
  - Last login tracking

### Employees Page
- **Files:**
  - `frontend/src/pages/Employees/EmployeeList.tsx` (Logic)
  - `frontend/src/pages/Employees/EmployeeList.module.css` (Styling)
- **Backend Files:**
  - `backend/app/api/routes/employees.py` (API endpoints)
  - `backend/app/models/domain.py` (Employee model)
  - `backend/app/repositories/postgres_repos.py` (PostgresEmployeeRepository)
- **Features Implemented:**
  - List all employees with pagination
  - Search by name, employee code, email
  - Filter by department, employment type, status
  - Create new employees
  - Edit employee details
  - Delete/deactivate employees
  - View employee manager and department
  - View active contracts per employee
  - Rich employee profile enrichment

### Attendance Page
- **Files:**
  - `frontend/src/pages/Attendance/AttendanceList.tsx` (Logic)
  - `frontend/src/pages/Attendance/AttendanceList.module.css` (Styling)
- **Backend Files:**
  - `backend/app/api/routes/attendance.py` (API endpoints)
  - `backend/app/models/domain.py` (AttendanceRecord model)
  - `backend/app/repositories/postgres_repos.py` (PostgresAttendanceRepository)
  - `backend/app/notifications/attendance_validation.py` (Validation logic)
- **Features Implemented:**
  - View attendance records with filtering
  - Filter by employee, date range, status, department
  - Track check-in/check-out times
  - Calculate worked hours
  - Attendance status tracking: PRESENT, ABSENT, LATE, HALF_DAY, OVERTIME
  - Department-wise attendance reports
  - Employee-specific view for personal attendance

### Leave Management Page
- **Files:**
  - `frontend/src/pages/Leave/LeaveList.tsx` (Logic)
  - `frontend/src/pages/Leave/LeaveList.module.css` (Styling)
- **Backend Files:**
  - `backend/app/api/routes/leave.py` (API endpoints)
  - `backend/app/models/domain.py` (Leave models: Type, Allocation, Request)
  - `backend/app/repositories/postgres_repos.py` (PostgresLeaveRepository)
- **Features Implemented:**
  - View leave allocations per employee/year
  - List leave types and their attributes
  - Submit leave requests
  - Approve/reject leave requests (HR only)
  - Track leave balance
  - Filter by status: PENDING, APPROVED, REJECTED
  - View leave duration and type
  - Year-based allocation tracking

### Payroll Page
- **Files:**
  - `frontend/src/pages/Payroll/PayrollList.tsx` (Logic)
  - `frontend/src/pages/Payroll/PayrollList.module.css` (Styling)
- **Backend Files:**
  - `backend/app/api/routes/payroll.py` (Main API endpoint)
  - `backend/app/payroll/engine.py` (Payroll computation engine)
  - `backend/app/payroll/calculator.py` (Payslip calculator)
  - `backend/app/payroll/rules.py` (Rule evaluation engine)
  - `backend/app/payroll/context.py` (Calculation context builder)
  - `backend/app/payroll/validators.py` (Pre/post-compute validations)
  - `backend/app/payroll/trace.py` (Debug tracing)
  - `backend/app/models/domain.py` (Payroll models)
  - `backend/app/repositories/postgres_repos.py` (PostgresPayrollRepository)
- **Features Implemented:**
  - View salary structures with rule versions
  - Manage salary rules and versions
  - Create and manage payruns
  - View payrun status: DRAFT, COMPUTED, VALIDATED, PAID
  - Generate payslips with automatic calculation
  - View payslip details and line items
  - Download payslips as PDF
  - Salary structure assignment to employees
  - Rule-based calculations: FIXED, PERCENTAGE, FORMULA
  - Formula expression evaluation with safe arithmetic
  - Attendance-based deductions/additions
  - Leave impact on salary
  - Overtime calculations
  - Validation warnings and error tracking
  - Payroll warning tracking (errors, blockers)

### Contracts Page
- **Files:**
  - `frontend/src/pages/Contracts/ContractList.tsx` (Logic)
  - `frontend/src/pages/Contracts/ContractList.module.css` (Styling)
- **Backend Files:**
  - `backend/app/api/routes/contracts.py` (API endpoints)
  - `backend/app/models/domain.py` (Contract model)
  - `backend/app/repositories/postgres_repos.py` (PostgresContractRepository)
- **Features Implemented:**
  - List all contracts with details
  - Filter by status, employee, department
  - Track contract start/end dates
  - Calculate days remaining until expiry
  - Contract expiry status: CRITICAL, URGENT, WARNING, NOTICE
  - Track contract type and salary structure
  - Monitor working hours per week
  - Employment status tracking

### Reports Page
- **Files:**
  - `frontend/src/pages/Reports/Reports.tsx` (Logic)
- **Backend Files:**
  - `backend/app/api/routes/reports.py` (Report generation)
  - `backend/app/reports/payslip_pdf.py` (PDF generation)
- **Features Implemented:**
  - Generate comprehensive HR reports
  - Filter by department and date range
  - KPI metrics: employee count, attendance health, payroll summary
  - Attendance statistics: present, absent, attendance rate
  - Leave utilization reports
  - Payslip and salary reports
  - Department-wise analysis
  - Monthly payroll trends

### Notifications Page
- **Files:**
  - `frontend/src/pages/Notifications/Notifications.tsx` (Logic)
- **Backend Files:**
  - `backend/app/api/routes/notifications.py` (API endpoints)
  - `backend/app/models/domain.py` (Notification model)
  - `backend/app/repositories/postgres_repos.py` (PostgresNotificationRepository)
- **Features Implemented:**
  - View inbox notifications
  - Filter by type and priority
  - Mark notifications as read
  - Create announcements (HR only)
  - Target notifications: ALL_EMPLOYEES, ROLE, DEPARTMENT, EMPLOYEE
  - Notification delivery tracking

### Settings Page
- **File:** `frontend/src/pages/Settings/Settings.tsx`
- **Features:** User and system configuration management

### Layout Components
- **AppLayout:**
  - `frontend/src/layouts/AppLayout.tsx` (Main layout logic)
  - `frontend/src/layouts/AppLayout.module.css` (Styling)
  - Purpose: Main application layout with sidebar navigation
  - Features: Route protection, auth state integration

- **Header:**
  - `frontend/src/layouts/Header.tsx` (Header logic)
  - `frontend/src/layouts/Header.module.css` (Styling)
  - Purpose: Top navigation bar with user menu

- **Sidebar:**
  - `frontend/src/layouts/Sidebar.tsx` (Navigation logic)
  - `frontend/src/layouts/Sidebar.module.css` (Styling)
  - Purpose: Side navigation with role-based menu items

---

## 2. BACKEND API ROUTES & ENDPOINTS

### Authentication Routes
- **File:** `backend/app/api/routes/auth.py`
- **Base Path:** `/api/v1/auth`
- **Endpoints:**
  - `POST /login` - User login with email/password, returns JWT token
  - JWT token generation with role and employee info
  - Password hash verification and upgrade
  - Last login tracking
  - Multi-role support

### Dashboard Routes
- **File:** `backend/app/api/routes/dashboard.py`
- **Base Path:** `/api/v1/dashboard`
- **Endpoints:**
  - `GET /dashboard` - Get dashboard KPIs and metrics
  - `GET /stats` - Detailed statistics endpoint
  - Computed metrics: employee counts, attendance, payroll, contracts

### Employees Routes
- **File:** `backend/app/api/routes/employees.py`
- **Base Path:** `/api/v1/employees`
- **Endpoints:**
  - `GET /` - List employees with pagination/filtering
  - `GET /{employee_id}` - Get single employee details
  - `POST /` - Create new employee
  - `PUT /{employee_id}` - Update employee
  - `DELETE /{employee_id}` - Deactivate employee
  - Employee enrichment with department, position, manager, active contract

### Attendance Routes
- **File:** `backend/app/api/routes/attendance.py`
- **Base Path:** `/api/v1/attendance`
- **Endpoints:**
  - `GET /` - List attendance records with filters
  - `POST /` - Record check-in/check-out
  - `PUT /{record_id}` - Update attendance record
  - Automatic status calculation: PRESENT, ABSENT, LATE, HALF_DAY, OVERTIME
  - Worked hours calculation
  - Department-level filtering

### Leave Routes
- **File:** `backend/app/api/routes/leave.py`
- **Base Paths:** `/api/v1/leave`, `/api/v1/time-off`
- **Endpoints:**
  - `GET /time-off/types` - List leave types
  - `GET /time-off/types/{type_id}` - Get leave type details
  - `GET /leave/allocations` - List leave allocations
  - `GET /leave/allocations/{employee_id}` - Get employee leave balance
  - `GET /leave/requests` - List leave requests with filtering
  - `POST /leave/requests` - Submit leave request
  - `PUT /leave/requests/{request_id}` - Approve/reject leave requests
  - Year-based allocation tracking
  - Status tracking: PENDING, APPROVED, REJECTED

### Payroll Routes
- **File:** `backend/app/api/routes/payroll.py`
- **Base Path:** `/api/v1/payroll`
- **Endpoints:**
  - `GET /salary-structures` - List salary structures
  - `GET /salary-structures/{structure_id}` - Get structure with rule versions
  - `GET /payruns` - List payruns with pagination
  - `GET /payruns/{payrun_id}` - Get payrun with payslips and warnings
  - `POST /payruns` - Create new payrun
  - `POST /payruns/{payrun_id}/compute` - Calculate payslips
  - `POST /payruns/{payrun_id}/validate` - Validate payrun
  - `POST /payruns/{payrun_id}/finalize` - Mark payrun as paid
  - `GET /payslips` - List payslips with filtering
  - `GET /payslips/{payslip_id}` - Get single payslip with line items
  - `GET /payslips/{payslip_id}/pdf` - Download payslip PDF
  - `GET /payslips/{payslip_id}/deliveries` - Track delivery status
  - Advanced filtering, status management, PDF generation

### Contracts Routes
- **File:** `backend/app/api/routes/contracts.py`
- **Base Path:** `/api/v1/contracts`
- **Endpoints:**
  - `GET /` - List contracts with expiry tracking
  - `GET /{contract_id}` - Get contract details
  - `POST /` - Create contract
  - `PUT /{contract_id}` - Update contract
  - Contract expiry status: CRITICAL, URGENT, WARNING, NOTICE
  - Days remaining calculation

### Organization Routes
- **File:** `backend/app/api/routes/organization.py`
- **Base Paths:** `/api/v1/departments`, `/api/v1/job-positions`
- **Department Endpoints:**
  - `GET /` - List all departments
  - `GET /{dept_id}` - Get department details
  - `POST /` - Create department
  - `PUT /{dept_id}` - Update department
  - `DELETE /{dept_id}` - Delete department
- **Job Position Endpoints:**
  - `GET /` - List positions with filtering by department
  - `GET /{pos_id}` - Get position details
  - `POST /` - Create position
  - `PUT /{pos_id}` - Update position
  - `DELETE /{pos_id}` - Delete position

### Schedules Routes
- **File:** `backend/app/api/routes/schedules.py`
- **Base Path:** `/api/v1/schedules`
- **Endpoints:**
  - `GET /` - List work schedules
  - `GET /{schedule_id}` - Get schedule with days configuration
  - `POST /` - Create work schedule
  - `PUT /{schedule_id}` - Update schedule and days
  - `DELETE /{schedule_id}` - Delete schedule
  - Weekly hours calculation
  - Working days per week tracking
  - Day-of-week configuration: MONDAY-SUNDAY

### Notifications Routes
- **File:** `backend/app/api/routes/notifications.py`
- **Base Path:** `/api/v1/notifications`
- **Endpoints:**
  - `GET /` - List notifications for current user
  - `GET /inbox` - Get personal inbox
  - `GET /{notif_id}` - Get notification details
  - `POST /` - Create announcement/notification (HR only)
  - `POST /{notif_id}/read` - Mark notification as read
  - `DELETE /{notif_id}` - Deactivate notification
  - Targeting: ALL_EMPLOYEES, ROLE, DEPARTMENT, EMPLOYEE

### Audit Routes
- **File:** `backend/app/api/routes/audit.py`
- **Base Path:** `/api/v1/audit`
- **Endpoints:**
  - `GET /` - Get audit logs with optional filtering

### Reports Routes
- **File:** `backend/app/api/routes/reports.py`
- **Base Path:** `/api/v1/reports`
- **Endpoints:**
  - `GET /` - Generate comprehensive HR reports
  - Filters: department, date range
  - KPIs: employees, active contracts, attendance health, leaves, payroll
  - Department-wise salary analysis
  - Monthly payroll trends

### Health Check
- **File:** `backend/app/main.py`
- **Endpoint:**
  - `GET /api/health` - Database connectivity and app status check

---

## 3. AUTHENTICATION & SECURITY

### Frontend Authentication
- **Context File:** `frontend/src/contexts/AuthContext.tsx`
- **Features:**
  - User and employee context management
  - Role-based access control: ADMIN, HR, EMPLOYEE
  - Token persistence and refresh
  - Login/logout functions
  - Local storage for credentials
  - useAuth() hook for components

### Backend Security
- **Security Module:** `backend/app/core/security.py`
- **Features:**
  - Password hashing with bcrypt ($2b$ algorithm)
  - JWT token creation and validation
  - Role normalization
  - Token expiration management
  - API key support
  - Dependency-based current user injection

### API Dependency Management
- **Dependencies File:** `backend/app/api/deps.py`
- **Features:**
  - `get_current_user()` - Extract and validate JWT token
  - `require_min_role(role)` - Role-based access protection
  - User authorization middleware

---

## 4. PAYROLL ENGINE & CALCULATION SYSTEM

### Payroll Engine (Orchestrator)
- **File:** `backend/app/payroll/engine.py`
- **Purpose:** Master orchestrator for payroll computation
- **Features:**
  - Coordinates payrun computation
  - Loads salary structures and rule versions
  - Assembles employee context (attendance, leave, contracts)
  - Triggers payslip calculation
  - Manages pre/post validation
  - Generates calculation traces for debugging
  - Handles warnings and errors
  - Transaction management

### Payroll Calculator (Single-Employee)
- **File:** `backend/app/payroll/calculator.py`
- **Purpose:** Single-employee payslip computation
- **Features:**
  - Attendance metrics calculation:
    - Worked days from attendance records
    - Paid vs unpaid leave tracking
    - Overtime hours calculation
  - Working days counting based on schedule
  - Rule execution in sequence
  - Gross and net salary computation
  - Payslip line item creation with trace
  - Integration with salary structures

### Payroll Rules Engine (Safe Evaluation)
- **File:** `backend/app/payroll/rules.py`
- **Purpose:** Safe salary rule evaluation without eval()
- **Calculation Types:**
  - **FIXED** - Fixed amount per rule
  - **PERCENTAGE** - Percentage of base amount
  - **FORMULA** - Arithmetic expression evaluation
- **Features:**
  - Formula tokenizer and parser
  - Safe arithmetic evaluation (NO eval())
  - Variable resolution from context
  - Supported variables: CONTRACT_WAGE, WORKED_DAYS, TOTAL_WORKING_DAYS, OVERTIME_HOURS, PAID_LEAVE_DAYS, UNPAID_LEAVE_DAYS, Rule codes
  - Supported operations: +, -, *, /, (), negation
  - Expression validation and error handling

### Payroll Context Builder
- **File:** `backend/app/payroll/context.py`
- **Purpose:** Salary calculation context builder
- **Maintains:**
  - Employee and contract details
  - Attendance and leave data
  - Schedule configuration
  - Computed rule values
  - Trace log for debugging
  - Data loading from repositories

### Payroll Validators
- **File:** `backend/app/payroll/validators.py`
- **Pre-Compute Validations:**
  - Missing bank account details
  - Duplicate payslip detection
  - Contract expiry warnings
  - Employment status checks
- **Post-Compute Validations:**
  - Payslip amount reasonableness
  - Net salary verification
  - Missing line items
- **Warning Severity Levels:** ERROR, WARNING, BLOCKER

### Calculation Trace (Debugging)
- **File:** `backend/app/payroll/trace.py`
- **Purpose:** Debug-friendly payroll calculation logging
- **Features:**
  - Trace each rule calculation
  - Log formula resolution
  - Record intermediate values
  - Enable transparency for debugging
  - JSON exportable traces

---

## 5. DATA REPOSITORIES & PERSISTENCE

### Base Repository (Abstract)
- **File:** `backend/app/repositories/base.py`
- **Purpose:** Abstract base for all repositories
- **Interface:** CRUD operations (create, read, update, delete, find)

### PostgreSQL Repository Implementation
- **File:** `backend/app/repositories/postgres_repos.py`
- **Repositories:**
  - `PostgresUserRepository` - User management
  - `PostgresEmployeeRepository` - Employee records
  - `PostgresDepartmentRepository` - Departments
  - `PostgresJobPositionRepository` - Job positions
  - `PostgresContractRepository` - Employment contracts
  - `PostgresAttendanceRepository` - Attendance records
  - `PostgresLeaveRepository` - Leave types, allocations, requests
  - `PostgresPayrollRepository` - Salary structures, rules, payruns, payslips
  - `PostgresNotificationRepository` - Notifications and read status
  - `PostgresBankAccountRepository` - Employee bank details
  - `PostgresScheduleRepository` - Work schedules and schedule days
  - `PostgresAuditRepository` - Audit logs
  - `PostgresPaymentRepository` - Payment records
- **Features:**
  - Object-relational mapping
  - Field mapping normalization
  - Query filtering and pagination
  - Bulk operations
  - Connection pooling via SQLAlchemy

### Dummy Repository (Demo/Testing)
- **Location:** `backend/app/repositories/dummy/`
- **Files:**
  - `backend/app/repositories/dummy/repositories.py` - Dummy implementations
  - `backend/app/repositories/dummy/store.py` - In-memory data store
- **Purpose:** Demo data for development without database

---

## 6. DATABASE MODELS & DOMAIN OBJECTS

### SQLAlchemy Models
- **Master File:** `backend/app/models/domain.py`

#### Identity Schema (User Management)
- **User** - System users with email, password hash, status
- **Role** - Role definitions (ADMIN, HR, EMPLOYEE)
- **UserRole** - User-role associations

#### Organization Schema
- **Department** - Organizational departments with hierarchical structure
- **JobPosition** - Job titles and positions per department

#### HR Schema
- **Employee** - Employee master with personal details (PAN, Aadhar, etc.)
- **Contract** - Employment contracts with salary info
- **AttendanceRecord** - Daily attendance tracking
- **LeaveType** - Leave category definitions
- **LeaveAllocation** - Annual leave balance per employee
- **LeaveRequest** - Leave requests with approval workflow
- **Schedule** - Work schedule templates (5-day, 6-day, etc.)
- **ScheduleDay** - Daily schedule configuration (hours per day)
- **Notification** - System announcements
- **NotificationRead** - Read status tracking

#### Payroll Schema
- **SalaryStructure** - Salary template definitions
- **SalaryRule** - Individual salary rule definitions
- **SalaryRuleVersion** - Rule configurations with calculation parameters
- **Payrun** - Monthly/periodic payroll batch
- **PayrunEmployee** - Employees in a payrun
- **Payslip** - Individual salary statement
- **PayslipLine** - Line items (gross, deductions, etc.)
- **PayslipDelivery** - Payslip delivery status tracking
- **PayrollWarning** - Validation warnings during payroll
- **BankAccount** - Employee bank details for payments
- **Payment** - Payment records

#### Audit Schema
- **AuditLog** - Event audit trail for compliance tracking

---

## 7. SERVICES & BUSINESS LOGIC

### Audit Service (Compliance Logging)
- **File:** `backend/app/services/audit_service.py`
- **Purpose:** Centralized audit logging for compliance
- **Features:**
  - `log()` - Log any business event
  - `get_logs()` - Retrieve audit logs with filtering
  - Event tracking: entity_type, event_type, actor_id, description, metadata
  - Compliance and audit trail maintenance

### Recommendation Service (Employee Insights)
- **File:** `backend/app/services/recommendation_service.py`
- **Purpose:** AI-powered employee recommendations (demo mode with rule-based logic)
- **Current Demo Rules:**
  - High overtime → workload concern
  - Excellent attendance → performance recognition
  - Multiple late arrivals → attendance improvement suggestion
  - Low attendance → concern alert
  - Unused leave → leave utilization suggestion
  - Strong performance + overtime → increment consideration
- **Architecture:** Ready for LLM integration (Ollama, etc.)

### Attendance Validation Service
- **File:** `backend/app/notifications/attendance_validation.py`
- **Purpose:** Validates and processes attendance records
- **Features:** Entry point for attendance-based notifications and validations

---

## 8. REPORTS & PDF GENERATION

### Payslip PDF Generator
- **File:** `backend/app/reports/payslip_pdf.py`
- **Purpose:** Generate downloadable payslip PDFs
- **Features:**
  - PDF formatting of payslip data
  - Line item breakdown
  - Employee and company details
  - Period and payment information
  - Format: suitable for bank submission and employee records
  - Integration with payroll route for download endpoint

---

## 9. FRONTEND API CLIENT

### API Client Module
- **File:** `frontend/src/api/client.ts`
- **Features:**
  - Axios-based HTTP client
  - Base URL: `http://localhost:8000/api/v1`
  - JWT token injection in Authorization headers
  - Automatic authentication redirect on 401 (Unauthorized)
  - Error message extraction and display
  - Response unwrapping utilities: `unwrapData()`, `unwrapList()`
  - Bearer token management
  - Request/response interceptors

---

## 10. FRONTEND UI COMPONENTS

### Reusable UI Components
- **Location:** `frontend/src/components/ui/`

#### Card Component
- **Files:**
  - `frontend/src/components/ui/Card/Card.tsx` (Component logic)
  - `frontend/src/components/ui/Card/Card.module.css` (Styling)
- **Purpose:** Reusable card layout component for content grouping

#### Badge Component
- **Files:**
  - `frontend/src/components/ui/Badge/Badge.tsx`
  - `frontend/src/components/ui/Badge/Badge.module.css`
- **Purpose:** Status and tag display

#### Button Component
- **Files:**
  - `frontend/src/components/ui/Button/Button.tsx`
  - `frontend/src/components/ui/Button/Button.module.css`
- **Purpose:** Reusable button with variants

#### Modal Component
- **Files:**
  - `frontend/src/components/ui/Modal/Modal.tsx`
  - `frontend/src/components/ui/Modal/Modal.module.css`
- **Purpose:** Dialog/modal functionality

---

## 11. SETUP & INITIALIZATION SCRIPTS

### Database & Connection Scripts
- **check_db.py** - Database connection verification
- **sample_db.py** - Sample data generation
- **test_api.py** - API endpoint testing

### User & Data Setup
- **scripts/create_named_users.py** - User creation utility
- **scripts/seed_postgres.py** - PostgreSQL data seeding with relationships
- **scripts/setup_peoplepay360.py** - Complete system setup script

---

## 12. DATA FILES & JSON SCHEMAS

### Seed Data Location
- **Base:** `backend/app/data/`

#### Employee & Organization Data
- **employees.json** - Employee master data
- **departments.json** - Department definitions
- **job_positions.json** - Job position catalog
- **employee_bank_accounts.json** - Bank account details

#### Contract & Schedule Data
- **contracts.json** - Sample employment contracts
- **working_schedules.json** - Work schedule templates
- **working_schedule_days.json** - Schedule day details

#### Payroll Data
- **salary_structures.json** - Salary structure templates
- **salary_rules.json** - Salary rule definitions
- **salary_rule_versions.json** - Rule configurations
- **payruns.json** - Payrun history
- **payslips.json** - Payslip records
- **payslip_lines.json** - Payslip line items
- **payslip_deliveries.json** - Delivery tracking
- **payroll_warnings.json** - Validation warnings
- **payrun_employees.json** - Payrun membership
- **payments.json** - Payment records

#### Attendance & Leave Data
- **attendance_records.json** - Attendance history
- **leave_types.json** - Leave type definitions
- **leave_allocations.json** - Annual leave balances
- **leave_requests.json** - Leave request records
- **time_off_types.json** - Time off type definitions

#### System Data
- **notifications.json** - Notification records
- **audit_logs.json** - Audit trail

---

## 13. CORE CONFIGURATION & UTILITIES

### Application Configuration
- **File:** `backend/app/core/config.py`
- **Variables:**
  - App name, version
  - Database connection strings
  - JWT settings
  - API documentation URLs

### Database Configuration
- **File:** `backend/app/core/database.py`
- **Purpose:** SQLAlchemy engine and session management
- **Database:** Aiven PostgreSQL (production-grade)
- **Features:** Connection pooling, session management

### Response Formatting
- **File:** `backend/app/core/response.py`
- **Utilities:**
  - `success_response()` - Standardized success wrapper
  - `error_response()` - Standardized error wrapper
  - `paginated_response()` - Pagination metadata wrapper

### Exception Handling
- **File:** `backend/app/core/exceptions.py`
- **Exception Types:**
  - `NotFoundException` - Resource not found
  - Custom HTTP exception handlers in main.py

---

## 14. APPLICATION ENTRY POINTS

### Backend Entry Point
- **File:** `backend/app/main.py`
- **Setup:**
  - FastAPI application initialization
  - Router registration for all API routes
  - CORS middleware configuration
  - Error handler setup
  - Health check endpoint configuration
  - Request/response logging
  - Database connection initialization

### Frontend Entry Points
- **Main Entry:** `frontend/src/main.tsx`
  - React DOM rendering
  - App initialization
  
- **App Component:** `frontend/src/App.tsx`
  - Route definitions
  - Protected route wrapper
  - Authentication provider initialization
  - Layout setup

### Build Configuration
- **Vite Config:** `frontend/vite.config.ts`
- **TypeScript Config:** `frontend/tsconfig.json`
- **Node Config:** `frontend/tsconfig.node.json`
- **App Config:** `frontend/tsconfig.app.json`

---

## 15. QUICK REFERENCE - FEATURE TO FILES MAPPING

| **Feature** | **Frontend Files** | **Backend Files** |
|---|---|---|
| **Authentication** | `Login.tsx`, `AuthContext.tsx` | `auth.py`, `security.py`, `deps.py` |
| **Dashboard** | `Dashboard.tsx` | `dashboard.py` |
| **Employee Management** | `EmployeeList.tsx` | `employees.py`, `Employee` model |
| **Attendance Tracking** | `AttendanceList.tsx` | `attendance.py`, `AttendanceRecord` model, `attendance_validation.py` |
| **Leave Management** | `LeaveList.tsx` | `leave.py`, `LeaveType/Request/Allocation` models |
| **Payroll Processing** | `PayrollList.tsx` | `payroll.py`, `engine.py`, `calculator.py`, `rules.py`, `context.py`, `validators.py`, `trace.py` |
| **Contract Management** | `ContractList.tsx` | `contracts.py`, `Contract` model |
| **Organization Setup** | (Dashboard, Employees) | `organization.py`, `Department/JobPosition` models |
| **Work Schedules** | (Contract setup) | `schedules.py`, `Schedule/ScheduleDay` models |
| **Notifications** | `Notifications.tsx` | `notifications.py`, `Notification` model |
| **Reports & Analytics** | `Reports.tsx`, `Dashboard.tsx` | `reports.py`, `payslip_pdf.py` |
| **Audit Logging** | (All pages) | `audit.py`, `audit_service.py`, `AuditLog` model |
| **Recommendations** | `Dashboard.tsx` | `recommendation_service.py` |
| **API Client** | `api/client.ts` | (All routes) |
| **Layouts** | `AppLayout.tsx`, `Header.tsx`, `Sidebar.tsx` | `main.py` |
| **Security** | `AuthContext.tsx` | `security.py`, `deps.py` |
| **Database** | (All pages via API) | `database.py`, `postgres_repos.py`, `base.py` |
| **Data Models** | (JSON responses) | `domain.py` |

---

## 16. KEY ARCHITECTURE PATTERNS

1. **Repository Pattern** - Data access abstraction via `PostgresXxxRepository` classes
2. **Service Layer** - Business logic in dedicated service files (AuditService, RecommendationService)
3. **Dependency Injection** - FastAPI `Depends()` for auth, repos, services
4. **Role-Based Access Control** - `require_min_role()`, token-based auth
5. **Response Wrapping** - Standardized success/error/paginated responses
6. **Calculation Engine** - Modular payroll (context → calculator → rules)
7. **Audit Trail** - All important operations logged via AuditService
8. **State Management** - AuthContext for frontend auth state
9. **Safe Formula Evaluation** - Custom parser instead of eval() for security
10. **Multi-Layer Validation** - Pre-compute and post-compute payroll validations

---

## Summary Statistics

- **Frontend Pages:** 8 main pages + 5 layouts
- **Backend API Routes:** 11 main route modules with 40+ endpoints
- **Database Models:** 25+ SQLAlchemy models
- **Services:** 3 main services + utilities
- **Repositories:** 13 repository implementations
- **UI Components:** 4+ reusable components
- **Data Files:** 22 JSON seed files
- **Total Implementation Files:** 50+ Python/TypeScript files

**Last Updated:** 2026-09-05
