"""Verify and screenshot what the driver sees when fetching the Flipkart product page."""
from selenium import webdriver
from bs4 import BeautifulSoup
import time, os

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=options)

test_url = "https://www.flipkart.com/orient-electric-46-l-room-personal-air-cooler/p/itmd45053f3e6912"

try:
    driver.get(test_url)
    time.sleep(5)
    
    # Save a screenshot to inspect visually
    os.makedirs("scratch/screenshots", exist_ok=True)
    driver.save_screenshot("scratch/screenshots/debug_detail_page.png")
    
    soup = BeautifulSoup(driver.page_source, 'lxml')
    imgs = soup.find_all('img')
    print(f"Total images: {len(imgs)}")
    for idx, img in enumerate(imgs[:10]):
        print(f"  [{idx}] src: {img.get('src', '')[:80]} | alt: {img.get('alt', '')} | class: {img.get('class', [])}")

finally:
    driver.quit()
