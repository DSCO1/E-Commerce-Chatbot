import sys
from pathlib import Path

# Add app/ to sys.path so we can import modules
sys.path.append(str(Path(__file__).parent.parent / "app"))

from sql import sql_chain_structured

print("=" * 60)
print("TEST 1: nothing 3 back cover under 500 rupee")
print("=" * 60)
response, products = sql_chain_structured("show me nothing 3 back cover under 500 rupee")
print(f"\nResponse: {response}")
print(f"Products count: {len(products)}")
for p in products[:3]:
    print(f"  - {p.get('brand')} | {p.get('title')[:60]} | Rs.{p.get('price')}")

print("\n" + "=" * 60)
print("TEST 2: iphone 17 backcover")
print("=" * 60)
response2, products2 = sql_chain_structured("iphone 17 backcover")
print(f"\nResponse: {response2}")
print(f"Products count: {len(products2)}")
for p in products2[:3]:
    print(f"  - {p.get('brand')} | {p.get('title')[:60]} | Rs.{p.get('price')}")

print("\n" + "=" * 60)
print("TEST 3: samsung s25 backcover under 1000 rupee")
print("=" * 60)
response3, products3 = sql_chain_structured("samsung s25 backcover under 1000 rupee")
print(f"\nResponse: {response3}")
print(f"Products count: {len(products3)}")
for p in products3[:3]:
    print(f"  - {p.get('brand')} | {p.get('title')[:60]} | Rs.{p.get('price')}")

print("\nAll tests complete!")
