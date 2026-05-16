"""
Migration: Fix FK constraints on eligibility_checks and audit_logs
- Drop existing FK constraints that block DELETE on patients/trials
- Re-add them with ON DELETE SET NULL
Run from the backend/ directory:
    python migrate_fk_cascade.py
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:abc@localhost:5432/postgres")

# Parse the URL manually for psycopg2
# e.g. postgresql://user:pass@host:port/dbname
import re
m = re.match(r"postgresql://([^:]+):([^@]+)@([^:/]+):(\d+)/(.+)", DATABASE_URL)
if not m:
    raise ValueError("Cannot parse DATABASE_URL: " + DATABASE_URL)

user, password, host, port, dbname = m.groups()

conn = psycopg2.connect(
    dbname=dbname, user=user, password=password, host=host, port=int(port)
)
conn.autocommit = True
cur = conn.cursor()

def get_fk_name(table, column):
    """Look up the actual constraint name from information_schema."""
    cur.execute("""
        SELECT tc.constraint_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_name = %s
          AND kcu.column_name = %s
          AND tc.table_schema = 'public'
    """, (table, column))
    row = cur.fetchone()
    return row[0] if row else None

migrations = [
    # (table, column, referenced_table, referenced_column)
    ("eligibility_checks", "patient_id", "patients", "id"),
    ("eligibility_checks", "trial_id",   "trials",   "id"),
    ("audit_logs",         "check_id",   "eligibility_checks", "id"),
]

for table, column, ref_table, ref_col in migrations:
    new_name = "fk_{0}_{1}_set_null".format(table, column)

    # Skip if already migrated
    cur.execute("""
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = %s AND table_schema = 'public'
    """, (new_name,))
    if cur.fetchone():
        print("  SKIP: {0} already exists on {1}.{2}".format(new_name, table, column))
        continue

    fk_name = get_fk_name(table, column)
    if fk_name:
        print("  Dropping  {0} on {1}.{2} ...".format(fk_name, table, column))
        cur.execute('ALTER TABLE "{0}" DROP CONSTRAINT "{1}"'.format(table, fk_name))
    else:
        print("  No existing FK found for {0}.{1} -- skipping drop.".format(table, column))

    print("  Adding    {0} ({1}.{2} -> {3}.{4} ON DELETE SET NULL) ...".format(
        new_name, table, column, ref_table, ref_col))
    cur.execute("""
        ALTER TABLE "{table}"
        ADD CONSTRAINT "{name}"
        FOREIGN KEY ("{col}") REFERENCES "{rtable}" ("{rcol}")
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED
    """.format(table=table, name=new_name, col=column, rtable=ref_table, rcol=ref_col))
    print("  [OK] Done.\n")

cur.close()
conn.close()
print("Migration complete! Restart the backend server.")
