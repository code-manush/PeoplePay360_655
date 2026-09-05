"""
PeoplePay360 — HR & Payroll Platform
FastAPI application entry point.
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
from app.core.response import error_response
from app.api.routes.employees import router as employees_router
from app.api.routes.organization import dept_router, pos_router
from app.api.routes.contracts import router as contracts_router
from app.api.routes.schedules import router as schedules_router
from app.api.routes.attendance import router as attendance_router
from app.api.routes.leave import types_router, leave_router
from app.api.routes.payroll import router as payroll_router
from app.api.routes.payroll_config import router as payroll_config_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.dashboard import router as dashboard_router, stats_router
from app.api.routes.audit import router as audit_router
from app.api.routes.auth import router as auth_router
from app.api.routes.reports import router as reports_router

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-grade HR & Payroll platform — PeoplePay360 (JWT + peoplepay360 DB)",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    response.headers["X-Process-Time"] = f"{elapsed:.4f}s"
    return response


@app.get("/api/health", tags=["health"])
def health():
    db_status = "disconnected"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        db_status = f"error: {exc}"
    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "app": settings.app_name,
        "version": settings.app_version,
        "database": db_status,
        "mode": "Aiven PostgreSQL",
    }


API_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(stats_router, prefix=API_PREFIX)
app.include_router(reports_router, prefix=API_PREFIX)
app.include_router(employees_router, prefix=API_PREFIX)
app.include_router(dept_router, prefix=API_PREFIX)
app.include_router(pos_router, prefix=API_PREFIX)
app.include_router(contracts_router, prefix=API_PREFIX)
app.include_router(schedules_router, prefix=API_PREFIX)
app.include_router(attendance_router, prefix=API_PREFIX)
app.include_router(types_router, prefix=API_PREFIX)
app.include_router(leave_router, prefix=API_PREFIX)
app.include_router(payroll_router, prefix=API_PREFIX)
app.include_router(payroll_config_router, prefix=API_PREFIX)
app.include_router(notifications_router, prefix=API_PREFIX)
app.include_router(audit_router, prefix=API_PREFIX)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        return JSONResponse(status_code=exc.status_code, content=detail)
    if isinstance(detail, dict):
        return JSONResponse(status_code=exc.status_code, content=detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response("HTTP_ERROR", str(detail)),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(exc),
            }
        }
    )
