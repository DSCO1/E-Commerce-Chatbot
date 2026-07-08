import os
import shutil
import sqlite3
from pathlib import Path

# Add project root directory to Python path if run directly
import sys
sys.path.append(str(Path(__file__).parent))

from database_service import init_db, get_connection, db_path
from category_classifier import CategoryClassifier
from category_normalizer import CategoryNormalizer
from category_manager import CategoryManager
from duplicate_detector import DuplicateDetector
from product_repository import ProductRepository

def run_migration():
    print("=" * 60)
    print("STARTING DATABASE SCHEMA MIGRATION & RECLASSIFICATION")
    print("=" * 60)
    
    # 1. Check if DB exists
    if not db_path.exists():
        print(f"[WARN] Database does not exist at {db_path}. Initializing empty schema.")
        init_db()
        print("[SUCCESS] Initialized empty schema.")
        return

    # 2. Backup database
    backup_path = db_path.with_name("db.sqlite.backup")
    print(f"[BACKUP] Copying {db_path} -> {backup_path}")
    shutil.copyfile(db_path, backup_path)

    # Connect
    conn = get_connection()
    cursor = conn.cursor()

    # 3. Check if table 'product' exists and if it is the old schema
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product'")
    product_exists = cursor.fetchone()

    if not product_exists:
        print("[INFO] No 'product' table found. Initializing schema.")
        conn.close()
        init_db()
        return

    # Check if 'product_id' is already in 'product' table
    cursor.execute("PRAGMA table_info(product)")
    columns = [col[1] for col in cursor.fetchall()]
    
    is_old_schema = 'product_id' not in columns

    if is_old_schema:
        print("[INFO] Old database schema detected. Performing migration.")
        
        # Rename old table to product_old
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product_old'")
        if cursor.fetchone():
            cursor.execute("DROP TABLE product_old")
            
        cursor.execute("ALTER TABLE product RENAME TO product_old")
        conn.commit()
        conn.close()
        
        # Initialize new tables
        print("[SCHEMA] Creating new 'product' and 'category' tables...")
        init_db()
        
        # Re-open connection
        conn = get_connection()
        cursor = conn.cursor()
        
        # Read old products
        cursor.execute("""
            SELECT product_link, title, brand, price, discount, avg_rating, total_ratings, image_url 
            FROM product_old
        """)
        old_rows = cursor.fetchall()
        print(f"[MIGRATION] Read {len(old_rows)} products from old schema to migrate.")
    else:
        # Schema is already new. We'll read existing products, reclassify them, and update them.
        cursor.execute("""
            SELECT product_link, title, brand, price, discount, avg_rating, total_ratings, image_url
            FROM product
        """)
        old_rows = cursor.fetchall()
        print(f"[MIGRATION] New schema already present. Re-evaluating classification for {len(old_rows)} products.")
        conn.close()
        init_db()
        conn = get_connection()
        cursor = conn.cursor()

    # Initialize components
    classifier = CategoryClassifier()
    category_manager = CategoryManager(get_connection)
    product_repository = ProductRepository(get_connection)

    # Classify and migrate products
    success_count = 0
    reclassified_log = []
    
    for row in old_rows:
        link, title, brand, price, discount, avg_rating, total_ratings, image_url = row
        
        # Extract product ID
        product_id = DuplicateDetector.extract_product_id(link, title)
        
        # Build product data structure
        product_data = {
            "product_id": product_id,
            "product_link": link,
            "title": title,
            "brand": brand or "Generic",
            "price": price or 0,
            "discount": discount or 0.0,
            "avg_rating": avg_rating or 0.0,
            "total_ratings": total_ratings or 0,
            "image": image_url or "",
            "image_url": image_url or "",
            "description": title,  # Fallback
            "availability": "In Stock"
        }
        
        # Run classification
        category_name, confidence, source, reason = classifier.classify(product_data)
        normalized_cat = CategoryNormalizer.normalize(category_name)
        
        # Ensure category exists in new category table
        category_id, slug = category_manager.get_or_create_category(normalized_cat)
        
        product_data["category_id"] = category_id
        product_data["category_name"] = normalized_cat
        product_data["confidence_score"] = confidence
        product_data["classification_source"] = source
        
        # Save product to the new schema
        product_repository.save_product(product_data)
        success_count += 1
        
        reclassified_log.append(f"Product: {title[:40]} -> {normalized_cat} ({confidence*100:.1f}%)")

    # Recalculate dynamic counts
    print("[MIGRATION] Recalculating category product counts...")
    category_manager.recalculate_all_counts()

    # Clean up old table
    if is_old_schema:
        print("[CLEANUP] Dropping temporary 'product_old' table...")
        cursor.execute("DROP TABLE product_old")
        conn.commit()

    conn.close()
    
    print("=" * 60)
    print(f"[SUCCESS] Migration completed! Successfully processed {success_count} products.")
    print("=" * 60)

if __name__ == "__main__":
    run_migration()
