from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

print("[1] Launching Chrome...")
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=2880,1600")

driver = webdriver.Chrome(options=options)
try:
    print("[2] Opening localhost:8501...")
    driver.get("http://localhost:8501")
    
    # Wait for Scraper page elements to load
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Flipkart Live Scraper Engine')]"))
    )
    print("[OK] Scraper dashboard loaded.")

    # Find the search term input field
    # Locate the label first and find the input underneath
    print("[3] Locating keyword input field...")
    keyword_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[contains(@aria-label, 'Search Term / Keywords:')]"))
    )
    
    # Clear and type a new keyword e.g. "pendrive"
    print("[4] Entering new search term 'pendrive'...")
    keyword_input.send_keys(Keys.CONTROL + "a")
    keyword_input.send_keys(Keys.BACKSPACE)
    keyword_input.send_keys("pendrive")
    keyword_input.send_keys(Keys.ENTER)
    time.sleep(2)
    
    # Click start scraping button
    print("[5] Clicking 'Start Web Scraping Session'...")
    start_btn = driver.find_element(By.XPATH, "//button[contains(., 'Start Web Scraping Session')]")
    start_btn.click()
    
    print("[6] Waiting for scrape to finish (this might take 15-20 seconds)...")
    # Wait for status/toast completion or the page to reload
    # We can wait for the toast "Scraped" to appear, or check for "Success!" status
    WebDriverWait(driver, 45).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Success!') or contains(text(), 'scraped and loaded')]"))
    )
    print("[OK] Scraper successfully executed.")
    
    # Wait another second for grid to reload
    time.sleep(3)
    
    # Take screenshot of the new scraped results in the grid
    os.makedirs("scratch/screenshots", exist_ok=True)
    driver.save_screenshot("scratch/screenshots/scraper_after_scrape.png")
    print("[OK] Saved scraper_after_scrape.png.")

finally:
    driver.quit()
    print("[DONE] Action verification finished.")
