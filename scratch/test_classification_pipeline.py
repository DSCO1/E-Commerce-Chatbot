"""Test script to verify the classification pipeline, deduplication, and dynamic catalog."""
import sys
import sqlite3
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "app"))

from category_classifier import CategoryClassifier
from category_normalizer import CategoryNormalizer
from duplicate_detector import DuplicateDetector

db_path = Path(__file__).parent.parent / "app" / "db.sqlite"

def test_classifier():
    print("=" * 60)
    print("TEST 1: Product Classification Accuracy")
    print("=" * 60)
    
    classifier = CategoryClassifier()
    
    test_cases = [
        # (product_data, expected_category)
        ({"title": "Apple MacBook Air M4 Laptop (16 GB/512 GB SSD)", "brand": "Apple"}, "Laptops"),
        ({"title": "ASUS Vivobook 15 Intel Core i3 Laptop (8 GB RAM/512 GB SSD)", "brand": "ASUS"}, "Laptops"),
        ({"title": "Samsung Galaxy F15 5G (6GB RAM, 128GB Storage)", "brand": "Samsung"}, "Smartphones"),
        ({"title": "Apple iPhone 16 (Black, 128 GB)", "brand": "Apple"}, "Smartphones"),
        ({"title": "LG 1.5 Ton 5 Star Inverter Split AC", "brand": "LG"}, "Air Conditioners"),
        ({"title": "Orient Electric 46 L Room/Personal Air Cooler", "brand": "Orient"}, "Air Coolers"),
        ({"title": "Samsung 7 kg Fully Automatic Top Load Washing Machine", "brand": "Samsung"}, "Washing Machines"),
        ({"title": "Whirlpool 265 L Frost Free Double Door Refrigerator", "brand": "Whirlpool"}, "Refrigerators"),
        ({"title": "Samsung 108 cm (43 inch) Full HD LED Smart TV", "brand": "Samsung"}, "Televisions"),
        ({"title": "boAt Airdopes 141 TWS Earbuds", "brand": "boAt"}, "Headphones"),
        ({"title": "Logitech G502 HERO Gaming Mouse", "brand": "Logitech"}, "Computer Mice"),
        ({"title": "Prestige Xclusive PIC 20.0 Induction Cooktop", "brand": "Prestige"}, "Induction Cooktops"),
        ({"title": "Bajaj Rex 500 W Mixer Grinder", "brand": "Bajaj"}, "Mixers & Grinders"),
        ({"title": "HIT Rechargeable Electric Mosquito Bat", "brand": "HIT"}, "Mosquito Bats"),
        ({"title": "Philips BT3215 Beard Trimmer", "brand": "Philips"}, "Trimmers & Grooming"),
        ({"title": "Ray-Ban Aviator Sunglasses", "brand": "Ray-Ban"}, "Sunglasses"),
        ({"title": "Atomic Habits Paperback Book", "brand": "Generic"}, "Books & Manga"),
        ({"title": "Push Pop Fidget Spinner Stress Relief Toy", "brand": "Generic"}, "Fidget Toys"),
        ({"title": "Canon EOS 1500D DSLR Camera", "brand": "Canon"}, "Cameras"),
        ({"title": "Crompton Hill Briz 48 inch Ceiling Fan", "brand": "Crompton"}, "Fans"),
        ({"title": "Nike Revolution 6 Running Shoes", "brand": "Nike"}, "Footwear"),
        ({"title": "Fire-Boltt Phoenix Ultra Smartwatch", "brand": "Fire-Boltt"}, "Smartwatches"),
    ]
    
    passed = 0
    failed = 0
    
    for product_data, expected in test_cases:
        category, confidence, source, reason = classifier.classify(product_data)
        normalized = CategoryNormalizer.normalize(category)
        
        status = "✅ PASS" if normalized == expected else "❌ FAIL"
        if normalized == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"  {status} | {product_data['title'][:50]}")
        if normalized != expected:
            print(f"         Expected: {expected}, Got: {normalized} (Confidence: {confidence*100:.1f}%)")
            print(f"         Reason: {reason}")
    
    print(f"\n  Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    return failed == 0

def test_cross_contamination():
    print("\n" + "=" * 60)
    print("TEST 2: Cross-Contamination Prevention")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    checks = [
        ("Laptops classified as Smartphones",
         "SELECT COUNT(*) FROM product WHERE category_name = 'Smartphones' AND (title LIKE '%laptop%' OR title LIKE '%notebook%' OR title LIKE '%macbook%')"),
        ("Refrigerators classified as Air Conditioners",
         "SELECT COUNT(*) FROM product WHERE category_name = 'Air Conditioners' AND (title LIKE '%refrigerator%' OR title LIKE '%fridge%')"),
        ("Washing Machines classified as Refrigerators",
         "SELECT COUNT(*) FROM product WHERE category_name = 'Refrigerators' AND (title LIKE '%washing%' OR title LIKE '%washer%')"),
        ("TVs classified as Smartwatches",
         "SELECT COUNT(*) FROM product WHERE category_name = 'Smartwatches' AND (title LIKE '%tv%' OR title LIKE '%television%')"),
        ("Shoes classified as Electronics",
         "SELECT COUNT(*) FROM product WHERE category_name IN ('Laptops', 'Smartphones', 'Televisions') AND (title LIKE '%shoe%' OR title LIKE '%sneaker%')"),
    ]
    
    all_pass = True
    for label, query in checks:
        cursor.execute(query)
        count = cursor.fetchone()[0]
        status = "✅ PASS" if count == 0 else f"❌ FAIL ({count} found)"
        if count > 0:
            all_pass = False
        print(f"  {status} | No {label}")
    
    conn.close()
    return all_pass

def test_category_counts():
    print("\n" + "=" * 60)
    print("TEST 3: Category Counts Match Actual Products")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get stored counts
    cursor.execute("SELECT name, product_count FROM category")
    stored_counts = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Get actual counts
    cursor.execute("SELECT category_name, COUNT(*) FROM product GROUP BY category_name")
    actual_counts = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Total product count
    cursor.execute("SELECT COUNT(*) FROM product")
    total_products = cursor.fetchone()[0]
    
    total_stored = sum(stored_counts.values())
    
    all_pass = True
    for cat_name, stored in stored_counts.items():
        actual = actual_counts.get(cat_name, 0)
        status = "✅" if stored == actual else "❌"
        if stored != actual:
            all_pass = False
        print(f"  {status} {cat_name}: stored={stored}, actual={actual}")
    
    total_match = total_stored == total_products
    print(f"\n  Total Products: {total_products}")
    print(f"  Sum of Category Counts: {total_stored}")
    print(f"  {'✅ PASS' if total_match else '❌ FAIL'} | Total counts match")
    
    conn.close()
    return all_pass and total_match

def test_no_duplicates():
    print("\n" + "=" * 60)
    print("TEST 4: No Duplicate Products")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM product")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT product_id) FROM product")
    unique_ids = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT product_link) FROM product")
    unique_links = cursor.fetchone()[0]
    
    id_pass = total == unique_ids
    link_pass = total == unique_links
    
    print(f"  {'✅ PASS' if id_pass else '❌ FAIL'} | All product_ids are unique ({unique_ids}/{total})")
    print(f"  {'✅ PASS' if link_pass else '❌ FAIL'} | All product_links are unique ({unique_links}/{total})")
    
    conn.close()
    return id_pass and link_pass

