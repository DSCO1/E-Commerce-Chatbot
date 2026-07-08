file_path = r"c:\Users\Ujjaw\OneDrive\Documents\E-commerce chatbot\app\main.py"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if "col_chat" in line:
        print(f"Line {i}: {line.strip()}")
