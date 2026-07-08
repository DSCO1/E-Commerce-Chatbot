import sqlite3
conn = sqlite3.connect('app/db.sqlite')
c = conn.cursor()
c.execute("SELECT title, image_url FROM product WHERE title LIKE '%Pen Drive%' OR title LIKE '%MUF-64DA%'")
for r in c.fetchall():
    print(f"Title: {r[0][:60]}... | Image: {r[1][:80] if r[1] else 'None'}")
conn.close()
