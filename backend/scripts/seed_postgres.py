"""
JSON seed helper kept for local experiments only.

The live peoplepay360 PostgreSQL database already has the production schema
(Prisma-introspected). Do not create tables from the old dummy JSON models.
"""
import sys


def seed():
    print(
        "Seed skipped: this project uses the live peoplepay360 PostgreSQL schema.\n"
        "Use scripts/create_named_users.py or scripts/setup_peoplepay360.py for demo logins.\n"
        "Dummy JSON in app/data is for the in-memory dummy repositories only."
    )
    return 0


if __name__ == "__main__":
    sys.exit(seed())
