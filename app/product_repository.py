import sqlite3
from typing import Dict, Any, Optional
import time

class ProductRepository:
    """Handles CRUD operations for the product table in SQLite."""

    def __init__(self, db_conn_factory):
        self.db_conn_factory = db_conn_factory

    def save_product(self, product_data: Dict[str, Any]) -> str:
        """
        Saves a product to the database. If it exists, updates it. If not, inserts it.
        Returns:
            The product_id of the saved product.
        """
        conn = self.db_conn_factory()
        cursor = conn.cursor()

        product_id = product_data["product_id"]
        product_link = product_data["product_link"]
        title = product_data["title"]
        brand = product_data.get("brand", "Generic")
        category_id = product_data.get("category_id")
        category_name = product_data.get("category_name")
        confidence_score = product_data.get("confidence_score", 0.0)
        classification_source = product_data.get("classification_source", "Keyword_Rules")
        price = product_data.get("price", 0)
        discount = product_data.get("discount", 0.0)
        avg_rating = product_data.get("avg_rating", 0.0)
        rating = product_data.get("rating", avg_rating)
        total_ratings = product_data.get("total_ratings", 0)
        availability = product_data.get("availability", "In Stock")
        image = product_data.get("image", "")
        image_url = product_data.get("image_url", image)
        description = product_data.get("description", "")
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')

        try:
            # Check if exists by product_id
            cursor.execute("SELECT id FROM product WHERE product_id = ?", (product_id,))
            row = cursor.fetchone()

            if row:
                # Update existing product
                cursor.execute("""
                    UPDATE product
                    SET title = ?,
                        brand = ?,
                        category_id = ?,
                        category_name = ?,
                        confidence_score = ?,
                        classification_source = ?,
                        price = ?,
                        discount = ?,
                        avg_rating = ?,
                        rating = ?,
                        total_ratings = ?,
                        availability = ?,
                        image = ?,
                        image_url = ?,
                        description = ?,
                        updated_at = ?
                    WHERE product_id = ?
                """, (title, brand, category_id, category_name, confidence_score, classification_source,
                      price, discount, avg_rating, rating, total_ratings, availability, image, image_url,
                      description, current_time, product_id))
                print(f"[PRODUCT-UPDATE] Updated product: {title[:50]}... (ID: {product_id})")
            else:
                # Insert new product
                cursor.execute("""
                    INSERT INTO product (
                        product_id, product_link, title, brand, category_id, category_name,
                        confidence_score, classification_source, price, discount, avg_rating,
                        rating, total_ratings, availability, image, image_url, description,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (product_id, product_link, title, brand, category_id, category_name,
                      confidence_score, classification_source, price, discount, avg_rating,
                      rating, total_ratings, availability, image, image_url, description,
                      current_time, current_time))
                print(f"[PRODUCT-INSERT] Inserted new product: {title[:50]}... (ID: {product_id})")
            
            conn.commit()
            return product_id
        finally:
            conn.close()
