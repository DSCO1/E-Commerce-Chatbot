"""Selenium test: send a query to the Streamlit chatbot and capture the response."""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, os

SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(options=options)

try:
    print("[1] Loading Streamlit app (waiting 20s)...")
    driver.get("http://localhost:8501")
    time.sleep(20)  # Give Streamlit plenty of time to start

    # Take initial screenshot to see state
    driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "initial_state.png"))
    print(f"  Page title: {driver.title}")

    # Try to find chat input with longer timeout
    print("[2] Looking for chat input (timeout 30s)...")
    chat_input = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
    )
    print("  Found chat input!")

    # Type query
    print("[3] Typing query...")
    chat_input.click()
    time.sleep(0.5)
    chat_input.send_keys("show me smart phone under 20000 rupee of samsung brand")
    time.sleep(0.5)
    chat_input.send_keys(Keys.RETURN)

    # Wait for response by polling
    print("[4] Waiting for response (polling up to 120s)...")
    for i in range(24):  # 24 * 5 = 120 seconds
        time.sleep(5)
        messages = driver.find_elements(By.CSS_SELECTOR, "[data-testid='stChatMessage']")
        if len(messages) >= 2:
            last_text = messages[-1].text.strip()
            if last_text and len(last_text) > 10:
                print(f"  Response detected after {(i+1)*5}s")
                break
        print(f"  ...waiting ({(i+1)*5}s, {len(messages)} messages)")

    time.sleep(2)

    # Screenshot
    screenshot_path = os.path.join(SCREENSHOT_DIR, "samsung_phone_result.png")
    driver.save_screenshot(screenshot_path)
    print(f"[5] Screenshot saved: {screenshot_path}")

    # Extract all messages
    messages = driver.find_elements(By.CSS_SELECTOR, "[data-testid='stChatMessage']")
    print(f"\n[INFO] Total messages: {len(messages)}")
    for idx, msg in enumerate(messages):
        text = msg.text.strip()
        print(f"\n--- Message {idx+1} ---")
        print(text[:800] if text else "(empty)")

finally:
    driver.quit()
    print("\n[DONE]")
