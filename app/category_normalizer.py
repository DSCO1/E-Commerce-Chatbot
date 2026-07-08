import re

class CategoryNormalizer:
    """Normalizes category names into consistent, standardized names."""

    # Map of lowercase synonyms/variations to standard category names
    NORMALIZE_MAP = {
        # Laptops
        "laptop": "Laptops",
        "laptops": "Laptops",
        "notebook": "Laptops",
        "notebooks": "Laptops",
        "ultrabook": "Laptops",
        "ultrabooks": "Laptops",
        "macbook": "Laptops",
        "macbooks": "Laptops",
        "chromebook": "Laptops",
        "chromebooks": "Laptops",
        
        # Smartphones
        "smartphone": "Smartphones",
        "smartphones": "Smartphones",
        "phone": "Smartphones",
        "phones": "Smartphones",
        "mobile": "Smartphones",
        "mobiles": "Smartphones",
        "cellphone": "Smartphones",
        "cellphones": "Smartphones",
        
        # Air Conditioners
        "ac": "Air Conditioners",
        "acs": "Air Conditioners",
        "air conditioner": "Air Conditioners",
        "air conditioners": "Air Conditioners",
        "split ac": "Air Conditioners",
        "window ac": "Air Conditioners",
        "air-conditioner": "Air Conditioners",
        
        # Air Coolers
        "cooler": "Air Coolers",
        "coolers": "Air Coolers",
        "air cooler": "Air Coolers",
        "air coolers": "Air Coolers",
        "desert cooler": "Air Coolers",
        "personal cooler": "Air Coolers",
        
        # Washing Machines
        "washing machine": "Washing Machines",
        "washing machines": "Washing Machines",
        "washer": "Washing Machines",
        "washers": "Washing Machines",
        "dryer": "Washing Machines",
        "dryers": "Washing Machines",
        
        # Refrigerators
        "refrigerator": "Refrigerators",
        "refrigerators": "Refrigerators",
        "fridge": "Refrigerators",
        "fridges": "Refrigerators",
        
        # Televisions
        "tv": "Televisions",
        "tvs": "Televisions",
        "television": "Televisions",
        "televisions": "Televisions",
        "smart tv": "Televisions",
        "monitor": "Televisions",
        "monitors": "Televisions",
        
        # Headphones
        "headphone": "Headphones",
        "headphones": "Headphones",
        "earphone": "Headphones",
        "earphones": "Headphones",
        "earbuds": "Headphones",
        "earbud": "Headphones",
        "headset": "Headphones",
        "headsets": "Headphones",
        "speaker": "Headphones",
        "speakers": "Headphones",
        "soundbar": "Headphones",
        
        # Computer Mice
        "mouse": "Computer Mice",
        "mice": "Computer Mice",
        "computer mouse": "Computer Mice",
        
        # Induction Cooktops
        "induction": "Induction Cooktops",
        "cooktop": "Induction Cooktops",
        "cooktops": "Induction Cooktops",
        "induction cooker": "Induction Cooktops",
        "stove": "Induction Cooktops",
        
        # Mixers & Grinders
        "mixer": "Mixers & Grinders",
        "blender": "Mixers & Grinders",
        "grinder": "Mixers & Grinders",
        "juicer": "Mixers & Grinders",
        "mixer grinder": "Mixers & Grinders",
        
        # Mosquito Bats
        "mosquito": "Mosquito Bats",
        "mosquito bat": "Mosquito Bats",
        "mosquito bats": "Mosquito Bats",
        "mosquito racket": "Mosquito Bats",
        
        # Trimmers & Grooming
        "trimmer": "Trimmers & Grooming",
        "trimmers": "Trimmers & Grooming",
        "shaver": "Trimmers & Grooming",
        "shavers": "Trimmers & Grooming",
        "groomer": "Trimmers & Grooming",
        "grooming": "Trimmers & Grooming",
        "epilator": "Trimmers & Grooming",
        
        # Sunglasses
        "sunglasses": "Sunglasses",
        "sunglass": "Sunglasses",
        "spectacles": "Sunglasses",
        "spectacle": "Sunglasses",
        "goggles": "Sunglasses",
        
        # Books & Manga
        "book": "Books & Manga",
        "books": "Books & Manga",
        "manga": "Books & Manga",
        "novel": "Books & Manga",
        "novels": "Books & Manga",
        "comic": "Books & Manga",
        "comics": "Books & Manga",
        
        # Fidget Toys
        "fidget": "Fidget Toys",
        "fidgets": "Fidget Toys",
        "popper": "Fidget Toys",
        "pop it": "Fidget Toys",
        "fidget spinner": "Fidget Toys",
        "spinner": "Fidget Toys",
        
        # Cameras
        "camera": "Cameras",
        "cameras": "Cameras",
        "dslr": "Cameras",
        
        # Fans
        "fan": "Fans",
        "fans": "Fans",
        
        # Footwear
        "shoe": "Footwear",
        "shoes": "Footwear",
        "footwear": "Footwear",
        "sneaker": "Footwear",
        "sneakers": "Footwear",
        "sandal": "Footwear",
        "sandals": "Footwear",
        "slipper": "Footwear",
        "slippers": "Footwear",
        "boot": "Footwear",
        "boots": "Footwear",
        
        # Smartwatches
        "watch": "Smartwatches",
        "watches": "Smartwatches",
        "smartwatch": "Smartwatches",
        "smartwatches": "Smartwatches",
        "fitness band": "Smartwatches",
        "smart band": "Smartwatches"
    }

    @classmethod
    def normalize(cls, name: str) -> str:
        """Normalize a category name. If not recognized, returns title-cased trimmed version."""
        if not name:
            return "Others"
        
        cleaned = str(name).strip().lower()
        if cleaned in cls.NORMALIZE_MAP:
            return cls.NORMALIZE_MAP[cleaned]
        
        # Try finding as a whole word boundary match in standard keys to prevent false partial matches
        for key, std_name in cls.NORMALIZE_MAP.items():
            if re.search(rf'\b{re.escape(key)}\b', cleaned):
                return std_name
                
        # Return title cased version if no match
        return name.strip().title()

if __name__ == "__main__":
    print(CategoryNormalizer.normalize("notebooks"))
    print(CategoryNormalizer.normalize("Phones"))
    print(CategoryNormalizer.normalize("Unknown item"))
