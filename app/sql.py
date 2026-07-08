from groq import Groq
import os
import re
import sqlite3
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from pandas import DataFrame

load_dotenv(Path(__file__).parent / ".env")

FALLBACK_MODELS = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "meta-llama/llama-4-scout-17b-16e-instruct"]

GROQ_MODEL = os.getenv('GROQ_MODEL')
if not GROQ_MODEL:
    GROQ_MODEL = FALLBACK_MODELS[0]
    os.environ['GROQ_MODEL'] = GROQ_MODEL

db_path = Path(__file__).parent / "db.sqlite"

# --------------- Multi-Key Pool ---------------
# Reads GROQ_API_KEY, GROQ_API_KEY_2, GROQ_API_KEY_3, ... from .env
def _load_api_keys():
    keys = []
    primary = os.getenv("GROQ_API_KEY")
    if primary:
        keys.append(primary)
    for i in range(2, 11):  # support up to 10 keys
        k = os.getenv(f"GROQ_API_KEY_{i}")
        if k:
            keys.append(k)
    return keys if keys else [primary or ""]

API_KEYS = _load_api_keys()
_current_key_idx = 0

def get_groq_client():
    """Return a Groq client using the currently active API key."""
    global _current_key_idx
    return Groq(api_key=API_KEYS[_current_key_idx % len(API_KEYS)])

def rotate_api_key():
    """Advance to the next API key in the pool. Returns the new key index."""
    global _current_key_idx
    _current_key_idx = (_current_key_idx + 1) % len(API_KEYS)
    print(f"[KEY-ROTATE] Switched to API key #{_current_key_idx + 1} of {len(API_KEYS)}")
    return _current_key_idx

client_sql = get_groq_client()

