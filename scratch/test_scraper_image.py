"""Verify advanced image selectors excluding thumbnails and recommendations on multiple categories"""
from selenium import webdriver
from bs4 import BeautifulSoup
import time

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=options)

test_links = [
    "https://www.flipkart.com/orient-electric-46-l-room-personal-air-cooler/p/itmf2qcfu7ty86p8",
    "https://www.flipkart.com/f-ferons-tg-113-ultra-3d-dynamic-thunder-sound-high-bass-wireless-portable-9-w-bluetooth-speaker/p/itm8b84e5f98ca43",
    "https://www.flipkart.com/samsung-muf-64da-apc-64-gb-utility-pendrive/p/itmf4b7f8df8ffc8"
]

def extract_image(url):
    print(f"\nFetching: {url}")
    try:
        driver.get(url)
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'lxml')
        
        exclude_sizes = ['/70/70/', '/80/80/', '/160/210/', '/120/120/', '/120/150/', '/40/40/', '/48/48/', '/30/30/', '/24/24/', '/10/10/']
        
        # 1. Try specific classes
        for selector in ['img._0DkuPH', 'img.DByoR4', 'img.jzoB4e', 'img.UHDDFP', 'img._53u2j-']:
            el = soup.select_one(selector)
            if el and el.get('src') and 'logo' not in el.get('src', '').lower():
                src = el.get('src')
                if not any(sz in src for sz in exclude_sizes):
                    print(f"  Matched selector '{selector}': {src}")
                    return src
                    
        # 2. Try scanning all img tags, filtering out thumbnails/recommendations
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if ('rukminim2.flixcart.com/image/' in src or 'rukminim1.flixcart.com/image/' in src or '/xif0q/' in src) and 'logo' not in src.lower() and 'promo' not in src.lower():
                if not any(sz in src for sz in exclude_sizes):
                    print(f"  Matched primary fallback: {src}")
                    return src
                    
        print("  No product image found.")
        return ''
    except Exception as e:
        print(f"  Error: {e}")
        return ''

try:
    for url in test_links:
        extract_image(url)
finally:
    driver.quit()
