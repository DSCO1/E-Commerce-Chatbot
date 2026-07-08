import os
from groq import Groq

# Load environment
from dotenv import load_dotenv
load_dotenv('app/.env')

client = Groq(api_key=os.environ.get('GROQ_API_KEY'))
try:
    models = client.models.list()
    print("Active models on Groq:")
    for model in models.data:
        print(f"  - {model.id}")
except Exception as e:
    print(f"Error fetching models: {e}")
