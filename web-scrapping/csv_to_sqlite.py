import pandas as pd
import sqlite3
from pathlib import Path

# Database and CSV file paths resolved relative to this script
base_dir = Path(__file__).parent
db_path = base_dir.parent / 'app' / 'db.sqlite'
# Use the larger pre-scraped dataset if available, otherwise fallback to the live scrape CSV
final_csv = base_dir.parent / 'app' / 'Resources' / 'ecommerce_data_final.csv'
csv_path = final_csv if final_csv.exists() else base_dir / 'flipkart_product_data.csv'

# Connect to SQLite database (creates one if not exists)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create the product table if it does not exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS product (
    product_link TEXT,
    title TEXT,
    brand TEXT,
    price INTEGER,
    discount FLOAT,
    avg_rating FLOAT,
    total_ratings INTEGER
);
''')

# Commit the table creation
conn.commit()

# Read CSV file using pandas
df = pd.read_csv(csv_path)

# Clear existing rows to prevent duplicates/bad rows on rerun
cursor.execute("DELETE FROM product")
conn.commit()

# Strip whitespace from text columns to ensure query matches work correctly
for col in ['brand', 'title']:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()

# Insert data into the product table
df.to_sql('product', conn, if_exists='append', index=False)

# Close the connection
conn.close()

print("Data inserted successfully!")
