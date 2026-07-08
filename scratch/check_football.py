import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))

from sql import generate_sql_query, run_query

query_text = "football"
sql = generate_sql_query(query_text)
print("Generated SQL response:")
print(sql)

import re
pattern = "<SQL>(.*?)</SQL>"
matches = re.findall(pattern, sql, re.DOTALL)
sql_command = matches[0].strip() if matches else ""
print(f"\nExtracted SQL command: {sql_command}")

if sql_command:
    res = run_query(sql_command)
    print(f"\nQuery results count: {len(res)}")
    print("\nQuery results (first 5):")
    print(res.head(5)[['title', 'price', 'product_link']])
