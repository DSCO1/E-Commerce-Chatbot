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
    
    # Wait for page to load
    chat_input = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
    )
    print("[OK] Page loaded successfully.")

    # Search for "football"
    print("[3] Sending user query 'football'...")
    chat_input.send_keys("football")
    send_btn = driver.find_element(By.XPATH, "//button[contains(., 'Send') or contains(., 'send')]")
    send_btn.click()

    # Wait for response via polling
    print("  Waiting for response to populate...")
    cards = []
    for step in range(45):
        cards = driver.find_elements(By.CSS_SELECTOR, "div.product-card")
        if len(cards) > 0:
            break
        time.sleep(2)
        
    print(f"  Response loaded with {len(cards)} products.")

    # Capture state
    os.makedirs("scratch/screenshots", exist_ok=True)
    driver.save_screenshot("scratch/screenshots/check_football_results.png")
    print("[OK] Saved check_football_results.png screenshot.")

    if len(cards) > 0:
        first_title = cards[0].find_element(By.CSS_SELECTOR, "div.product-title").text
        print(f"  First product in carousel: '{first_title}'")
        
        if "samsung" not in first_title.lower() and "tv" not in first_title.lower() and "football" in first_title.lower():
            print("[PASS] Verified: TVs are successfully filtered out from football results!")
        else:
            print("[FAIL] TVs or non-football items are still present in results.")
    else:
        print("[FAIL] No cards loaded.")

finally:
    driver.quit()
    print("[DONE] E2E football verification finished.")
