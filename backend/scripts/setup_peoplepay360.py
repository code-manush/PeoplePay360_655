"""Create notification tables and set demo password hashes on peoplepay360."""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.core.database import engine, Base
from app.core.config import settings
from app.core.security import hash_password
from app.models import domain  # noqa: F401


def setup():
    print("Creating notification tables if missing...")
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS hr.notifications (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                type VARCHAR(50),
                priority VARCHAR(20) DEFAULT 'NORMAL',
                target_type VARCHAR(30) NOT NULL,
                target_id UUID,
                created_by UUID,
                published_at TIMESTAMPTZ DEFAULT NOW(),
                expires_at TIMESTAMPTZ,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS hr.notification_reads (
                notification_id UUID NOT NULL,
                employee_id UUID NOT NULL,
                read_at TIMESTAMPTZ DEFAULT NOW(),
                PRIMARY KEY (notification_id, employee_id)
            )
        """))
        hashed = hash_password(settings.DEMO_PASSWORD)
        updated = conn.execute(text("""
            UPDATE identity.users
            SET password_hash = :hashed, updated_at = NOW()
            WHERE password_hash LIKE '%DEMO_PASSWORD_HASH%'
               OR password_hash NOT LIKE '$2%'
        """), {"hashed": hashed}).rowcount
        print(f"Updated {updated} user password hashes to bcrypt(demo123).")

        existing = conn.execute(text("SELECT COUNT(*) FROM hr.notifications")).scalar()
        if existing == 0:
            conn.execute(text("""
                INSERT INTO hr.notifications (title, message, type, priority, target_type, is_active)
                VALUES
                ('Welcome to PeoplePay360',
                 'The HR & Payroll platform is live. Review your profile, attendance, and leave balance.',
                 'ANNOUNCEMENT', 'HIGH', 'ALL', TRUE),
                ('August payroll computed',
                 'August 2026 payroll has been computed for 400 employees. HR can review payslips before marking paid.',
                 'PAYROLL', 'NORMAL', 'ROLE', TRUE)
            """))
            conn.execute(text("""
                UPDATE hr.notifications
                SET target_id = (SELECT id FROM identity.roles WHERE name = 'HR_MANAGER' LIMIT 1)
                WHERE title = 'August payroll computed'
            """))
            print("Seeded starter notifications.")
        else:
            print(f"Notifications already present: {existing}")

    print("peoplepay360 setup complete.")


if __name__ == "__main__":
    setup()
