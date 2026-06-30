"""Consolidated database seeding, diagnostics, and catalog inspection utilities.

Combines functionality from:
- seed_db.py
- count_products.py
- check_gaming.py
- inspect_csv.py
- list_all_keywords.py
"""

import sys
import sqlite3
import pandas as pd
import re
from pathlib import Path
from collections import Counter

# Add project root directory to Python path
sys.path.append(str(Path(__file__).parent.parent / "app"))
from sql import scrape_and_populate_db

base_dir = Path(__file__).parent.parent
db_path = base_dir / "app" / "db.sqlite"
csv_path = base_dir / "app" / "Resources" / "ecommerce_data_final.csv"

def seed_database():
    print("=" * 60)
    print("SEEDING DATABASE SCHEMA AND REFRESHING DATA")
    print("=" * 60)
    print("Connecting to DB at:", db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Ensure table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product (
            product_link TEXT UNIQUE,
            title TEXT,
            brand TEXT,
            price INTEGER,
            discount REAL,
            avg_rating REAL,
            total_ratings INTEGER
        )
    """)
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM product")
    row_count = cursor.fetchone()[0]
    
    if row_count == 0 and csv_path.exists():
        print("Database is empty. Seeding initial products from CSV...")
        df = pd.read_csv(csv_path)
        for col in ['brand', 'title']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        df = df.drop_duplicates(subset=['product_link'])
        df.to_sql('product', conn, if_exists='append', index=False)
        print(f"Loaded {len(df)} products from CSV.")
    else:
        print(f"Database table exists. Current count: {row_count} rows.")
        
    conn.close()

    # Seed list of core categories from live scraper
    categories = [
        "watches",
        "cooler",
        "ac",
        "laptop",
        "fan",
        "fridge",
        "washing machine"
    ]
    print("\nStarting live scraper populate for core categories (5 products each)...")
    for category in categories:
        print(f"---> Scraping '{category}'")
        try:
            num = scrape_and_populate_db(category, limit=5)
            print(f"  [SUCCESS] Populated {num} products for '{category}'")
        except Exception as e:
            print(f"  [ERROR] Scraping failed: {e}")
            
    print("\nDatabase refresh and seeding complete!")
    print()

def inspect_catalog_counts():
    print("=" * 60)
    print("LOCAL SQLITE CATALOG COUNTS")
    print("=" * 60)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    categories = {
        "Washing Machines": "title LIKE '%washing%'",
        "Air Conditioners / AC": "title LIKE '%AC%' OR title LIKE '%conditioner%'",
        "Refrigerators": "title LIKE '%refrigerator%' OR title LIKE '%fridge%'",
        "Laptops": "title LIKE '%laptop%'",
        "Watches": "title LIKE '%watch%'"
    }
    
    c.execute("SELECT COUNT(*) FROM product")
    total = c.fetchone()[0]
    print(f"Total catalog products: {total}")
    
    for cat_name, condition in categories.items():
        c.execute(f"SELECT COUNT(*) FROM product WHERE {condition}")
        count = c.fetchone()[0]
        print(f"  - {cat_name}: {count}")
    conn.close()
    print()

def search_by_keyword(keyword):
    print("=" * 60)
    print(f"SEARCH DATABASE FOR '{keyword}'")
    print("=" * 60)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute(
        "SELECT brand, title, price, avg_rating FROM product WHERE title LIKE ?",
        (f"%{keyword}%",)
    )
    rows = c.fetchall()
    print(f"Found {len(rows)} matching products:")
    for row in rows[:15]:
        print(f"  {row[0]} | {row[1][:65]}... | Rs.{row[2]} | Rating: {row[3]}")
    if len(rows) > 15:
        print(f"  ... and {len(rows)-15} more products.")
    conn.close()
    print()

def inspect_csv_counts():
    print("=" * 60)
    print("ORIGINAL CSV FILE COUNTS")
    print("=" * 60)
    if not csv_path.exists():
        print(f"CSV file not found at: {csv_path}")
        return
        
    df = pd.read_csv(csv_path)
    print(f"Total rows in CSV: {len(df)}")
    keywords = ['watch', 'cooler', 'ac', 'laptop', 'fan', 'fridge', 'refrigerator', 'washing', 'shoes', 'phone', 'air conditioner']
    for kw in keywords:
        count = df['title'].str.contains(kw, case=False, na=False).sum()
        print(f"  - '{kw}': {count} matches")
    print()

def list_common_keywords():
    print("=" * 60)
    print("COMMON NOUNS / KEYWORDS IN PRODUCT TITLES")
    print("=" * 60)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT title FROM product")
    titles = [row[0] for row in c.fetchall()]
    conn.close()
    
    words = []
    for title in titles:
        tokens = re.findall(r'[a-zA-Z]+', title.lower())
        words.extend(tokens)
        
    ignored = {
        'in', 'india', 'price', 'with', 'and', 'for', 'of', 'on', 'at', 'to', 'the', 'under', 'over', 'by', 'from',
        'rs', 'l', 'kg', 'star', 'rating', 'liter', 'liters', 'mm', 'cm', 'v', 'w', 'ah', 'ahp', 'v1', 'g10', 'r100',
        'electric', 'room', 'personal', 'desert', 'window', 'split', 'air', 'cooler', 'coolers', 'refrigerator',
        'refrigerators', 'fridge', 'fridges', 'washing', 'machine', 'machines', 'laptop', 'laptops', 'fan', 'fans',
        'ceiling', 'watch', 'watches', 'smartwatch', 'smartwatches', 'camera', 'cameras', 'trimmer', 'trimmers',
        'orient', 'thomson', 'bajaj', 'sansui', 'kenstar', 'lazer', 'hindware', 'crompton', 'voltas', 'lg', 'samsung',
        'haier', 'hp', 'asus', 'lenovo', 'acer', 'fossil', 'boat', 'noise', 'fire', 'boltt', 'veet', 'beardo', 'bombay',
        'shaving', 'nova', 'bironza', 'zyrian', 'geemy', 'canon', 'dji', 'yash', 'enterprises', 'techio', 'goboult',
        'punnkfunnk', 'polycab', 'maxotech', 'athots', 'gestor', 'stardom', 'digital', 'smartbuy', 'flipkart'
    }
    
    counter = Counter([w for w in words if w not in ignored and len(w) > 2])
    print("Top 40 unique keywords in database titles:")
    for word, count in counter.most_common(40):
        print(f"  {word}: {count}")
    print()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "--seed":
            seed_database()
        elif mode == "--inspect":
            inspect_catalog_counts()
            inspect_csv_counts()
        elif mode == "--keywords":
            list_common_keywords()
        elif mode.startswith("--search="):
            kw = mode.split("=")[1]
            search_by_keyword(kw)
    else:
        # Default behavior: run counts and keywords analysis
        inspect_catalog_counts()
        list_common_keywords()
