import os
from pathlib import Path

import psycopg2


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("DATABASE_URL is not set. Copy backend/.env.example to backend/.env")


conn = psycopg2.connect(database_url())
cur = conn.cursor()

cur.execute("SELECT * FROM employees LIMIT 3")
cols = [d[0] for d in cur.description]
rows = cur.fetchall()
print("=== EMPLOYEES SAMPLE ===")
for r in rows:
    print(dict(zip(cols, r)))

cur.execute("SELECT * FROM contracts LIMIT 3")
cols = [d[0] for d in cur.description]
rows = cur.fetchall()
print("\n=== CONTRACTS SAMPLE ===")
for r in rows:
    print(dict(zip(cols, r)))

cur.execute("SELECT * FROM payruns LIMIT 3")
cols = [d[0] for d in cur.description]
rows = cur.fetchall()
print("\n=== PAYRUNS SAMPLE ===")
for r in rows:
    print(dict(zip(cols, r)))

cur.execute("SELECT * FROM payslips LIMIT 3")
cols = [d[0] for d in cur.description]
rows = cur.fetchall()
print("\n=== PAYSLIPS SAMPLE ===")
for r in rows:
    print(dict(zip(cols, r)))

cur.execute("SELECT * FROM departments")
cols = [d[0] for d in cur.description]
rows = cur.fetchall()
print("\n=== DEPARTMENTS ===")
for r in rows:
    print(dict(zip(cols, r)))

conn.close()
