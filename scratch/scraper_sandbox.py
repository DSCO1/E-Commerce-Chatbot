"""Consolidated utility script for scraper testing, troubleshooting, and regex checks.

Combines functionality from:
- test_scraper_cameras.py
- debug_scraper.py
"""

import sys
import re
from pathlib import Path

# Add project root directory to Python path
sys.path.append(str(Path(__file__).parent.parent / "app"))
from sql import scrape_and_populate_db

scratch_dir = Path(__file__).parent
page_info_path = scratch_dir / "page_info.txt"

def run_scraper_test(category, limit=5):
    print("=" * 60)
    print(f"SCRAPER SANDBOX: Live scraping for '{category}' (limit: {limit})")
    print("=" * 60)
    try:
        num_inserted = scrape_and_populate_db(category, limit=limit)
        print(f"  [SUCCESS] Scraper finished. Inserted {num_inserted} products.")
    except Exception as e:
        print(f"  [ERROR] Scraper failed with exception: {e}")
    print()

def test_regex_on_body_text():
    print("=" * 60)
    print("SCRAPER TROUBLESHOOTING: Regex matching on body text")
    print("=" * 60)
    if not page_info_path.exists():
        print(f"Page text file not found at: {page_info_path}")
        print("Please save text from a sample product page to scratch/page_info.txt to debug.")
        return
        
    with open(page_info_path, "r", encoding="utf-8") as f:
        body_text = f.read()
        
    print("Scanning body text for ratings pattern:")
    # Pattern 1: rating followed by | and number of ratings (e.g. "4\n| 78")
    match1 = re.search(r'([1-5](?:\.[0-9])?)\s*\|\s*([0-9,]+)', body_text)
    if match1:
        print("  Match 1 (rating | count) found:")
        print("    Rating:", match1.group(1))
        print("    Count:", match1.group(2))
    else:
        print("  Match 1 pattern not found.")
        
    # Pattern 2: rating followed by star and count, or ratings count
    # Let's search for "based on X ratings"
    match2 = re.search(r'based on\s*([0-9,]+)\s*ratings', body_text, re.IGNORECASE)
    if match2:
        print("  Match 2 (based on count ratings) found:")
        print("    Count:", match2.group(1))
    else:
        print("  Match 2 pattern not found.")
        
    # Let's search for "X ratings"
    match3 = re.search(r'([0-9,]+)\s*ratings', body_text, re.IGNORECASE)
    if match3:
        print("  Match 3 (count ratings) found:")
        print("    Count:", match3.group(1))
    else:
        print("  Match 3 pattern not found.")
    print()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "--regex":
            test_regex_on_body_text()
        elif mode == "--cameras":
            run_scraper_test("cameras", limit=5)
        elif mode.startswith("--scrape="):
            category = mode.split("=")[1]
            run_scraper_test(category, limit=5)
    else:
        # Default behavior: run regex tests and inform user
        test_regex_on_body_text()
        print("Run with '--cameras' to test scraping cameras live, or '--scrape=<category>' to test a custom query.")
