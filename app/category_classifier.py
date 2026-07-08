import json
import re
import os
from pathlib import Path
from typing import Dict, Any, Tuple

class CategoryClassifier:
    """Intelligent classification engine for categorizing products using multiple fields and confidence scores."""

    def __init__(self, mapping_path: str = None):
        if mapping_path is None:
            mapping_path = str(Path(__file__).parent / "category_mapping.json")
        
        self.mapping_path = mapping_path
        self.load_mapping()
        
    def load_mapping(self):
        """Load category mapping configuration."""
        try:
            with open(self.mapping_path, 'r', encoding='utf-8') as f:
                self.categories = json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load category mapping: {e}")
            self.categories = {}

    def clean_text(self, text: str) -> str:
        """Clean and lowercase text for robust matching."""
        if not text:
            return ""
        # Keep letters, numbers, and basic spaces
        return re.sub(r'\s+', ' ', str(text).lower()).strip()

    def count_word_matches(self, text: str, keyword: str) -> int:
        """Count occurrences of keyword in text using word boundaries."""
        if not text or not keyword:
            return 0
        cleaned_kw = keyword.lower().strip()
        if not cleaned_kw:
            return 0
        
        # Escape keyword for safe regex matching
        escaped_kw = re.escape(cleaned_kw)
        
        # Word boundary matching. If keyword has spaces, we match it as is
        if ' ' in cleaned_kw:
            pattern = rf'\b{escaped_kw}\b'
        else:
            pattern = rf'\b{escaped_kw}\b'
            
        try:
            return len(re.findall(pattern, text))
        except Exception:
            return 1 if cleaned_kw in text else 0

    def classify(self, product_data: Dict[str, Any]) -> Tuple[str, float, str, str]:
        """
        Classifies a product based on its fields.
        Returns:
            Tuple of (category_name, confidence_score, source, reasoning)
        """
        if not self.categories:
            return "Others", 0.0, "None", "No category mapping configuration loaded."

        # Extract product fields
        title = self.clean_text(product_data.get("title", ""))
        name = self.clean_text(product_data.get("name", ""))
        brand = self.clean_text(product_data.get("brand", ""))
        description = self.clean_text(product_data.get("description", ""))
        specifications = self.clean_text(product_data.get("specifications", ""))
        breadcrumbs = self.clean_text(product_data.get("breadcrumbs", ""))
        url = self.clean_text(product_data.get("product_link", product_data.get("url", "")))
        flipkart_category = self.clean_text(product_data.get("flipkart_category", ""))
        attributes = self.clean_text(product_data.get("attributes", ""))

        # Combine text fields for general description search
        combined_details = f"{description} {specifications} {attributes}"

        scores = {}
        reasoning_log = {}

        # Evaluate match scores for each configured category
        for cat_name, cat_info in self.categories.items():
            keywords = cat_info.get("keywords", [])
            negative_keywords = cat_info.get("negative_keywords", [])
            
            # 1. Negative Keyword Match check (Exclusions)
            # If any negative keyword is found in the title or name, disqualify completely
            neg_match_found = False
            matched_neg_word = ""
            for neg_kw in negative_keywords:
                if self.count_word_matches(title, neg_kw) > 0 or self.count_word_matches(name, neg_kw) > 0:
                    neg_match_found = True
                    matched_neg_word = neg_kw
                    break
            
            if neg_match_found:
                scores[cat_name] = 0.0
                reasoning_log[cat_name] = f"Disqualified: Negative keyword '{matched_neg_word}' matched in title."
                continue

            # 2. Positive Keyword Score Calculations
            # Apply weights to different fields
            title_score = sum(self.count_word_matches(title, kw) * 10.0 for kw in keywords)
            name_score = sum(self.count_word_matches(name, kw) * 8.0 for kw in keywords)
            brand_score = sum(self.count_word_matches(brand, kw) * 4.0 for kw in keywords)
            breadcrumb_score = sum(self.count_word_matches(breadcrumbs, kw) * 6.0 for kw in keywords)
            category_score = sum(self.count_word_matches(flipkart_category, kw) * 6.0 for kw in keywords)
            url_score = sum(self.count_word_matches(url, kw) * 4.0 for kw in keywords)
            detail_score = sum(self.count_word_matches(combined_details, kw) * 1.5 for kw in keywords)

            # Sum score
            total_raw_score = title_score + name_score + brand_score + breadcrumb_score + category_score + url_score + detail_score
            
            # Penalize slightly if negative keywords are found in description/details
            for neg_kw in negative_keywords:
                if self.count_word_matches(combined_details, neg_kw) > 0:
                    total_raw_score -= 3.0
            
            total_raw_score = max(0.0, total_raw_score)
            scores[cat_name] = total_raw_score
            
            if total_raw_score > 0:
                reasoning_log[cat_name] = (
                    f"Score: {total_raw_score:.1f} (Title: {title_score:.1f}, "
                    f"Category: {category_score:.1f}, URL: {url_score:.1f}, Details: {detail_score:.1f})"
                )
            else:
                reasoning_log[cat_name] = "Score: 0.0 (No keyword matches)"

        # Prevent cross-conflict (e.g. Shoes classified as Electronics, or Laptop as Shoes)
        # We can implement specific super-category validation checks:
        # e.g., if "footwear" keywords match high, prevent choosing any Electronics category.
        # Find maximum scoring category
        sorted_categories = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_category, top_score = sorted_categories[0] if sorted_categories else ("Others", 0.0)

        # Apply Super-Category validation rules (Prevent impossible classifications)
        # If we have Footwear keywords matching, exclude Electronics
        if top_score > 0:
            top_super = self.categories[top_category].get("super_category", "")
            
            # Let's check conflicts with other scoring categories
            for alt_cat, alt_score in sorted_categories[1:]:
                if alt_score > 0:
                    alt_super = self.categories[alt_cat].get("super_category", "")
                    # Conflict: Electronics vs Fashion/Books/Toys
                    if top_super == "Electronics" and alt_super in ["Fashion", "Books", "Toys"] and alt_score >= (top_score * 0.4):
                        # Alt category has strong match. Re-check if title really has the alt keyword
                        # Example: "Puma Running Shoes" matches Puma (brand) and Shoes (Footwear). 
                        # Brand Puma is Electronics-neutral, but Shoes is Fashion-specific.
                        # Let's check which has higher title matches
                        alt_title_matches = sum(self.count_word_matches(title, kw) for kw in self.categories[alt_cat].get("keywords", []))
                        top_title_matches = sum(self.count_word_matches(title, kw) for kw in self.categories[top_category].get("keywords", []))
                        if alt_title_matches > top_title_matches:
                            # Swap
                            top_category, top_score = alt_cat, alt_score
                            top_super = alt_super
                            break

        # Calculate confidence score
        # Confidence is calculated relative to a reasonable expected score threshold (e.g. 10.0 for matching a keyword in title)
        # Or relative to sum of all positive scores.
        total_all_scores = sum(scores.values())
        
        if top_score == 0.0:
            return "Others", 0.0, "Keyword_Rules", "No matching keywords found across any categories."
            
        # Target threshold represents a standard high-quality match (e.g., 1 title match = 10.0 score)
        target_match_threshold = 10.0
        confidence = min(1.0, top_score / target_match_threshold)
        
        # If there's high ambiguity (e.g. another category has a very close score), reduce confidence
        if len(sorted_categories) > 1 and sorted_categories[1][1] > 0:
            runner_up_score = sorted_categories[1][1]
            margin = (top_score - runner_up_score) / top_score
            # If the margin is very small, reduce confidence
            if margin < 0.2:
                confidence *= (margin * 3.0) # Penalty for ambiguity

        # If confidence is below 0.40, set category to "Others" (Unknown)
        final_category = top_category
        reason = reasoning_log.get(top_category, "")
        
        # If confidence is low, classify as "Others"
        if confidence < 0.40:
            final_category = "Others"
            reason = f"Low confidence ({confidence*100:.1f}%). Best match was '{top_category}' with score {top_score:.1f}. Reason: {reason}"
            confidence = 0.0
        else:
            reason = f"Matched title/details (Score: {top_score:.1f}). {reason}"

        return final_category, float(confidence), "Keyword_Rules", reason

if __name__ == "__main__":
    classifier = CategoryClassifier()
    # Test laptop
    res = classifier.classify({
        "title": "ASUS Vivobook 15 Intel Core i3 11th Gen Laptop (8 GB RAM/512 GB SSD)",
        "brand": "ASUS",
        "description": "Standard windows laptop with SSD."
    })
    print("Test Laptop Classify:", res)
    
    # Test phone
    res = classifier.classify({
        "title": "Samsung Galaxy F15 5G (6GB RAM, 128GB Storage)",
        "brand": "Samsung"
    })
    print("Test Phone Classify:", res)

    # Test laptop accessory (should be disqualified or Others)
    res = classifier.classify({
        "title": "HP Laptop Bag Backpack",
        "brand": "HP"
    })
    print("Test Accessory Classify:", res)