sql_prompt = """You are an expert in understanding the database schema and generating SQL queries for a natural language question asked
pertaining to the data you have. The schema is provided in the schema tags. 
<schema> 
table: product 

fields: 
product_link - string (hyperlink to product)	
title - string (name of the product, contains the product type like laptop, shoes, watch, phone, etc.)	
brand - string (brand of the product)	
price - integer (price of the product in Indian Rupees)	
discount - float (discount on the product. 10 percent discount is represented as 0.1, 20 percent as 0.2, and such.)	
avg_rating - float (average rating of the product. Range 0-5, 5 is the highest.)	
total_ratings - integer (total number of ratings for the product)

</schema>
Make sure whenever you try to search for the brand name, the name can be in any case. 
So, make sure to use %LIKE% to find the brand in condition. Never use "ILIKE". 

CRITICAL QUERY ACCURACY RULES:
1. ALWAYS FILTER BY PRODUCT TYPE: You MUST always identify the product type or category (e.g. laptop, cooler, fan, shoe, watch, phone, refrigerator, washing machine, AC, back cover, case, screen protector, earbuds, charger, cable, etc.) from the user's question and search for it in the 'title' column. Never write a query without filtering the product category, otherwise it will return incorrect types of products (e.g., returning air coolers when asked for a laptop).
2. STRICT CATEGORY EXCLUSION RULES (CRITICAL):
   IMPORTANT: These exclusion rules ONLY apply when the user is asking for the MAIN product (e.g., a laptop, a phone, a fan). If the user is explicitly asking for an ACCESSORY product (like a "back cover", "case", "screen protector", "charger", "cable", "sleeve", "bag", "stand", "keyboard", "mouse", "earphone", "headphone"), then do NOT apply any NOT LIKE exclusions that would filter out the very product the user wants. For example, if the user asks for a "back cover", do NOT add `NOT LIKE '%cover%'`.
   - LAPTOP EXCLUSIONS (only when asking for laptops, NOT laptop accessories): When the user asks for a "laptop", "notebook", or "chromebook", you MUST search for them but strictly exclude any accessory products using `NOT LIKE` conditions:
     `title LIKE '%laptop%' AND title NOT LIKE '%speaker%' AND title NOT LIKE '%soundbar%' AND title NOT LIKE '%case%' AND title NOT LIKE '%cover%' AND title NOT LIKE '%bag%' AND title NOT LIKE '%sleeve%' AND title NOT LIKE '%adapter%' AND title NOT LIKE '%charger%' AND title NOT LIKE '%cable%' AND title NOT LIKE '%stand%' AND title NOT LIKE '%mouse%' AND title NOT LIKE '%keyboard%' AND title NOT LIKE '%headphone%' AND title NOT LIKE '%earphone%'`
   - FAN EXCLUSIONS: When the user asks for a "fan" (such as ceiling fans, exhaust fans, pedestal fans, wall fans), you MUST search for `fan` but strictly exclude air coolers, air conditioners, heaters, and cases using `NOT LIKE` conditions:
     `title LIKE '%fan%' AND title NOT LIKE '%cooler%' AND title NOT LIKE '%ac%' AND title NOT LIKE '%conditioner%' AND title NOT LIKE '%heater%' AND title NOT LIKE '%case%' AND title NOT LIKE '%cover%'`
   - AIR COOLER EXCLUSIONS: When the user asks for a "cooler" or "air cooler", you MUST search for `cooler` but exclude stand-alone fans using `NOT LIKE`:
     `title LIKE '%cooler%' AND title NOT LIKE '%ceiling fan%' AND title NOT LIKE '%exhaust fan%' AND title NOT LIKE '%pedestal fan%'`
   - FOOTBALL EXCLUSIONS: When the user asks for a "football" or "soccer", you MUST search for them but strictly exclude TVs, televisions, board games, chess sets, and toys using `NOT LIKE` conditions:
     `title LIKE '%football%' AND title NOT LIKE '%tv%' AND title NOT LIKE '%television%' AND title NOT LIKE '%chess%' AND title NOT LIKE '%board game%' AND title NOT LIKE '%toy%' AND title NOT LIKE '%game%'`
3. MULTI-WORD CATEGORIES: If the product category contains multiple words (like "smart tv", "running shoes", "gaming laptop", "air cooler", "washing machine", "back cover"), search for each of them individually in the 'title' column using AND (e.g. for 'gaming laptop' use: `title LIKE '%gaming%' AND title LIKE '%laptop%'`, for 'back cover' use: `title LIKE '%back%' AND title LIKE '%cover%'`). 
   CRITICAL WARNING: Never search for a multi-word category as a single string (e.g. `title LIKE '%smart tv%'` or `title LIKE '%air cooler%'`) because other words might be in between (e.g., 'Smart Google TV' or 'Air Personal Cooler'). You MUST always split them into separate LIKE clauses joined by AND (e.g., for smart tv use: `title LIKE '%smart%' AND title LIKE '%tv%'`). Do NOT just search for one word like '%gaming%', as it will return other gaming accessories (e.g. gaming mice) instead of laptops.
4. PRECISE AC / AIR CONDITIONER FILTER: For "AC", "air conditioner", or "split ac", search using:
   `(title LIKE '%air conditioner%' OR title LIKE '%air-conditioner%' OR title LIKE '% ac %' OR title LIKE 'ac %' OR title LIKE '% ac' OR title LIKE '%split ac%' OR title LIKE '%window ac%')`
   WARNING: Never use `title LIKE '%ac%'` (without word boundaries/spaces), because this raw substring matches unrelated words like 'capacity', 'compact', 'bacterial', 'black', and 'package', which will return air coolers and bags instead of air conditioners.
5. SYNONYMS: Use OR conditions for synonyms. For example:
   - For "fridge" or "refrigerator", search using: `(title LIKE '%fridge%' OR title LIKE '%refrigerator%')`
6. PRECISE PHONE / SMARTPHONE / MOBILE FILTER (ONLY when asking for phones, NOT phone accessories): E-commerce phone listings often omit the words "phone" or "smartphone" and instead use model/brand names (e.g., "Samsung Galaxy F70e 5G", "Nothing Phone (3)", "iPhone 15"). When the user asks for a "phone", "smartphone", or "mobile" (the device itself, NOT accessories like covers/cases), you MUST use the exact parenthesized format below to group the OR conditions together, otherwise operator precedence will cause incorrect results. Never omit the outer parentheses of the OR conditions:
   `((title LIKE '%phone%' OR title LIKE '%smartphone%' OR title LIKE '%mobile%' OR title LIKE '%galaxy%' OR title LIKE '%iphone%' OR title LIKE '%5g%' OR title LIKE '%gb storage%') AND title NOT LIKE '%laptop%' AND title NOT LIKE '%chromebook%' AND title NOT LIKE '%notebook%' AND title NOT LIKE '%case%' AND title NOT LIKE '%cover%' AND title NOT LIKE '%adapter%')`
   CRITICAL: Do NOT use this phone filter or its NOT LIKE exclusions when the user is asking for phone ACCESSORIES like "back cover", "case", "screen protector", "charger", etc. If the user asks for a "Nothing 3 back cover" or "iPhone 15 case", search for the accessory type directly (e.g., `title LIKE '%back%' AND title LIKE '%cover%' AND title LIKE '%nothing%'`). Do NOT add `NOT LIKE '%cover%'` or `NOT LIKE '%case%'` when the user is explicitly asking for covers or cases.
7. HYPHENATED WORDS OR MODEL CODES (CRITICAL): If the user question contains any hyphenated terms, model codes, or combined alphanumeric descriptors (e.g., "samsung-s24", "oneplus-12r", "split-ac", "s24-ultra"), you MUST split them at the hyphen or word boundaries and search for each term/code individually using AND operators (e.g., `title LIKE '%samsung%' AND title LIKE '%s24%'`). Never search for hyphenated terms as a single literal string (like `title LIKE '%samsung-s24%'` or `title LIKE '%s24-ultra%'`) because product titles in the database do not contain hyphens and instead list them as separate words (e.g., "Samsung Galaxy S24 Ultra").
8. COMPOUND AND SPLIT WORDS (CRITICAL): E-commerce queries often use compound terms (e.g., "backcover", "powerbank", "smartwatch", "earphone", "aircooler", "soundbar") where listings in the database use separate words (e.g., "back cover", "power bank", "smart watch", "ear phone", "air cooler", "sound bar"). When the user asks for such terms, you MUST search for both the compound version and the split version using OR and AND conditions. For example, for "backcover" or "back cover", you MUST use: `(title LIKE '%backcover%' OR (title LIKE '%back%' AND title LIKE '%cover%'))`. Similarly, for "powerbank", use: `(title LIKE '%powerbank%' OR (title LIKE '%power%' AND title LIKE '%bank%'))`.
9. ACCESSORY-AWARE QUERIES (MOST CRITICAL): When the user asks for product ACCESSORIES (like "back cover", "case", "screen protector", "tempered glass", "charger", "cable", "earbuds", "earphone", "headphone", "sleeve", "bag", "stand", "keyboard", "mouse"), you MUST:
   a) Search for the accessory type in the title (e.g., `title LIKE '%back%' AND title LIKE '%cover%'`).
   b) If the user specifies a device brand or model (e.g., "Samsung S24", "Nothing 3", "iPhone 15"), add those as additional AND conditions on the TITLE column ONLY (e.g., `AND title LIKE '%samsung%' AND title LIKE '%s24%'`). 
   c) NEVER add NOT LIKE conditions for the very product the user is searching for. If the user asks for "covers", NEVER add `NOT LIKE '%cover%'`. If they ask for "cases", NEVER add `NOT LIKE '%case%'`.
   d) Keep the query SIMPLE — just filter for the accessory type + brand/model + price. Do NOT add unrelated NOT LIKE exclusions.
   e) CRITICAL BRAND COLUMN WARNING: For accessories, the `brand` column stores the ACCESSORY MANUFACTURER (e.g., Spigen, CASEVIBE, KWINE), NOT the device brand (e.g., Samsung, Apple, Nothing). So when the user asks for "Samsung S24 back cover", do NOT add `brand LIKE '%samsung%'` because the cover's brand is Spigen/CASEVIBE, not Samsung. Only use `title LIKE '%samsung%'` to match the device name in the product title. Only use the `brand` column when the user explicitly asks for an accessory by its manufacturer brand (e.g., "Spigen case for iPhone").
   Examples:
   - "nothing 3 back cover under 500" -> `SELECT * FROM product WHERE title LIKE '%back%' AND title LIKE '%cover%' AND title LIKE '%nothing%' AND price < 500`
   - "samsung s24 case" -> `SELECT * FROM product WHERE title LIKE '%case%' AND title LIKE '%samsung%' AND title LIKE '%s24%'`
   - "iphone 15 screen protector" -> `SELECT * FROM product WHERE title LIKE '%screen%' AND title LIKE '%protector%' AND title LIKE '%iphone%' AND title LIKE '%15%'`
   - "boat earbuds under 1000" -> `SELECT * FROM product WHERE title LIKE '%earbuds%' AND title LIKE '%boat%' AND price < 1000`
   - "spigen case for samsung s25" -> `SELECT * FROM product WHERE title LIKE '%case%' AND title LIKE '%samsung%' AND title LIKE '%s25%' AND brand LIKE '%spigen%'`
10. COMMON-WORD BRAND NAMES (CRITICAL): Many popular e-commerce brands have names that are common English words. You MUST recognize and preserve these as brand names when they appear in product queries, and filter for them using `title LIKE '%brand%'`. Common-word brands include: "Nothing" (phone brand), "Boat" (audio brand), "Noise" (smartwatch brand), "Realme", "OnePlus", "Apple", "Google", "Fire-Boltt", "Zebronics", "Portronics", "Ambrane", "Redmi", "POCO". Never ignore or drop brand names from the query. For example, "nothing 3 back cover" must include `title LIKE '%nothing%'` in the WHERE clause. Remember: for accessories, the device brand belongs in the title search, not the brand column (see Rule 9e).

CRITICAL REASONING LENGTH CONSTRAINT: You MUST keep your internal reasoning or thinking process (everything inside the <think>...</think> tags) extremely brief, short, and concise (maximum 3-4 sentences). Do not write a long essay. Proceed to generate the <SQL> tag as quickly as possible.

Create a single SQL query for the question provided. 
The query should have all the fields in SELECT clause (i.e. SELECT *)

Just the SQL query is needed, nothing more. Always provide the SQL in between the <SQL></SQL> tags.
If the input is a greeting (e.g. "hi", "hello", "hey", "good morning") or general conversational chitchat unrelated to product database queries, do NOT generate any <SQL></SQL> tags or queries. Instead, reply directly with a friendly, conversational response assisting the user on what they can ask (e.g., "Hello! I can help you search our products or answer store FAQs. What are you looking for today?")."""


