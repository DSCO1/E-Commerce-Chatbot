import sqlite3
import re
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import json

class CategoryManager:
    """Manages categories in the database, dynamic creation, and count recalculation."""

    def __init__(self, db_conn_factory, mapping_path: str = None):
        self.db_conn_factory = db_conn_factory
        if mapping_path is None:
            mapping_path = str(Path(__file__).parent / "category_mapping.json")
        self.mapping_path = mapping_path
        self.load_mapping()

    def load_mapping(self):
        try:
            with open(self.mapping_path, 'r', encoding='utf-8') as f:
                self.mapping = json.load(f)
        except Exception:
            self.mapping = {}

    def get_or_create_category(self, category_name: str) -> Tuple[int, str]:
        """
        Retrieves category ID and slug. If it does not exist, creates it dynamically.
        Returns:
            Tuple of (category_id, slug)
        """
        conn = self.db_conn_factory()
        cursor = conn.cursor()

        try:
            # Check if category exists
            cursor.execute("SELECT id, slug FROM category WHERE name = ?", (category_name,))
            row = cursor.fetchone()
            if row:
                return row[0], row[1]

            # Category doesn't exist, create it dynamically
            # 1. Determine slug
            # Check mapping config first
            cat_config = self.mapping.get(category_name, {})
            slug = cat_config.get("slug")
            if not slug:
                # Generate slug from name
                slug = category_name.strip().lower().replace(" & ", "-").replace(" ", "-").replace("/", "-")
                slug = re.sub(r'[^a-z0-9\-]', '', slug)
                
            # 2. Determine image and icon
            image = cat_config.get("image", "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=200&q=80")
            icon = cat_config.get("icon", "📦")

            cursor.execute("""
                INSERT INTO category (name, slug, icon, image, product_count)
                VALUES (?, ?, ?, ?, 0)
            """, (category_name, slug, icon, image))
            conn.commit()

            category_id = cursor.lastrowid
            print(f"[CATEGORY-CREATE] Dynamically created category: {category_name} (ID: {category_id}, Slug: {slug})")
            return category_id, slug
        finally:
            conn.close()

    def recalculate_all_counts(self):
        """Recalculates counts for all categories and deletes categories with 0 products if they are not in the mapping."""
        conn = self.db_conn_factory()
        cursor = conn.cursor()

        try:
            # 1. Reset all category counts to 0
            cursor.execute("UPDATE category SET product_count = 0")
            
            # 2. Compute counts from product table
            cursor.execute("SELECT category_id, COUNT(*) FROM product GROUP BY category_id")
            counts = cursor.fetchall()
            
            # 3. Update the counts
            for category_id, count in counts:
                if category_id:
                    cursor.execute("UPDATE category SET product_count = ? WHERE id = ?", (count, category_id))

            # 4. Remove dynamically created categories that are now empty (not in category_mapping)
            cursor.execute("SELECT id, name FROM category WHERE product_count = 0")
            empty_categories = cursor.fetchall()
            for cat_id, cat_name in empty_categories:
                if cat_name not in self.mapping and cat_name != "Others":
                    print(f"[CATEGORY-CLEAN] Removing empty dynamic category: {cat_name}")
                    cursor.execute("DELETE FROM category WHERE id = ?", (cat_id,))

            conn.commit()
        finally:
            conn.close()

