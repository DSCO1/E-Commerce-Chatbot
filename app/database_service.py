import sqlite3
import os
import shutil
import tempfile
from pathlib import Path

def get_db_path() -> Path:
    """Resolve database path, falling back to temp directory if local path is read-only."""
    local_path = Path(__file__).parent / "db.sqlite"
    try:
        # Test if local folder is writable
        test_file = local_path.parent / ".write_test"
        test_file.touch()
        test_file.unlink()
        return local_path
    except (IOError, PermissionError):
        # Local folder is read-only. Fall back to temp folder.
        temp_path = Path(tempfile.gettempdir()) / "db.sqlite"
        if not temp_path.exists() and local_path.exists():
            try:
                shutil.copy2(local_path, temp_path)
            except Exception as e:
                print(f"[DB-FALLBACK] Failed to copy database to temp directory: {e}")
        return temp_path

db_path = get_db_path()

def get_connection():
    """Return a connection to the SQLite database."""
    return sqlite3.connect(db_path)

def init_db():
    """Initialize the database schema for products and categories."""
    conn = get_connection()
    cursor = conn.cursor()

    # Create category table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS category (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            icon TEXT,
            image TEXT,
            product_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create product table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT UNIQUE NOT NULL,
            product_link TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            brand TEXT,
            category_id INTEGER,
            category_name TEXT,
            confidence_score REAL,
            classification_source TEXT,
            price INTEGER,
            discount REAL,
            avg_rating REAL,
            rating REAL,
            total_ratings INTEGER,
            availability TEXT,
            image TEXT,
            image_url TEXT,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES category(id)
        )
    """)

    # Index for speed
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_category_id ON product(category_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_link ON product(product_link)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_id ON product(product_id)")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
