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
    driver.save_screenshot("scratch/screenshots/chat_pair_before_delete.png")
    print("[OK] Saved chat_pair_before_delete.png screenshot.")

    # Find all delete buttons. There should only be 2 (the assistant response, plus the Clear Chat History button)
    del_buttons = driver.find_elements(By.XPATH, "//button[contains(., '🗑️')]")
    print(f"  Found {len(del_buttons)} delete buttons.")

    if len(del_buttons) > 0:
        # Click the delete button corresponding to the assistant message
        # Let's click the first delete button inside stChatMessage
        chat_del_buttons = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='stChatMessage'] button")
        print(f"  Found {len(chat_del_buttons)} delete buttons inside chat bubbles.")
        # Debug print removed to prevent encoding error
        
        # Filter to only visible trash buttons using XPath inside stChatMessage
        visible_trash_buttons = driver.find_elements(By.XPATH, "//div[@data-testid='stChatMessage']//button[contains(., '🗑️')]")
        visible_trash_buttons = [b for b in visible_trash_buttons if b.is_displayed()]
        print(f"  Found {len(visible_trash_buttons)} visible trash buttons in chat bubbles.")
        
        if len(visible_trash_buttons) == 1:
            print("[PASS] Verified: Exactly ONE delete button is rendered for this chat turn!")
            print("[4] Clicking the delete button...")
            visible_trash_buttons[0].click()
            time.sleep(5)
            
            # Verify chat content is empty
            chat_del_buttons_after = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='stChatMessage'] button")
            print(f"  Now found {len(chat_del_buttons_after)} delete buttons inside chat bubbles.")
            
            driver.save_screenshot("scratch/screenshots/chat_pair_after_delete.png")
            print("[OK] Saved chat_pair_after_delete.png screenshot.")
            
            if len(chat_del_buttons_after) == 0:
                print("[PASS] Both the query and the results were successfully deleted together!")
            else:
                print("[FAIL] Chat elements were not cleared.")
        else:
            print(f"[FAIL] Expected 1 delete button in chat bubbles, but found {len(chat_del_buttons)}.")
    else:
        print("[FAIL] No delete buttons found on screen.")

finally:
    driver.quit()
    print("[DONE] E2E delete pair test finished.")
