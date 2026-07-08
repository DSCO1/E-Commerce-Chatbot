import sqlite3

conn = sqlite3.connect('app/db.sqlite')
c = conn.cursor()
c.execute("SELECT title, product_link FROM product WHERE title LIKE '%football%' OR title LIKE '%soccer%'")
rows = c.fetchall()
print(f"Total matching titles: {len(rows)}")
for idx, r in enumerate(rows):
    print(f"{idx}: {r[0]} | {r[1]}")
conn.close()
