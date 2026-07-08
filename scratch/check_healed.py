import sqlite3
conn = sqlite3.connect('app/db.sqlite')
c = conn.cursor()
c.execute("SELECT count(image_url) FROM product WHERE image_url LIKE 'http%'")
print('Healed count:', c.fetchone()[0])
conn.close()