def test_dynamic_catalog():
    print("\n" + "=" * 60)
    print("TEST 5: Dynamic Catalog (Categories from DB)")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM category")
    cat_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT name, slug, image, product_count FROM category ORDER BY product_count DESC")
    categories = cursor.fetchall()
    
    print(f"  Total categories in DB: {cat_count}")
    for name, slug, image, count in categories:
        has_image = "✅" if image and image.startswith("http") else "⚠️"
        print(f"  {has_image} {name} (slug: {slug}) -> {count} products")
    
    all_have_slugs = all(slug for _, slug, _, _ in categories)
    all_have_images = all(img and img.startswith("http") for _, _, img, _ in categories)
    
    print(f"\n  {'✅ PASS' if cat_count > 0 else '❌ FAIL'} | Categories exist in DB")
    print(f"  {'✅ PASS' if all_have_slugs else '❌ FAIL'} | All categories have slugs")
    print(f"  {'✅ PASS' if all_have_images else '⚠️ WARN'} | All categories have images")
    
    conn.close()
    return cat_count > 0

if __name__ == "__main__":
    results = []
    results.append(("Classification Accuracy", test_classifier()))
    results.append(("Cross-Contamination", test_cross_contamination()))
    results.append(("Category Counts", test_category_counts()))
    results.append(("No Duplicates", test_no_duplicates()))
    results.append(("Dynamic Catalog", test_dynamic_catalog()))
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS SUMMARY")
    print("=" * 60)
    all_pass = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        if not passed:
            all_pass = False
        print(f"  {status} | {name}")
    
    print(f"\n  Overall: {'ALL TESTS PASSED ✅' if all_pass else 'SOME TESTS FAILED ❌'}")