comprehension_prompt = """You are an expert in understanding the context of the question and replying based on the data pertaining to the question provided. You will be provided with Question: and Data:. The data will be in the form of an array or a dataframe or dict. Reply based on only the data provided as Data for answering the question asked as Question. Do not write anything like 'Based on the data' or any other technical words. Just a plain simple natural language response.
The Data would always be in context to the question asked. For example is the question is "What is the average rating?" and data is "4.3", then answer should be "The average rating for the product is 4.3". So make sure the response is curated with the question and data. Make sure to note the column names to have some context, if needed, for your response.
There can also be cases where you are given an entire dataframe in the Data: field. Always remember that the data field contains the answer of the question asked. All you need to do is to always reply in the following format when asked about a product: 
Product title, price in indian rupees, discount percentage, rating, and then the actual product link formatted as a markdown hyperlink [View Product](URL). Replace the "URL" with the actual value from the 'product_link' column. Take care that all the products are listed in list format, one line after the other. Not as a paragraph. Never output the literal text '<link>'.
For example:
1. ASUS ExpertBook P1 Laptop: Rs. 45,990 (50% off), Rating: 4.6 [View Product](https://www.flipkart.com/asus-expertbook-p1...)
2. Samsung Galaxy Book4: Rs. 62,990 (21% off), Rating: 4.3 [View Product](https://www.flipkart.com/samsung-galaxy-book4...)
3. Motorola Motobook 60 Pro: Rs. 69,990 (37% off), Rating: 4.4 [View Product](https://www.flipkart.com/motorola-motobook-60...)

"""


import time



