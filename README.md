# PeoplePay360

HR and payroll system for managing employees, attendance, leave, contracts, and salary processing. Roles are Admin, HR, and Employee.

The React frontend talks to a FastAPI backend. Data lives in local PostgreSQL.

## What it does

- Employee, department, and job position management
- Contracts and employment history
- Attendance and work schedules
- Leave requests and allocations
- Payroll runs, payslips, and salary rules
- Reports, notifications, and audit logs
- JWT login with role-based access

## Stack

- Frontend: React 19, Vite, TypeScript (`frontend/`)
- Backend: FastAPI, SQLAlchemy (`backend/`)
- Database: PostgreSQL 18, database name `peoplepay360`

## Setup

Needs Python 3, Node.js, and a local PostgreSQL server.

1. Create the database (once):

```
createdb -U postgres peoplepay360
```

Restore an existing dump into `peoplepay360` if you already have one.

2. Backend

```
cd backend
copy .env.example .env
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Default local URL in `.env`:

```
postgresql://postgres:1234@localhost:5432/peoplepay360
```

Change the password if yours is different.

3. Frontend (second terminal)

```
cd frontend
npm install
npm run dev
```

UI: http://127.0.0.1:5174  
API: http://127.0.0.1:8000  
Health: http://127.0.0.1:8000/api/health

The Vite dev server proxies `/api` to the backend.

## Notes

Prisma under `database/` documents the schema only. The API uses SQLAlchemy at runtime.
