"""Test script to verify query cleaning and fallback classification behavior."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "app"))

from sql import clean_search_term
from category_normalizer import CategoryNormalizer

def test_clean_search_term():
    print("=" * 60)
    print("TESTING SEARCH TERM TO CATEGORY NAME CONVERSION")
    print("=" * 60)
    
    test_cases = [
        ("perfume", "Perfumes"),
        ("chocolate", "Chocolates"),
        ("smart plugs", "Smart Plugs"),
        ("jackets under 2000", "Jackets"),
        ("buy online keyboards", "Keyboards"),
        ("tshirt", "Tshirts"),
        ("laptops", "Laptops"), # Already plural
        ("smartphones", "Smartphones"), # Already plural
        ("curtains", "Curtains"),
        ("sofa", "Sofas"),
        ("cheap sunglasses", "Sunglasses"), # Normalizes to existing category Sunglasses
        ("best earbuds", "Earbuds"), # Will map to Headphones via normalizer
    ]
    
    passed = True
    for query, expected in test_cases:
        candidate = clean_search_term(query)
        # Normalize to see if it resolves to existing categories
        normalized = CategoryNormalizer.normalize(candidate)
        
        # If it was "best earbuds" -> candidate is "Earbuds" -> normalizes to "Headphones"
        expected_normalized = CategoryNormalizer.normalize(expected)
        
        status = "✅ PASS" if normalized == expected_normalized else "❌ FAIL"
        if normalized != expected_normalized:
            passed = False
        print(f"  {status} | Query: '{query}' -> Candidate: '{candidate}' -> Normalized: '{normalized}' (Expected: '{expected_normalized}')")
        
    print("\nOverall Search Term Fallback Tests:", "PASSED ✅" if passed else "FAILED ❌")
    return passed

if __name__ == "__main__":
    test_clean_search_term()
