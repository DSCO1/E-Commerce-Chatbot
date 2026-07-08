import os
import sys

# Ensure app path is in system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))

# Import the retry_on_rate_limit decorator
from sql import retry_on_rate_limit, FALLBACK_MODELS

# Set initial model environment variable
os.environ["GROQ_MODEL"] = FALLBACK_MODELS[0]

call_count = 0

@retry_on_rate_limit(max_retries=3, initial_delay=1)
def simulate_api_call():
    global call_count
    call_count += 1
    
    current_model = os.environ.get("GROQ_MODEL")
    print(f"  [API Call] Trying with model: {current_model}")
    
    if current_model == FALLBACK_MODELS[0]:
        # Simulate rate limit error on the first model
        print("  [API Call] Simulating 429 rate limit error!")
        raise Exception("429 Too Many Requests: Rate limit exceeded")
    
    print("  [API Call] Success!")
    return "API Success Result"

print("--- Testing Model Failover Mechanism ---")
print(f"Initial model set in env: {os.environ['GROQ_MODEL']}")

try:
    result = simulate_api_call()
    print(f"\nResult: {result}")
    print(f"Final model set in env: {os.environ['GROQ_MODEL']}")
    
    if os.environ["GROQ_MODEL"] == FALLBACK_MODELS[1] and result == "API Success Result":
         print("\n[PASS] Model failover test succeeded! Automatically switched to fallback model.")
    else:
         print("\n[FAIL] Model did not switch to correct fallback model.")
except Exception as e:
    print(f"\n[FAIL] Test raised exception: {e}")