def retry_on_rate_limit(max_retries=8, initial_delay=1):
    """Auto-retry on rate limit / decommissioned errors.
    
    Strategy (per attempt):
      1. Switch to the next model in FALLBACK_MODELS.
      2. Every time we've cycled through ALL models, also rotate
         to the next API key (if multiple keys exist in .env).
    This ensures we exhaust all model+key combinations before giving up.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            delay = initial_delay
            models_tried_on_key = 0
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    err_msg = str(e)
                    err_lower = err_msg.lower()
                    is_retriable = any(k in err_lower for k in [
                        "429", "rate_limit", "ratelimiterror", "overloaded",
                        "decommissioned", "not_found", "invalid_request_error",
                        "tokens per day", "tokens per minute", "request_limit",
                        "resource_exhausted", "service_unavailable",
                    ])
                    
                    if is_retriable:
                        # --- Rotate model ---
                        current_model = os.environ.get('GROQ_MODEL', FALLBACK_MODELS[0])
                        try:
                            curr_idx = FALLBACK_MODELS.index(current_model)
                            next_idx = (curr_idx + 1) % len(FALLBACK_MODELS)
                        except ValueError:
                            next_idx = 0
                        next_model = FALLBACK_MODELS[next_idx]
                        os.environ['GROQ_MODEL'] = next_model
                        models_tried_on_key += 1
                        
                        # --- Rotate API key after cycling through all models ---
                        if models_tried_on_key >= len(FALLBACK_MODELS) and len(API_KEYS) > 1:
                            rotate_api_key()
                            models_tried_on_key = 0
                        
                        print(f"[FAILOVER] attempt {attempt+1}/{max_retries}: "
                              f"'{current_model}' failed -> switching to model='{next_model}', "
                              f"key #{(_current_key_idx % len(API_KEYS)) + 1}/{len(API_KEYS)}")
                        
                        time.sleep(delay)
                        delay = min(delay * 1.5, 15)  # cap backoff at 15s
                    else:
                        raise e
            # Final attempt after exhausting retries
            return func(*args, **kwargs)
        return wrapper
    return decorator


def clean_think_block(text):
    if not text:
        return ""
    if "<SQL>" in text:
        parts = text.split("<SQL>", 1)
        sql_part = "<SQL>" + parts[1]
        prefix = parts[0]
        if "</think>" in prefix:
            prefix = prefix.split("</think>", 1)[1]
        elif "<think>" in prefix:
            prefix = prefix.split("<think>", 1)[0]
        return (prefix.strip() + "\n" + sql_part.strip()).strip()
    if "</think>" in text:
        return text.split("</think>", 1)[1].strip()
    elif "<think>" in text:
        return text.split("<think>", 1)[0].strip()
    return text.strip()


@retry_on_rate_limit(max_retries=8, initial_delay=1)
def generate_sql_query(question):
    client = get_groq_client()
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": sql_prompt,
            },
            {
                "role": "user",
                "content": question,
            }
        ],
        model=os.environ['GROQ_MODEL'],
        temperature=0.2,
        max_tokens=2048
    )

    res = chat_completion.choices[0].message.content
    return clean_think_block(res)


def run_query(query):
    if query.strip().upper().startswith('SELECT'):
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(query, conn)
            return df


@retry_on_rate_limit(max_retries=8, initial_delay=1)
def data_comprehension(question, context):
    client = get_groq_client()
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": comprehension_prompt,
            },
            {
                "role": "user",
                "content": f"QUESTION: {question}. DATA: {context}",
            }
        ],
        model=os.environ['GROQ_MODEL'],
        temperature=0.2,
        max_tokens=2048
    )

    res = chat_completion.choices[0].message.content
    return clean_think_block(res)


@retry_on_rate_limit(max_retries=5, initial_delay=2)
def extract_category_or_search_term(question):
    prompt = f"""You are an expert at extracting the target product search term from a user question.
We want to use this term to search Flipkart and scrape matching products.
Analyze the user's question and extract the most relevant search query.

CRITICAL RULES:
1. BRAND NAMES (CRITICAL): If the user mentions a specific brand name, you MUST include the brand in your search term. This is essential because we need to scrape brand-specific products from Flipkart.
   - Note that brand names can be common words (e.g. "Nothing", "Apple", "Boat", "Realme", "Google", "Noise", "Fire-Boltt"). You MUST treat them as brand names and preserve them in the search term. For example, "nothing 3 back cover" -> "nothing 3 back cover", "boat earbuds" -> "boat earbuds".
2. MODEL NUMBERS / CODES: Preserve model numbers, versions, or specs (e.g. "s24", "15 pro", "2a", "3", "v15") in the search term.
3. REMOVE CONSTRAINTS: Do not include price constraints (like "under 500", "below 10000"), ratings, or conversational preambles in the search term.

Examples:
- "Show me some watches" -> "watches"
- "Do you have split ACs?" -> "split ac"
- "I want to buy running shoes" -> "running shoes"
- "List some budget laptops under 30000" -> "laptops"
- "Which is the cheapest Symphony cooler?" -> "Symphony cooler"
- "Show me iphone 15" -> "iphone 15"
- "Are there ceiling fans?" -> "ceiling fan"
- "Show me double door fridges" -> "refrigerator"
- "Show me washing machines" -> "washing machine"
- "Show me Thomson smart tv under 15000" -> "Thomson smart tv"
- "Show me smart phone under 20000 of samsung brand" -> "Samsung phone"
- "show me nothing 3 back cover under 500 rupee" -> "nothing 3 back cover"
- "do you have nothing phone 2a" -> "nothing phone 2a"
- "I want a Boat earbuds" -> "Boat earbuds"
- "Do you have Realme phones?" -> "Realme phone"

Return ONLY the plain text search term (maximum 4 words), nothing else. Do not wrap in quotes or add preamble. If the question is not about products or is chitchat, return "None".

