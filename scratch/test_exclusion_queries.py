import os
import sys
sys.path.append('app')

from dotenv import load_dotenv
load_dotenv('app/.env')

from sql import generate_sql_query

print("Testing SQL Query for 'fans':")
try:
    print(generate_sql_query("fans"))
except Exception as e:
    print(f"Error: {e}")

print("\nTesting SQL Query for 'laptops':")
try:
    print(generate_sql_query("laptops"))
except Exception as e:
    print(f"Error: {e}")
