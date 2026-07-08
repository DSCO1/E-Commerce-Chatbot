"""Heal database image URLs by scraping correct large product images and updating existing thumbnails/recommendations"""
from selenium import webdriver
from bs4 import BeautifulSoup
import sqlite3
import time
import os

db_path = "app/db.sqlite"
exclude_sizes = ['/70/70/', '/80/80/', '/160/210/', '/120/120/', '/120/150/', '/40/40/', '/48/48/', '/30/30/', '/24/24/', '/10/10/']

def get_pending_products():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Find products without images or with small thumbnail sizes that need correction
    c.execute("""
        SELECT product_link, title, image_url FROM product 
    """)
    rows = c.fetchall()
    conn.close()
    
    pending = []
    for link, title, img in rows:
        if not img or not img.startswith('http'):
            pending.append((link, title))
        elif any(sz in img for sz in exclude_sizes):
            pending.append((link, title))
    return pending

def update_product_image(link, image_url):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("UPDATE product SET image_url = ? WHERE product_link = ?", (image_url, link))
    conn.commit()
    conn.close()

def main():
    pending = get_pending_products()
    print(f"Found {len(pending)} products needing image healing/corrections.")
    if not pending:
        print("All products have correct large image URLs. Database is healthy!")
        return

    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    print("Launching Selenium driver...")
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    success_count = 0
    try:
        for idx, (link, title) in enumerate(pending):
            print(f"[{idx+1}/{len(pending)}] Healing: {title[:50]}...")
            try:
                driver.get(link)
                time.sleep(3.5)
                
                page_soup = BeautifulSoup(driver.page_source, 'lxml')
                image_url = ''
                
                # Check specific product detail selectors first
                for selector in ['img._0DkuPH', 'img.DByoR4', 'img.jzoB4e', 'img.UHDDFP', 'img._53u2j-']:
                    el = page_soup.select_one(selector)
                    if el and el.get('src') and 'logo' not in el.get('src', '').lower():
                        src = el.get('src')
                        if not any(sz in src for sz in exclude_sizes):
                            image_url = src
                            break
                
                # Fallback to scanning all img tags, filtering out thumbnails/recommendations
                if not image_url:
                    for img in page_soup.find_all('img'):
                        src = img.get('src', '')
                        if ('rukminim2.flixcart.com/image/' in src or 'rukminim1.flixcart.com/image/' in src or '/xif0q/' in src) and 'logo' not in src.lower() and 'promo' not in src.lower():
                            if not any(sz in src for sz in exclude_sizes):
                                image_url = src
                                break
                            
                if image_url:
                    update_product_image(link, image_url)
                    success_count += 1
                    print(f"  [OK] Saved large image: {image_url[:80]}...")
                else:
                    print("  [WARN] No primary image found on page.")
                    
            except Exception as e:
                print(f"  [ERROR] Failed to heal: {e}")
                time.sleep(5)
                
    finally:
        driver.quit()
        print(f"\nFinished healing run. Successfully updated {success_count} product images.")

if __name__ == "__main__":
    main()