QUESTION: {question}"""

    chat_completion = client_sql.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model=os.environ['GROQ_MODEL'],
        temperature=0.0,
        max_tokens=50
    )

    res = chat_completion.choices[0].message.content.strip()
    return clean_think_block(res)


def sql_chain(question):
    try:
        sql_query = generate_sql_query(question)
        pattern = "<SQL>(.*?)</SQL>"
        matches = re.findall(pattern, sql_query, re.DOTALL)

        sql_command = matches[0].strip() if (len(matches) > 0) else ""
        if not sql_command or not sql_command.upper().startswith("SELECT"):
            cleaned_response = sql_query.replace("<SQL>", "").replace("</SQL>", "").strip()
            if cleaned_response:
                return cleaned_response
            return "I'm sorry, I couldn't understand your request. You can ask me about our products, store FAQs, shipping, or policies."

        print(sql_command)

        response = run_query(sql_command)
        if response is None:
            return "Sorry, there was a problem executing the product search."

        total_results = len(response)

        # Auto-scrape on demand if no products match the query locally
        if total_results == 0:
            search_term = extract_category_or_search_term(question)
            if search_term and search_term.lower() != "none":
                print(f"No products found locally. Attempting to scrape Flipkart live for: '{search_term}'...")
                try:
                    num_scraped = scrape_and_populate_db(search_term, limit=8)
                    if num_scraped > 0:
                        # Retry query after scraping
                        response = run_query(sql_command)
                        if response is not None:
                            total_results = len(response)
                except Exception as scrape_err:
                    print(f"On-demand automatic scraping failed: {scrape_err}")
                    err_msg = str(scrape_err)
                    if "Internet connection" in err_msg or "ERR_INTERNET_DISCONNECTED" in err_msg:
                        return "I tried to search Flipkart live for this product, but it seems your internet connection is disconnected. Please check your network connection and try again."
                    elif "DNS name resolution" in err_msg or "ERR_NAME_NOT_RESOLVED" in err_msg:
                        return "I tried to search Flipkart live, but name resolution failed. Please check your internet connection."
                    elif "Connection timed out" in err_msg or "ERR_CONNECTION_TIMED_OUT" in err_msg:
                        return "I tried to search Flipkart live, but the connection timed out. Flipkart may be currently offline or blocking automated requests."

        if 'product_link' in response.columns:
            response['product_link'] = response['product_link'].apply(lambda x: x.split('?')[0] if isinstance(x, str) else x)

        if total_results > 10:
            context = response.head(10).to_dict(orient='records')
        else:
            context = response.to_dict(orient='records')

        answer = data_comprehension(question, context)
        
        if total_results > 10:
            answer += f"\n\n*(Showing top 10 out of {total_results} matching products)*"
        return answer
    except Exception as chain_err:
        err_msg = str(chain_err)
        if "APIConnectionError" in err_msg or "Connection error" in err_msg or "Failed to establish a new connection" in err_msg or "request failed" in err_msg:
            return "I cannot reach the AI model server. It seems your internet connection is disconnected. Please check your network connection and try again."
        if "Internet connection" in err_msg or "ERR_INTERNET_DISCONNECTED" in err_msg:
            return "I tried to search Flipkart live for this product, but it seems your internet connection is disconnected. Please check your network connection and try again."
        raise chain_err


def sql_chain_structured(question):
    try:
        sql_query = generate_sql_query(question)
        pattern = "<SQL>(.*?)</SQL>"
        matches = re.findall(pattern, sql_query, re.DOTALL)

        sql_command = matches[0].strip() if (len(matches) > 0) else ""
        if not sql_command or not sql_command.upper().startswith("SELECT"):
            cleaned_response = sql_query.replace("<SQL>", "").replace("</SQL>", "").strip()
            if cleaned_response:
                return cleaned_response, []
            return "I'm sorry, I couldn't understand your request. You can ask me about our products, store FAQs, shipping, or policies.", []

        print(sql_command)

        response = run_query(sql_command)
        if response is None:
            return "Sorry, there was a problem executing the product search.", []

        total_results = len(response)

        # Auto-scrape on demand if no products match the query locally
        if total_results == 0:
            search_term = extract_category_or_search_term(question)
            if search_term and search_term.lower() != "none":
                print(f"No products found locally. Attempting to scrape Flipkart live for: '{search_term}'...")
                try:
                    num_scraped = scrape_and_populate_db(search_term, limit=8)
                    if num_scraped > 0:
                        # Retry query after scraping
                        response = run_query(sql_command)
                        if response is not None:
                            total_results = len(response)
                except Exception as scrape_err:
                    print(f"On-demand automatic scraping failed: {scrape_err}")
                    err_msg = str(scrape_err)
                    if "Internet connection" in err_msg or "ERR_INTERNET_DISCONNECTED" in err_msg:
                        return "I tried to search Flipkart live for this product, but it seems your internet connection is disconnected. Please check your network connection and try again.", []
                    elif "DNS name resolution" in err_msg or "ERR_NAME_NOT_RESOLVED" in err_msg:
                        return "I tried to search Flipkart live, but name resolution failed. Please check your internet connection.", []
                    elif "Connection timed out" in err_msg or "ERR_CONNECTION_TIMED_OUT" in err_msg:
                        return "I tried to search Flipkart live, but the connection timed out. Flipkart may be currently offline or blocking automated requests.", []

        if 'product_link' in response.columns:
            response['product_link'] = response['product_link'].apply(lambda x: x.split('?')[0] if isinstance(x, str) else x)

        if total_results > 10:
            context = response.head(10).to_dict(orient='records')
        else:
            context = response.to_dict(orient='records')

        answer = data_comprehension(question, context)
        
        if total_results > 10:
            answer += f"\n\n*(Showing top 10 out of {total_results} matching products)*"
        return answer, context
    except Exception as chain_err:
        err_msg = str(chain_err)
        if "APIConnectionError" in err_msg or "Connection error" in err_msg or "Failed to establish a new connection" in err_msg or "request failed" in err_msg:
            return "I cannot reach the AI model server. It seems your internet connection is disconnected. Please check your network connection and try again.", []
        if "Internet connection" in err_msg or "ERR_INTERNET_DISCONNECTED" in err_msg:
            return "I tried to search Flipkart live for this product, but it seems your internet connection is disconnected. Please check your network connection and try again.", []
        return f"Error executing request: {err_msg}", []


def clean_search_term(term: str) -> str:
    """Cleans a search query and returns a standardized title-case category name candidate."""
    if not term:
        return "Others"
    
    # Lowercase and clean common search noise
    t = term.lower().strip()
    t = re.sub(r'\b(buy|online|cheap|best|latest|top|free shipping|flipkart|amazon|for men|for women|for kids|under|below|above|rs|\d+|rupee|rupees)\b', '', t)
    t = re.sub(r'[^a-z0-9\s]', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    
    if not t or len(t) < 3:
        return "Others"
        
    # Split into words and title case
    words = t.split()
    title_words = [w.capitalize() for w in words]
    
    # Pluralize the last word if it's not already pluralized
    if title_words:
        last_word = title_words[-1]
        if not (last_word.endswith('s') or last_word.endswith('y') or last_word.endswith('ch') or last_word.endswith('sh') or last_word.endswith('x') or last_word.endswith('z')):
            title_words[-1] = last_word + 's'
        elif last_word.endswith('y') and not any(last_word.endswith(x) for x in ['ay', 'ey', 'oy', 'uy']):
            title_words[-1] = last_word[:-1] + 'ies'
        elif last_word.endswith('ch') or last_word.endswith('sh') or last_word.endswith('x'):
            title_words[-1] = last_word + 'es'
            
    return " ".join(title_words)


def scrape_and_populate_db(search_term, limit=25):
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from bs4 import BeautifulSoup
    import sqlite3
    import pandas as pd
    import re
    import time

    options = webdriver.ChromeOptions()
    options.page_load_strategy = 'eager'
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Auto-detect Streamlit Cloud's Chromium binary (Linux)
    import shutil
    chromium_path = shutil.which("chromium") or shutil.which("chromium-browser")
    if chromium_path:
        options.binary_location = chromium_path

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(15)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    try:
        # Step 1: Search Flipkart for the product category
        search_query_clean = search_term.replace('-', ' ')
        website_link = f"https://www.flipkart.com/search?q={search_query_clean.replace(' ', '+')}"
        try:
            driver.get(website_link)
        except Exception as e:
            err_msg = str(e)
            if "ERR_INTERNET_DISCONNECTED" in err_msg:
                raise RuntimeError("Internet connection is disconnected. Please check your network connection and try again.") from e
            elif "ERR_NAME_NOT_RESOLVED" in err_msg:
                raise RuntimeError("DNS name resolution failed. Please verify your internet connection.") from e
            elif "ERR_CONNECTION_TIMED_OUT" in err_msg:
                raise RuntimeError("Connection timed out. Flipkart might be unreachable or blocking request.") from e
            else:
                raise RuntimeError(f"Failed to load search page: {err_msg}") from e
        time.sleep(3)

        # Wait for product links to load
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/p/"]'))
            )
        except Exception:
            print("No products found on search page")
            return 0

        # Collect unique product links from search results
        soup = BeautifulSoup(driver.page_source, 'lxml')
        product_anchors = soup.find_all('a', href=re.compile(r'/p/itm'))
        
        all_links = []
        seen = set()
        for a in product_anchors:
            href = a.get('href', '')
            # Build full URL, strip query params for dedup
            base_href = href.split('?')[0]
            if base_href in seen:
                continue
            seen.add(base_href)
            full_url = f"https://www.flipkart.com{base_href}" if base_href.startswith('/') else base_href
            all_links.append(full_url)
            if len(all_links) >= limit:
                break

        # Step 2: Visit each product page and extract details using BeautifulSoup
        complete_product_details = []
        for product_page_link in all_links:
            try:
                driver.get(product_page_link)
                time.sleep(2)
                
                page_soup = BeautifulSoup(driver.page_source, 'lxml')
                page_text = page_soup.get_text(separator=' ', strip=True)

                # --- Title ---
                title = ''
                # Strategy 1: <title> tag (most reliable - always has full product name)
                title_tag = page_soup.find('title')
                if title_tag:
                    raw_title = title_tag.get_text(strip=True)
                    # Flipkart title format: "Product Name - Buy Product Name ... | Flipkart.com"
                    # Take everything before the first " - Buy" or " | Flipkart" or "- Price"
                    for sep in [' - Buy ', ' | Flipkart', '- Price']:
                        if sep in raw_title:
                            raw_title = raw_title.split(sep)[0]
                            break
                    title = raw_title.strip()

                # Strategy 2: h1 or span with product title classes
                if not title or len(title) < 5:
                    for selector in ['h1', 'span.VU-ZEz', 'h1.yhB1nd']:
                        el = page_soup.select_one(selector)
                        if el and el.get_text(strip=True):
                            title = el.get_text(strip=True)
                            break

                if not title:
                    print(f"Skipping - no title found for {product_page_link}")
                    continue

                # Clean parentheticals like "(16 GB/512 GB SSD)" - keep them for searchability
                # Only remove color variants like "(3 Colors)"
                title = re.sub(r'\s*\(\d+\s*Colors?\)', '', title, flags=re.IGNORECASE)

                # --- Brand ---
                brand = ''
                for selector in ['span.mEh187', 'span.B1GeXm', 'span.G6Xh1M']:
                    el = page_soup.select_one(selector)
                    if el and el.get_text(strip=True):
                        brand = el.get_text(strip=True)
                        break
                if not brand:
                    brand = title.split(' ')[0] if title else 'Generic'

                # --- Price ---
                price = 0
                # Look for the selling price (first ₹ amount on the page in price divs)
                for selector in ['div.Nx9bqj', 'div._30jeq3', 'div.CxhGGd']:
                    el = page_soup.select_one(selector)
                    if el:
                        price_text = el.get_text(strip=True)
                        nums = re.findall(r'\d+', price_text.replace(',', ''))
                        if nums:
                            price = int(''.join(nums))
                            break
                # Fallback: regex on page text
                if price == 0:
                    price_match = re.search(r'₹\s*([0-9,]+)', page_text)
                    if price_match:
                        price = int(price_match.group(1).replace(',', ''))

                # --- Discount ---
                discount = 0.0
                for selector in ['div.UkUFwK', 'div._3Ay6B1']:
                    el = page_soup.select_one(selector)
                    if el:
                        disc_text = el.get_text(strip=True)
                        disc_match = re.search(r'(\d+)\s*%', disc_text)
                        if disc_match:
                            discount = int(disc_match.group(1)) / 100
                            break
                if discount == 0.0:
                    disc_match = re.search(r'(\d+)\s*%\s*off', page_text, re.IGNORECASE)
                    if disc_match:
                        discount = int(disc_match.group(1)) / 100

                # --- Rating ---
                avg_rating = 0.0
                total_ratings = 0

                # Primary: "Ratings and reviews X.X ... based on N ratings"
                rating_review_match = re.search(
                    r'Ratings?\s+and\s+reviews?\s+([1-5]\.?\d?)\s+.*?based\s+on\s+([\d,]+)\s+ratings?',
                    page_text, re.IGNORECASE
                )
                if rating_review_match:
                    try:
                        avg_rating = float(rating_review_match.group(1))
                        total_ratings = int(rating_review_match.group(2).replace(',', ''))
                    except (ValueError, IndexError):
                        pass

                # Fallback 1: CSS selectors (older Flipkart layout)
                if avg_rating == 0.0:
                    for selector in ['div.XQDdHH', 'div._3LWZlK']:
                        el = page_soup.select_one(selector)
                        if el:
                            try:
                                avg_rating = float(el.get_text(strip=True))
                            except ValueError:
                                pass
                            break

                # Fallback 2: "X.X | Y,YYY Ratings" pattern
                if avg_rating == 0.0:
                    rating_pattern = re.search(r'([1-5]\.?\d?)\s*[|&]\s*([\d,]+)\s*Ratings?', page_text, re.IGNORECASE)
                    if rating_pattern:
                        try:
                            avg_rating = float(rating_pattern.group(1))
                            if total_ratings == 0:
                                total_ratings = int(rating_pattern.group(2).replace(',', ''))
                        except ValueError:
                            pass

                # Fallback 3: just find any "X.X" followed by rating context
                if avg_rating == 0.0:
                    simple_rating = re.search(r'([1-5]\.\d)\s+(?:Very Good|Good|Average|Poor|Excellent)', page_text)
                    if simple_rating:
                        try:
                            avg_rating = float(simple_rating.group(1))
                        except ValueError:
                            pass

                # Total ratings fallback
                if total_ratings == 0:
                    total_match = re.search(r'([\d,]+)\s*Ratings?', page_text, re.IGNORECASE)
                    if total_match:
                        try:
                            total_ratings = int(total_match.group(1).replace(',', ''))
                        except ValueError:
                            pass

                # --- Image URL ---
                image_url = ''
                exclude_sizes = ['/70/70/', '/80/80/', '/160/210/', '/120/120/', '/120/150/', '/40/40/', '/48/48/', '/30/30/', '/24/24/', '/10/10/']
                
                # Check specific product detail selectors first
                for selector in ['img._0DkuPH', 'img.DByoR4', 'img.jzoB4e', 'img.UHDDFP', 'img._53u2j-']:
                    el = page_soup.select_one(selector)
                    if el and el.get('src') and 'logo' not in el.get('src', '').lower():
                        src = el.get('src')
                        if not any(sz in src for sz in exclude_sizes):
                            image_url = src
                            break
                
                # Fallback to scanning all img tags, filtering out thumbnails/recommendations
                if not image_url:
                    for img in page_soup.find_all('img'):
                        src = img.get('src', '')
                        if ('rukminim2.flixcart.com/image/' in src or 'rukminim1.flixcart.com/image/' in src or '/xif0q/' in src) and 'logo' not in src.lower() and 'promo' not in src.lower():
                            if not any(sz in src for sz in exclude_sizes):
                                image_url = src
                                break

                description = page_text[:2000] if page_text else title
                complete_product_details.append([
                    product_page_link, title, brand, price, discount, avg_rating, total_ratings, image_url, description
                ])
                print(f"  [OK] {brand} | {title[:60]}... | Rs.{price} | {discount*100:.0f}% off | Rating: {avg_rating} | Image: {bool(image_url)}")

            except Exception as item_err:
                err_msg = str(item_err)
                if "ERR_INTERNET_DISCONNECTED" in err_msg or "disconnected" in err_msg:
                    raise RuntimeError("Internet connection was lost during scraping. Please check your network connection.") from item_err
                print(f"Skipping product {product_page_link}: {item_err}")

        # Insert/Update using modular components
        if complete_product_details:
            from database_service import get_connection
            from category_classifier import CategoryClassifier
            from category_normalizer import CategoryNormalizer
            from category_manager import CategoryManager
            from duplicate_detector import DuplicateDetector
            from product_repository import ProductRepository
            
            classifier = CategoryClassifier()
            category_manager = CategoryManager(get_connection)
            product_repository = ProductRepository(get_connection)
            
            success_count = 0
            for item in complete_product_details:
                link, title, brand, price, discount, avg_rating, total_ratings, image_url, description = item
                
                # Extract clean brand/title
                brand = str(brand).strip()
                title = str(title).strip()
                if not title:
                    continue
                    
                product_id = DuplicateDetector.extract_product_id(link, title)
                product_data = {
                    "product_id": product_id,
                    "product_link": link,
                    "title": title,
                    "brand": brand,
                    "price": price,
                    "discount": discount,
                    "avg_rating": avg_rating,
                    "rating": avg_rating,
                    "total_ratings": total_ratings,
                    "availability": "In Stock",
                    "image": image_url,
                    "image_url": image_url,
                    "description": description
                }
                
                # Dynamic Category detection and creation
                category_name, confidence, source, reason = classifier.classify(product_data)
                normalized_cat = CategoryNormalizer.normalize(category_name)
                
                # If classified as "Others", fallback to clean search term candidate
                if normalized_cat == "Others":
                    candidate = clean_search_term(search_term)
                    if candidate != "Others":
                        normalized_cat = CategoryNormalizer.normalize(candidate)
                        source = "Search_Term_Fallback"
                        reason = f"Classification is 'Others' (low confidence). Using cleaned search query '{search_term}' to assign to dynamic category '{normalized_cat}'."
                        confidence = 0.50 # Moderate confidence for search term fallback
                
                # Fetch or create
                category_id, slug = category_manager.get_or_create_category(normalized_cat)
                
                product_data["category_id"] = category_id
                product_data["category_name"] = normalized_cat
                product_data["confidence_score"] = confidence
                product_data["classification_source"] = source
                
                # Save product in DB (handles insert/update correctly)
                product_repository.save_product(product_data)
                success_count += 1
                
                # Detailed category scoring log (Requirement 11)
                print(f"\n[SCRAPER-PIPELINE] Product: {title[:50]}...")
                print(f"  Detected Category: {normalized_cat} (Confidence: {confidence*100:.1f}%)")
                print(f"  Reason: {reason}")
                
            # Recalculate category counts
            category_manager.recalculate_all_counts()
            print(f"Successfully scraped, classified, and processed {success_count} products for '{search_term}'!")
            return success_count
        return 0
    finally:
        driver.quit()


def extract_specs_from_title(title):
    import re
    title_lower = title.lower()
    
    # Try to extract parenthetical info first
    parenthetical = re.search(r'\(([^)]+)\)', title)
    if parenthetical:
        p_text = parenthetical.group(1)
        if any(k in p_text.lower() for k in ['ram', 'ssd', 'storage', 'gb', 'tb', 'core', 'ryzen', 'capacity', 'litre', 'inch']):
            return p_text.strip()
            
    specs = []
    
    # Laptop patterns
    if any(k in title_lower for k in ['laptop', 'notebook', 'macbook', 'expertbook', 'book']):
        # Graphics
        gpu = re.search(r'(rtx\s*\d+|gtx\s*\d+|iris|intel hd|radeon)', title_lower, re.IGNORECASE)
        if gpu: specs.append(gpu.group(1).upper())
        # RAM
        ram = re.search(r'(\d+\s*gb\s*(?:ram|lpddr\d|ddr\d))', title_lower, re.IGNORECASE)
        if ram: specs.append(ram.group(1).upper())
        # SSD/HDD
        storage = re.search(r'(\d+\s*(?:gb|tb)\s*(?:ssd|hdd))', title_lower, re.IGNORECASE)
        if storage: specs.append(storage.group(1).upper())
        # Screen Size
        screen = re.search(r'(\d+(?:\.\d+)?\s*(?:inch|in|\"))', title_lower, re.IGNORECASE)
        if screen: specs.append(screen.group(1).replace('in', '-inch'))
        
    # Phone patterns
    elif any(k in title_lower for k in ['phone', 'smartphone', 'mobile', 'galaxy', 'iphone']):
        # RAM/Storage
        storage = re.search(r'(\d+\s*(?:gb|tb)\s*(?:storage|rom))', title_lower, re.IGNORECASE)
        if storage: specs.append(storage.group(1).upper())
        ram = re.search(r'(\d+\s*gb\s*(?:ram))', title_lower, re.IGNORECASE)
        if ram: specs.append(ram.group(1).upper())
        # 5G
        five_g = re.search(r'\b(5g|4g)\b', title_lower, re.IGNORECASE)
        if five_g: specs.append(five_g.group(1).upper())
        
    # Air Cooler/Appliance patterns
    elif any(k in title_lower for k in ['cooler', 'ac', 'refrigerator', 'fridge', 'washing']):
        # Capacity
        capacity = re.search(r'(\d+\s*(?:l|litre|litres|kg))', title_lower, re.IGNORECASE)
        if capacity: specs.append(capacity.group(1).title())
        # Speed/Inverter
        if 'inverter' in title_lower: specs.append("Inverter Compatible")
        if 'honeycomb' in title_lower: specs.append("Honeycomb Pads")
        
    if specs:
        return ' • '.join(specs)
        
    fallback = re.findall(r'(\d+\s*(?:gb|tb|l|kg|inch))', title_lower, re.IGNORECASE)
    if fallback:
        return ' • '.join([f.upper() for f in fallback[:3]])
        
    return "Standard Edition"


if __name__ == "__main__":
    question = "Show top 3 shoes in descending order of rating"
    answer = sql_chain(question)
    print(answer)

