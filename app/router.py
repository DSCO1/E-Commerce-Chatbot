from semantic_router import Route, SemanticRouter
from semantic_router.encoders import HuggingFaceEncoder

encoder = HuggingFaceEncoder(
    name="sentence-transformers/all-MiniLM-L6-v2",
    device="cpu"
)
faq = Route(
    name='faq',
    utterances=[
        "What is the return policy of the products?",
        "Do I get discount with the HDFC credit card?",
        "How can I track my order?",
        "What payment methods are accepted?",
        "How long does it take to process a refund?",
        "What is your shipping policy?",
        "How do I cancel my order?",
        "Do you offer EMI options?",
        "What is the warranty on products?",
        "How do I contact customer support?",
        "How can I create an account?",
        "What should I do if my package is lost or damaged?",
        "Can I change my shipping address after placing an order?",
        "Do you offer gift wrapping services?",
        "Do you have a loyalty program?",
        "Can I return a product if it was purchased with a gift card?",
        "Can we make payment in Cash after delivery?",
    ]
)

sql = Route(
    name='sql',
    utterances=[
        # General product queries
        "Show me the cheapest products available.",
        "What products do you have?",
        "Show me all products with more than 4 star rating.",
        "What are the top rated products?",
        "Show me products with the highest discount.",
        "Which products are under Rs. 5000?",
        "List all products sorted by price.",
        "What brands do you have?",

        # Laptop queries
        "Show me laptops.",
        "Show me some laptops.",
        "What laptops do you have?",
        "Are there any laptops under Rs. 50000?",
        "Do you have laptops from HP or Dell?",
        "Show me laptops with i7 processor.",
        "I want a budget laptop under 30000.",
        "What is the best rated laptop?",
        "Show me gaming laptops.",

        # Shoe queries
        "Show me shoes.",
        "Show me some shoes.",
        "What shoes do you have?",
        "I want to buy nike shoes that have 50% discount.",
        "Are there any shoes under Rs. 3000?",
        "Are there any Puma shoes on sale?",
        "What is the price of puma running shoes?",
        "Show me sports shoes.",

        # Watch queries
        "Show me watches.",
        "Show me some watches.",
        "What watches do you have?",
        "Show me watches with discount more than 30%.",
        "I want to buy a sports watch.",
        "What is the price of the fossil watch?",
        "Show me smartwatches under 5000.",

        # Cooler queries
        "Show me coolers.",
        "Show me some air coolers.",
        "What coolers do you have?",
        "Show me Symphony air coolers.",
        "Are there any coolers under Rs. 8000?",
        "I want to buy a desert cooler.",

        # AC / Air Conditioner queries
        "Show me ACs.",
        "Show me split air conditioners.",
        "Do you have window AC?",
        "What air conditioners do you have?",
        "LG split AC under 40000.",
        "Show me 1.5 ton ACs.",

        # Fan queries
        "Show me fans.",
        "Do you have ceiling fans?",
        "Havells fans price list.",
        "Show me wall fans.",
        "Show me pedestal fans.",

        # Fridge / Refrigerator queries
        "Show me fridges.",
        "What refrigerators do you have?",
        "Samsung double door fridge.",
        "Show me single door refrigerators.",
        "Are there any fridges under 25000?",

        # Washing Machine queries
        "Show me washing machines.",
        "What washing machines do you have?",
        "LG front load washing machine.",
        "Washing machine under 15000.",
        "Fully automatic washing machines.",

        # Phone/Electronics queries
        "Do you have Samsung phones?",
        "Show me phones under Rs. 15000.",
        "What earbuds do you have?",
        "I want a tablet under 20000.",
        "Show me headphones with good ratings.",

        # Clothing queries
        "Show me t-shirts under Rs. 500.",
        "Do you have jackets from Puma?",
        "What jeans do you have?",

        # Other categories (generalization)
        "Show me trimmers.",
        "Show me some trimmers.",
        "What trimmers do you have?",
        "Do you have any trimmers?",
        "Show me cameras.",
        "Do you sell cameras?",
        "Show me bicycles.",
        "What keyboards do you have?",
        "Show me toys.",

        # General shopping intent
        "I want to buy something with a big discount.",
        "What is the price of this product?",
        "Which product has the best reviews?",
        "Show me products from brand Apple.",
        "I'm looking for something under my budget of 10000.",
    ]
)

router = SemanticRouter(routes=[faq, sql], encoder=encoder, auto_sync="local", top_k=1)

if __name__ == "__main__":
    print(router("What is your policy on defective product?").name)
    print(router("Pink Puma shoes in price range 5000 to 1000").name)