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
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
tables = cur.fetchall()
print('TABLES IN DB:')
for t in tables:
    tname = t[0]
    cur2 = conn.cursor()
    cur2.execute(f"SELECT COUNT(*) FROM \"{tname}\"")
    cnt = cur2.fetchone()[0]
    print(f'  {tname}: {cnt} rows')

print('\nCOLUMNS:')
for t in tables:
    tname = t[0]
    cur2 = conn.cursor()
    cur2.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'public' AND table_name = '{tname}' ORDER BY ordinal_position")
    cols = cur2.fetchall()
    print(f'\n  [{tname}]')
    for col in cols:
        print(f'    {col[0]}: {col[1]}')

conn.close()
