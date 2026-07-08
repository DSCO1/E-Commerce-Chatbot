"""Selenium E2E Verification for ShopAI Dashboard"""
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
    print("[1] Loading ShopAI App on localhost:8501...")
    driver.get("http://localhost:8501")
    time.sleep(15)  # Wait for boot & render
    
    # Save screenshot of initial home state (greeting, suggestion cards)
    screenshot_1 = os.path.join(SCREENSHOT_DIR, "shopai_home.png")
    driver.save_screenshot(screenshot_1)
    print(f"  Home screen screenshot saved: {screenshot_1}")

    # Verify if suggestion buttons/cards exist
    buttons = driver.find_elements(By.CSS_SELECTOR, "button")
    button_texts = [b.text for b in buttons if b.text]
    print(f"  Found buttons count: {len(button_texts)}")

    # Type a query to search for products
    print("[2] Typing search query...")
    chat_input = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
    )
    chat_input.click()
    time.sleep(0.5)
    chat_input.send_keys("trimmer")
    time.sleep(0.5)
    chat_input.send_keys(Keys.RETURN)

    print("[3] Waiting for response and product carousel (up to 40s)...")
    time.sleep(25)  # Wait for SQL query and UI render

    # Save screenshot of search results
    screenshot_2 = os.path.join(SCREENSHOT_DIR, "shopai_search_results.png")
    driver.save_screenshot(screenshot_2)
    print(f"  Search result screenshot saved: {screenshot_2}")

    # Check if custom product cards are present
    product_cards = driver.find_elements(By.CLASS_NAME, "product-card")
    print(f"  Found {len(product_cards)} styled product cards in UI!")
    for idx, card in enumerate(product_cards[:3]):
        print(f"    Card {idx+1} text content: {card.text.encode('ascii', 'ignore').decode('ascii').replace(chr(10), ' | ')}")

finally:
    driver.quit()
    print("\n[DONE] E2E test finished.")
