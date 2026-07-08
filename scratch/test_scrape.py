import sys
from pathlib import Path

# Add app/ to sys.path so we can import modules
sys.path.append(str(Path(__file__).parent.parent / "app"))

from main import ask

print("Starting live test of chatbot query...")
query = "show me nothing 3 back cover under 500 rupee"
print(f"Query: '{query}'")

response, products = ask(query)

print("\n--- CHATBOT RESPONSE ---")
print(response)

print("\n--- PRODUCTS CAROUSEL ---")
for p in products:
    print(f"- {p.get('brand')} | {p.get('title')} | Rs.{p.get('price')} | Link: {p.get('product_link')}")
