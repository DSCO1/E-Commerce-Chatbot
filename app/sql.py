from groq import Groq
import os
import re
import sqlite3
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from pandas import DataFrame

load_dotenv(Path(__file__).parent / ".env")

GROQ_MODEL = os.getenv('GROQ_MODEL')

db_path = Path(__file__).parent / "db.sqlite"

client_sql = Groq()

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
1. ALWAYS FILTER BY PRODUCT TYPE: You MUST always identify the product type or category (e.g. laptop, cooler, fan, shoe, watch, phone, refrigerator, washing machine, AC, etc.) from the user's question and search for it in the 'title' column. Never write a query without filtering the product category, otherwise it will return incorrect types of products (e.g., returning air coolers when asked for a laptop).
2. MULTI-WORD CATEGORIES: If the product category contains multiple words (like "smart tv", "running shoes", "gaming laptop", "air cooler", "washing machine"), search for each of them individually in the 'title' column using AND (e.g. for 'gaming laptop' use: `title LIKE '%gaming%' AND title LIKE '%laptop%'`). 
   CRITICAL WARNING: Never search for a multi-word category as a single string (e.g. `title LIKE '%smart tv%'` or `title LIKE '%air cooler%'`) because other words might be in between (e.g., 'Smart Google TV' or 'Air Personal Cooler'). You MUST always split them into separate LIKE clauses joined by AND (e.g., for smart tv use: `title LIKE '%smart%' AND title LIKE '%tv%'`). Do NOT just search for one word like '%gaming%', as it will return other gaming accessories (e.g. gaming mice) instead of laptops.
3. PRECISE AC / AIR CONDITIONER FILTER: For "AC", "air conditioner", or "split ac", search using:
   `(title LIKE '%air conditioner%' OR title LIKE '%air-conditioner%' OR title LIKE '% ac %' OR title LIKE 'ac %' OR title LIKE '% ac' OR title LIKE '%split ac%' OR title LIKE '%window ac%')`
   WARNING: Never use `title LIKE '%ac%'` (without word boundaries/spaces), because this raw substring matches unrelated words like 'capacity', 'compact', 'bacterial', 'black', and 'package', which will return air coolers and bags instead of air conditioners.
4. SYNONYMS: Use OR conditions for synonyms. For example:
   - For "fridge" or "refrigerator", search using: `(title LIKE '%fridge%' OR title LIKE '%refrigerator%')`
5. PRECISE PHONE / SMARTPHONE / MOBILE FILTER: E-commerce phone listings often omit the words "phone" or "smartphone" and instead use model/brand names (e.g., "Samsung Galaxy F70e 5G", "Nothing Phone (3)", "iPhone 15"). When the user asks for a "phone", "smartphone", or "mobile", you MUST use the exact parenthesized format below to group the OR conditions together, otherwise operator precedence will cause incorrect results. Never omit the outer parentheses of the OR conditions:
   `((title LIKE '%phone%' OR title LIKE '%smartphone%' OR title LIKE '%mobile%' OR title LIKE '%galaxy%' OR title LIKE '%iphone%' OR title LIKE '%5g%' OR title LIKE '%gb storage%') AND title NOT LIKE '%laptop%' AND title NOT LIKE '%chromebook%' AND title NOT LIKE '%notebook%' AND title NOT LIKE '%case%' AND title NOT LIKE '%cover%' AND title NOT LIKE '%adapter%')`

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


def generate_sql_query(question):
    chat_completion = client_sql.chat.completions.create(
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
        max_tokens=1024
    )

    return chat_completion.choices[0].message.content



def run_query(query):
    if query.strip().upper().startswith('SELECT'):
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(query, conn)
            return df


def data_comprehension(question, context):
    chat_completion = client_sql.chat.completions.create(
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

    return chat_completion.choices[0].message.content



def extract_category_or_search_term(question):
    prompt = f"""You are an expert at extracting the target product search term from a user question.
We want to use this term to search Flipkart and scrape matching products.
Analyze the user's question and extract the most relevant search query.

CRITICAL RULE: If the user mentions a specific brand name, you MUST include the brand in your search term. This is essential because we need to scrape brand-specific products from Flipkart.

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
- "I want a Boat earbuds" -> "Boat earbuds"
- "Do you have Realme phones?" -> "Realme phone"

Return ONLY the plain text search term (maximum 3 words), nothing else. Do not wrap in quotes or add preamble. If the question is not about products or is chitchat, return "None".

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

    return chat_completion.choices[0].message.content.strip()


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
                    num_scraped = scrape_and_populate_db(search_term, limit=10)
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


def scrape_and_populate_db(search_term, limit=10):
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
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    try:
        # Step 1: Search Flipkart for the product category
        website_link = f"https://www.flipkart.com/search?q={search_term.replace(' ', '+')}"
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

                complete_product_details.append([
                    product_page_link, title, brand, price, discount, avg_rating, total_ratings
                ])
                print(f"  [OK] {brand} | {title[:60]}... | Rs.{price} | {discount*100:.0f}% off | Rating: {avg_rating}")

            except Exception as item_err:
                err_msg = str(item_err)
                if "ERR_INTERNET_DISCONNECTED" in err_msg or "disconnected" in err_msg:
                    raise RuntimeError("Internet connection was lost during scraping. Please check your network connection.") from item_err
                print(f"Skipping product {product_page_link}: {item_err}")

        # Insert into SQLite
        if complete_product_details:
            df = pd.DataFrame(complete_product_details,
                              columns=['product_link', 'title', 'brand', 'price', 'discount', 'avg_rating', 'total_ratings'])
            # Clean values
            for col in ['brand', 'title']:
                df[col] = df[col].astype(str).str.strip()

            # Drop rows with empty titles
            df = df[df['title'].str.len() > 0]

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Ensure table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS product (
                    product_link TEXT UNIQUE,
                    title TEXT,
                    brand TEXT,
                    price INTEGER,
                    discount REAL,
                    avg_rating REAL,
                    total_ratings INTEGER
                )
            """)
            conn.commit()

            # Clear only the duplicate records we are about to scrape/refresh to avoid duplicates
            placeholders = ','.join(['?'] * len(df))
            cursor.execute(f"DELETE FROM product WHERE product_link IN ({placeholders})", list(df['product_link']))
            conn.commit()

            df.to_sql('product', conn, if_exists='append', index=False)
            conn.close()
            print(f"Successfully scraped and inserted {len(df)} products for '{search_term}'!")
            return len(df)
        return 0
    finally:
        driver.quit()


if __name__ == "__main__":
    question = "Show top 3 shoes in descending order of rating"
    answer = sql_chain(question)
    print(answer)
