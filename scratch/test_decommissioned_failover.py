import os
import sys

# Ensure app path is in system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))

from sql import generate_sql_query, FALLBACK_MODELS

# Explicitly set to a decommissioned/deprecated model to simulate the exact failure
os.environ["GROQ_MODEL"] = "gemma2-9b-it"

print("--- Testing Live Decommissioned Model Failover ---")
print(f"Starting model set to: {os.environ['GROQ_MODEL']}")

try:
    # Run completion. This will throw the 400 decommissioned exception on the initial call, 
    # which should be intercepted and switched to a supported model.
    res = generate_sql_query("watches")
    print(f"\nResponse received successfully!")
    print(f"Ending model set to: {os.environ['GROQ_MODEL']}")
    
    if os.environ["GROQ_MODEL"] in FALLBACK_MODELS and "SELECT" in res:
        print("\n[PASS] Automatic decommissioned model failover was successful!")
    else:
        print("\n[FAIL] Model did not switch to correct fallback.")
except Exception as e:
    print(f"\n[FAIL] Test failed with exception: {e}")
