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

    # Search for "laptops"
    print("[3] Sending user query 'laptops'...")
    chat_input.send_keys("laptops")
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

    # Capture state before deletion
    os.makedirs("scratch/screenshots", exist_ok=True)
    driver.save_screenshot("scratch/screenshots/chat_before_delete.png")
    print("[OK] Saved chat_before_delete.png screenshot.")

    # Find all delete buttons
    del_buttons = driver.find_elements(By.XPATH, "//button[contains(., '🗑️')]")
    print(f"  Found {len(del_buttons)} delete buttons.")

    if len(del_buttons) > 0:
        print("[4] Clicking the first delete button to remove the message...")
        del_buttons[0].click()
        time.sleep(5)
        
        # Verify that number of delete buttons has decreased or text is gone
        new_del_buttons = driver.find_elements(By.XPATH, "//button[contains(., '🗑️')]")
        print(f"  Now found {len(new_del_buttons)} delete buttons.")
        
        driver.save_screenshot("scratch/screenshots/chat_after_delete.png")
        print("[OK] Saved chat_after_delete.png screenshot.")
        
        if len(new_del_buttons) < len(del_buttons):
            print("[PASS] Message was successfully deleted!")
        else:
            print("[FAIL] Message count did not decrease after clicking delete button.")
    else:
        print("[FAIL] No delete buttons found on screen.")

finally:
    driver.quit()
    print("[DONE] E2E delete test finished.")
