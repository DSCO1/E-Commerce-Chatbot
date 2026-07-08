"""Diagnostic: fetch a real Flipkart product page and print all image tags and their attributes to see how to scrape the actual product image."""
from selenium import webdriver
from bs4 import BeautifulSoup
import time

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=options)

# Let's check a product link. Let's fetch one from our database.
import sqlite3
conn = sqlite3.connect('app/db.sqlite')
c = conn.cursor()
c.execute("SELECT product_link FROM product WHERE product_link LIKE '%flipkart.com%' LIMIT 1")
row = c.fetchone()
conn.close()

test_url = row[0] if row else "https://www.flipkart.com/orient-electric-46-l-room-personal-air-cooler/p/itmd45053f3e6912"
print(f"Fetching: {test_url}")

try:
    driver.get(test_url)
    time.sleep(5)
    
    soup = BeautifulSoup(driver.page_source, 'lxml')
    
    # Let's find all img tags
    imgs = soup.find_all('img')
    print(f"Total img tags found: {len(imgs)}")
    
    # Filter for larger images or images that seem to be the main product image
    for idx, img in enumerate(imgs):
        src = img.get('src', '')
        srcset = img.get('srcset', '')
        alt = img.get('alt', '')
        classes = img.get('class', [])
        # Only print images that look relevant
        if 'logo' not in src.lower() and ('plus' not in src.lower()) and len(src) > 5:
            print(f"\n[IMG {idx}]")
            print(f"  class: {classes}")
            print(f"  src: {src[:120]}")
            if srcset:
                print(f"  srcset: {srcset[:120]}")
            if alt:
                print(f"  alt: {alt}")

finally:
    driver.quit()
