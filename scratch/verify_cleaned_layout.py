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
    
    # Wait for Chat view greeting to load
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Hello! I')]"))
    )
    print("[OK] Split layout with chat loaded successfully.")
    
    os.makedirs("scratch/screenshots", exist_ok=True)
    driver.save_screenshot("scratch/screenshots/shopai_home.png")
    print("[OK] Saved shopai_home.png.")

    # Locate side bar buttons and click All Products
    print("[3] Switching to All Products tab...")
    products_btn = driver.find_element(By.XPATH, "//button[contains(., 'All Products')]")
    products_btn.click()
    time.sleep(4)
    
    driver.save_screenshot("scratch/screenshots/shopai_catalog.png")
    print("[OK] Saved shopai_catalog.png.")

finally:
    driver.quit()
    print("[DONE] Layout verification finished.")
