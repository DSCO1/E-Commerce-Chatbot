"""Check: does 'samsung' appear in BOTH brand and title for all Samsung phones?"""
import sqlite3

conn = sqlite3.connect('app/db.sqlite')
c = conn.cursor()

# Samsung phones with samsung in title
c.execute("""
    SELECT brand, title, price FROM product 
    WHERE brand LIKE '%Samsung%' AND price < 20000 
    AND (title LIKE '%phone%' OR title LIKE '%galaxy%' OR title LIKE '%5g%' OR title LIKE '%gb storage%')
    AND title LIKE '%samsung%'
""")
r1 = c.fetchall()
print(f"Samsung in brand AND title: {len(r1)} rows")

# Samsung phones WITHOUT samsung in title
c.execute("""
    SELECT brand, title, price FROM product 
    WHERE brand LIKE '%Samsung%' AND price < 20000 
    AND (title LIKE '%phone%' OR title LIKE '%galaxy%' OR title LIKE '%5g%' OR title LIKE '%gb storage%')
    AND title NOT LIKE '%samsung%'
""")
r2 = c.fetchall()
print(f"Samsung in brand but NOT title: {len(r2)} rows")
for r in r2[:5]:
    print(f"  brand={r[0]} | title={r[1][:80]} | price={r[2]}")

# What does the LLM-generated query return?
print("\n--- Testing generated query ---")
c.execute("""
    SELECT brand, title, price FROM product
    WHERE (title LIKE '%phone%' OR title LIKE '%smartphone%' OR title LIKE '%mobile%' 
           OR title LIKE '%galaxy%' OR title LIKE '%iphone%' OR title LIKE '%5g%' OR title LIKE '%gb storage%') 
    AND title LIKE '%samsung%' AND price < 20000
    AND title NOT LIKE '%laptop%' AND title NOT LIKE '%chromebook%' AND title NOT LIKE '%notebook%' 
    AND title NOT LIKE '%case%' AND title NOT LIKE '%cover%' AND title NOT LIKE '%adapter%'
""")
r3 = c.fetchall()
print(f"LLM-generated query returns: {len(r3)} rows")
for r in r3[:5]:
    print(f"  {r[0]} | {r[1][:80]} | Rs.{r[2]}")

# What does the brand column version return?
c.execute("""
    SELECT brand, title, price FROM product
    WHERE (title LIKE '%phone%' OR title LIKE '%smartphone%' OR title LIKE '%mobile%' 
           OR title LIKE '%galaxy%' OR title LIKE '%iphone%' OR title LIKE '%5g%' OR title LIKE '%gb storage%') 
    AND brand LIKE '%samsung%' AND price < 20000
    AND title NOT LIKE '%laptop%' AND title NOT LIKE '%chromebook%' AND title NOT LIKE '%notebook%' 
    AND title NOT LIKE '%case%' AND title NOT LIKE '%cover%' AND title NOT LIKE '%adapter%'
""")
r4 = c.fetchall()
print(f"\nUsing brand column instead: {len(r4)} rows")
for r in r4[:5]:
    print(f"  {r[0]} | {r[1][:80]} | Rs.{r[2]}")

conn.close()
