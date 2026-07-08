import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "app" / "db.sqlite"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]
print("Tables in database:", tables)

for table in tables:
    print(f"\nSchema for table: {table}")
    cursor.execute(f"PRAGMA table_info({table})")
    for col in cursor.fetchall():
        print(f"  Column: {col[1]} ({col[2]})")

    # Get sample data
    cursor.execute(f"SELECT * FROM {table} LIMIT 2")
    print("  Sample rows:")
    for row in cursor.fetchall():
        print("   ", row)

conn.close()
