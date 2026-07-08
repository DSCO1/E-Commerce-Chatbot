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

    # Task 1: Search for "fans"
    print("[3] Searching for 'fans'...")
    chat_input.send_keys("fans")
    send_btn = driver.find_element(By.XPATH, "//button[contains(., 'Send') or contains(., 'send')]")
    send_btn.click()

    # Wait for response via polling
    print("  Waiting for response to populate (polling up to 90s)...")
    cards = []
    for step in range(45):
        cards = driver.find_elements(By.CSS_SELECTOR, "div.product-card")
        if len(cards) > 0:
            break
        time.sleep(2)

    print(f"  Found {len(cards)} cards for 'fans' search.")
    
    coolers_found = []
    for i, c in enumerate(cards):
        text = c.text
        if "cooler" in text.lower() or "room/personal air" in text.lower():
            coolers_found.append(f"Card {i+1}: {text[:60]}")
            
    if coolers_found:
        print(f"[FAIL] Air coolers were found in 'fans' search results:")
        for col in coolers_found:
            print(f"  - {col}")
    else:
        print("[PASS] No air coolers found in 'fans' search results.")

    # Save screenshot
    os.makedirs("scratch/screenshots", exist_ok=True)
    driver.save_screenshot("scratch/screenshots/check_fans_results.png")

    # Clear chat / refresh page for next test
    driver.get("http://localhost:8501")
    chat_input = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
    )

    # Task 2: Search for "laptops"
    print("[4] Searching for 'laptops'...")
    chat_input.send_keys("laptops")
    send_btn = driver.find_element(By.XPATH, "//button[contains(., 'Send') or contains(., 'send')]")
    send_btn.click()

    # Wait for response via polling
    print("  Waiting for response to populate (polling up to 90s)...")
    cards = []
    for step in range(45):
        cards = driver.find_elements(By.CSS_SELECTOR, "div.product-card")
        if len(cards) > 0:
            break
        time.sleep(2)
    
    print(f"  Found {len(cards)} cards for 'laptops' search.")
    
    speakers_found = []
    for i, c in enumerate(cards):
        text = c.text
        if "speaker" in text.lower() or "soundbar" in text.lower():
            speakers_found.append(f"Card {i+1}: {text[:60]}")
            
    if speakers_found:
        print(f"[FAIL] Speakers/soundbars were found in 'laptops' search results:")
        for spk in speakers_found:
            print(f"  - {spk}")
    else:
        print("[PASS] No speakers/soundbars found in 'laptops' search results.")

    driver.save_screenshot("scratch/screenshots/check_laptops_results.png")

finally:
    driver.quit()
    print("[DONE] E2E test finished.")
