from selenium import webdriver
from selenium.webdriver.common.by import By
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
    print("[OK] Scraper dashboard loaded successfully.")
    
    os.makedirs("scratch/screenshots", exist_ok=True)
    driver.save_screenshot("scratch/screenshots/scraper_home.png")
    print("[OK] Saved scraper_home.png.")

    # Find sidebar buttons
    # In Streamlit, buttons are rendered inside divs.
    print("[3] Switching to Chat Agent tab...")
    chat_btn = driver.find_element(By.XPATH, "//button[contains(., 'Chat Agent')]")
    chat_btn.click()
    time.sleep(4)
    
    driver.save_screenshot("scratch/screenshots/chat_home.png")
    print("[OK] Saved chat_home.png.")

    print("[4] Switching to All Products tab...")
    products_btn = driver.find_element(By.XPATH, "//button[contains(., 'All Products')]")
    products_btn.click()
    time.sleep(4)
    
    driver.save_screenshot("scratch/screenshots/catalog_home.png")
    print("[OK] Saved catalog_home.png.")

finally:
    driver.quit()
    print("[DONE] Sidebar layouts verification finished.")
