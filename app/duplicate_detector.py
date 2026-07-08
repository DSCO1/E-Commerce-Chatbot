import re
from difflib import SequenceMatcher
from typing import Optional, Tuple
import sqlite3

class DuplicateDetector:
    """Detects duplicate products in the database using multiple matching strategies."""

    def __init__(self, db_conn_factory):
        self.db_conn_factory = db_conn_factory

    @staticmethod
    def extract_product_id(url: str, title: str = "") -> str:
        """
        Extracts product ID from URL (e.g. Flipkart /p/itm... pattern).
        If not found, returns a cleaned version of the URL or a hash.
        """
        if not url:
            # Fallback to title based hash if no URL
            import hashlib
            return "hash_" + hashlib.md5(title.encode('utf-8')).hexdigest()[:12]
            
        # Try to find /p/itm... pattern (Flipkart product ID)
        match = re.search(r'/p/(itm[a-zA-Z0-9]+)', url)
        if match:
            return match.group(1)
            
        # Strip query parameters and clean up
        clean_url = url.split('?')[0].rstrip('/')
        # Extract last part or hash
        import hashlib
        return hashlib.md5(clean_url.encode('utf-8')).hexdigest()[:16]

    @staticmethod
    def title_similarity(title1: str, title2: str) -> float:
        """Returns similarity score between 0.0 and 1.0 using SequenceMatcher."""
        if not title1 or not title2:
            return 0.0
        t1 = str(title1).strip().lower()
        t2 = str(title2).strip().lower()
        return SequenceMatcher(None, t1, t2).ratio()

    def check_duplicate(self, product_link: str, title: str) -> Tuple[bool, Optional[str]]:
        """
        Checks if the product already exists in the database.
        Returns:
            Tuple of (is_duplicate, existing_product_id)
        """
        product_id = self.extract_product_id(product_link, title)
        conn = self.db_conn_factory()
        cursor = conn.cursor()

        try:
            # 1. Check by exact product_id
            cursor.execute("SELECT product_id FROM product WHERE product_id = ?", (product_id,))
            row = cursor.fetchone()
            if row:
                return True, row[0]

            # 2. Check by exact product_link (ignoring query parameters)
            base_link = product_link.split('?')[0]
            cursor.execute("SELECT product_id FROM product WHERE product_link LIKE ?", (f"{base_link}%",))
            row = cursor.fetchone()
            if row:
                return True, row[0]

            # 3. Check by title similarity of products from the same brand
            # Extract brand
            words = title.strip().split()
            brand = words[0] if words else "Generic"
            
            cursor.execute("SELECT product_id, title FROM product WHERE brand LIKE ?", (brand,))
            for row in cursor.fetchall():
                existing_id, existing_title = row
                similarity = self.title_similarity(title, existing_title)
                if similarity > 0.95:  # Extremely high similarity
                    return True, existing_id

            return False, None
        finally:
            conn.close()
