import sqlite3

db_path = r"c:\Users\Ujjaw\OneDrive\Documents\E-commerce chatbot\app\db.sqlite"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for table_tuple in tables:
        table = table_tuple[0]
        cursor.execute(f"PRAGMA table_info({table});")
        columns = [col[1] for col in cursor.fetchall()]
        
        cursor.execute(f"SELECT * FROM {table};")
        rows = cursor.fetchall()
        for r_idx, row in enumerate(rows):
            for c_idx, val in enumerate(row):
                if val and isinstance(val, str) and ("onload" in val.lower() or "onerror" in val.lower()):
                    print(f"Table {table}, Row {r_idx}, Col {columns[c_idx]}: {val}")
                    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
