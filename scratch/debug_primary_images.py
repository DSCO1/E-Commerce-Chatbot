"""Diagnostic: fetch a Flipkart product page (pen drive or speaker) and find how to uniquely locate the primary product image vs recommendations."""
from selenium import webdriver
from bs4 import BeautifulSoup
import time

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=options)

# Let's try two URLs: a speaker and a pen drive
urls = {
    "speaker": "https://www.flipkart.com/buy-fx1-a100-dynamic-thunder-sound-acoustic-performance-wired-speaker/p/itmd45053f3e6912",
    "pendrive": "https://www.flipkart.com/samsung-muf-64da-apc-64-gb-utility-pendrive/p/itmd45053f3e6912"
}

# Wait! Let's get the real URLs from our database.
import sqlite3
conn = sqlite3.connect('app/db.sqlite')
c = conn.cursor()
c.execute("SELECT product_link, title FROM product WHERE title LIKE '%Pen Drive%' OR title LIKE '%Thunder Sound%' LIMIT 5")
rows = c.fetchall()
conn.close()

print(f"Found {len(rows)} real database matching rows:")
for r in rows:
    print(f"  Title: {r[1]} | Link: {r[0]}")

test_links = [r[0] for r in rows] if rows else [
    "https://www.flipkart.com/samsung-muf-64da-apc-64-gb-utility-pendrive/p/itmf4b7f8df8ffc8"
]

try:
    for link in test_links:
        print(f"\nFetching: {link}")
        driver.get(link)
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'lxml')
        
        print("All img tags with class/parent information:")
        for idx, img in enumerate(soup.find_all('img')):
            src = img.get('src', '')
            alt = img.get('alt', '')
            classes = img.get('class', [])
            parent_classes = img.parent.get('class', []) if img.parent else []
            
            if ('rukminim2.flixcart.com' in src or 'rukminim1.flixcart.com' in src or 'xif0q' in src) and 'logo' not in src.lower():
                print(f"  [{idx}] src: {src[:80]} | alt: '{alt}' | class: {classes} | parent class: {parent_classes}")

finally:
    driver.quit()
