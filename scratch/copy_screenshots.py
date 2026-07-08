import shutil
import os

src_dir = r"c:\Users\Ujjaw\OneDrive\Documents\E-commerce chatbot\scratch\screenshots"
dest_dir = r"C:\Users\Ujjaw\.gemini\antigravity-ide\brain\95796c4d-1896-467a-b456-2585590b183c"

os.makedirs(dest_dir, exist_ok=True)

for name in ["scraper_home.png", "chat_home.png", "catalog_home.png"]:
    src_path = os.path.join(src_dir, name)
    dest_path = os.path.join(dest_dir, name)
    if os.path.exists(src_path):
        shutil.copy(src_path, dest_path)
        print(f"Copied {name} to artifact directory successfully.")
    else:
        print(f"Source file {src_path} does not exist.")
