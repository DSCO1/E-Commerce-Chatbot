import sqlite3
conn = sqlite3.connect('app/db.sqlite')
c = conn.cursor()
c.execute("SELECT product_link, title, image_url FROM product WHERE title LIKE '%Pen Drive%' OR title LIKE '%MUF-64DA%' OR title LIKE '%Thunder Sound%' LIMIT 5")
for r in c.fetchall():
    print(f"Title: {r[1]} | Image: {r[2]} | Link: {r[0]}")
conn.close()
