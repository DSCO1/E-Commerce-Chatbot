"""Print all images on the Samsung pendrive detail page to see why it matched no images."""
from selenium import webdriver
from bs4 import BeautifulSoup
import time

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=options)

test_url = "https://www.flipkart.com/samsung-muf-64da-apc-64-gb-utility-pendrive/p/itmf4b7f8df8ffc8"

try:
    driver.get(test_url)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    print("All image tags:")
    for idx, img in enumerate(soup.find_all('img')):
        src = img.get('src', '')
        alt = img.get('alt', '')
        print(f"  [{idx}] src: {src[:90]} | alt: '{alt}'")
finally:
    driver.quit()
