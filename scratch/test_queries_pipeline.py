"""Consolidated script for e-commerce chatbot query execution tests.

Combines functionality from:
- test_queries.py
- test_20_existing_products.py
- test_20_product_queries.py
- streamlit_pipeline_test.py
- e2e_test_20_products.py
"""

import sys
import re
import time
from pathlib import Path

# Add project root directory to Python path
sys.path.append(str(Path(__file__).parent.parent / "app"))
from router import router
from sql import sql_chain, generate_sql_query, run_query
from faq import faq_chain, ingest_faq_data

# Ensure FAQ data is loaded (same as main.py does on startup)
faqs_path = Path(__file__).parent.parent / "app" / "Resources" / "FAQ.csv"
ingest_faq_data(faqs_path)

def ask(query):
    """Simulates main.py routing & response pipeline"""
    route = router(query).name
    if route == 'faq':
        return route, faq_chain(query)
    else:
        return 'sql', sql_chain(query)

# Test datasets
test_7_queries = [
    "Show me watches",
    "Do you have air coolers?",
    "Show me split ACs",
    "List some budget laptops",
    "Are there ceiling fans?",
    "Show me double door fridges",
    "Show me washing machines"
]

test_20_complex_queries = [
    "Show me personal air coolers from Orient under 6000",
    "List top rated laptops with discount more than 20 percent",
    "Do you have any double door refrigerators from LG under 35000?",
    "Show me split ACs with a rating of 4 or higher",
    "I want a budget laptop under 30000 with good ratings",
    "Are there any desert air coolers from Thomson on sale?",
    "Show me the cheapest washing machines available",
    "Do you have LG front load washing machines under 45000?",
    "List smartwatches under 5000 with rating above 4",
    "Show me desert coolers with capacity over 80 liters",
    "Show me the best rated air conditioners with discount above 10 percent",
    "Do you have single door refrigerators from Haier under 20000?",
    "Show me some Orient ceiling fans under 3000",
    "What is the price of the cheapest gaming laptop?",
    "Are there any personal coolers under 5000 with rating above 3.5?",
    "Show me LG refrigerators with discount more than 15 percent",
    "List BAJAJ air coolers sorted by price",
    "Do you have any smartwatches from brand Fossil?",
    "Show me window ACs under 30000",
    "Show me Lenovo laptops under 50000"
]

test_20_standard_queries = [
    "Show me laptops under 40000",
    "Do you have Orient air coolers?",
    "Show me split ACs with a rating above 4",
    "What washing machines do you have under 20000?",
    "Do you have LG double door refrigerators?",
    "Show me some ceiling fans under 3000",
    "List smartwatches under 3000",
    "Do you have any action cameras?",
    "Show me trimmers from brand Nova",
    "Do you have bluetooth speakers under 2000?",
    "List mixer grinders under 4000",
    "Show me induction cooktops on sale",
    "Do you have rechargeable mosquito rackets?",
    "Show me indoor insect killers",
    "List juicers with discount more than 25 percent",
    "Do you have gaming mice under 1000?",
    "Show me wireless mice",
    "List smart bands from Yash",
    "Show me window ACs",
    "Do you have single door refrigerators from Haier?"
]

def run_7_queries_test():
    print("=" * 70)
    print("BASIC 7-QUERY EVALUATION")
    print("=" * 70)
    for idx, q in enumerate(test_7_queries, start=1):
        print(f"\n[{idx}/7] Query: '{q}'")
        route = router(q).name
        print(f"  Route: '{route}'")
        if route == 'sql':
            response = sql_chain(q)
            print(f"  Response Preview: {response.strip().split(chr(10))[0][:120]}...")
        else:
            print("  Routed to FAQ. Response omitted.")
    print()

def verify_sql_generation(queries_list, test_title):
    print("=" * 70)
    print(f"SQL GENERATION & EXECUTION VERIFICATION: {test_title}")
    print("=" * 70)
    failures = 0
    for idx, q in enumerate(queries_list, start=1):
        print(f"\n[{idx}/{len(queries_list)}] Query: '{q}'")
        try:
            sql_query = generate_sql_query(q)
            pattern = "<SQL>(.*?)</SQL>"
            matches = re.findall(pattern, sql_query, re.DOTALL)
            sql_command = matches[0].strip() if (len(matches) > 0) else ""
            
            if not sql_command:
                print("  Warning: No SQL generated, likely treated as conversational.")
                continue
                
            print(f"  SQL Generated: {sql_command}")
            res = run_query(sql_command)
            if res is None:
                print("  ERROR: Run returned None (Execution error).")
                failures += 1
            else:
                print(f"  SUCCESS: Returned {len(res)} rows.")
        except Exception as e:
            print(f"  ERROR: Exception raised: {e}")
            failures += 1
            
    print(f"\nVerification completed. Total failures: {failures}/{len(queries_list)}")
    print()

def run_e2e_pipeline_test():
    print("=" * 70)
    print("STREAMLIT PIPELINE TEST: 20 Standard Queries with Rate-Limit Handling")
    print("=" * 70)
    passed = 0
    failed = 0
    for idx, q in enumerate(test_20_standard_queries, start=1):
        print(f"\n[{idx}/20] Query: '{q}'")
        try:
            route, response = ask(q)
            print(f"  Route: {route}")
            lines = response.strip().split('\n')
            for line in lines[:2]:
                print(f"  > {line[:120]}")
            if len(lines) > 2:
                print(f"  > ... ({len(lines) - 2} more lines)")
            passed += 1
        except Exception as e:
            err = str(e)
            if "429" in err or "rate_limit" in err or "APIConnectionError" in err:
                print(f"  RATE LIMITED (Groq API) - sleeping 30s before retry...")
                time.sleep(30)
                try:
                    route, response = ask(q)
                    print(f"  Route: {route}")
                    lines = response.strip().split('\n')
                    for line in lines[:2]:
                        print(f"  > {line[:120]}")
                    passed += 1
                except Exception as e2:
                    print(f"  FAILED after retry: {str(e2)[:120]}")
                    failed += 1
            else:
                print(f"  FAILED: {err[:120]}")
                failed += 1
        time.sleep(3.5)  # Pause to prevent rate limits
        
    print(f"\n{'=' * 70}")
    print(f"RESULTS: {passed} PASSED, {failed} FAILED out of 20")
    print(f"{'=' * 70}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "--basic":
            run_7_queries_test()
        elif mode == "--complex-sql":
            verify_sql_generation(test_20_complex_queries, "20 Complex Queries")
        elif mode == "--standard-sql":
            verify_sql_generation(test_20_standard_queries, "20 Standard Queries")
        elif mode == "--pipeline":
            run_e2e_pipeline_test()
    else:
        # Default behavior: run basic 7 queries evaluation
        run_7_queries_test()
