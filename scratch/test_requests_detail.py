"""Test if requests can fetch Flipkart product pages without getting blocked, to fast-heal database image URLs."""
import requests
from bs4 import BeautifulSoup

url = "https://www.flipkart.com/orient-electric-46-l-room-personal-air-cooler/p/itmf2qcfu7ty86p8"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

print(f"Fetching via requests: {url}")
try:
    r = requests.get(url, headers=headers, timeout=10)
    print(f"Response status: {r.status_code}")
    print(f"Response length: {len(r.text)} characters")
    
    soup = BeautifulSoup(r.text, 'lxml')
    # Let's count image tags
    imgs = soup.find_all('img')
    print(f"Total image tags: {len(imgs)}")
    
    # Try our selectors
    image_url = ''
    for selector in ['img._0DkuPH', 'img.DByoR4', 'img.jzoB4e', 'img.UHDDFP', 'img._53u2j-']:
        el = soup.select_one(selector)
        if el and el.get('src') and 'logo' not in el.get('src', '').lower():
            image_url = el.get('src')
            print(f"Matched selector '{selector}': {image_url}")
            break
            
    if not image_url:
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if ('rukminim2.flixcart.com/image/' in src or '/xif0q/' in src) and 'logo' not in src.lower() and 'promo' not in src.lower():
                image_url = src
                print(f"Matched fallback: {image_url}")
                break
except Exception as e:
    print(f"Error: {e}")
