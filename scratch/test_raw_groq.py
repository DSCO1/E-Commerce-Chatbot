import os
import sys
sys.path.append('app')

from dotenv import load_dotenv
load_dotenv('app/.env')

from groq import Groq
client = Groq()

# Read sql_prompt from app/sql.py
with open('app/sql.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract sql_prompt content
start_marker = 'sql_prompt = """'
end_marker = '"""'
start_idx = content.find(start_marker) + len(start_marker)
end_idx = content.find(end_marker, start_idx)
sql_prompt = content[start_idx:end_idx]

def get_raw_response(question):
    chat = client.chat.completions.create(
        model=os.environ['GROQ_MODEL'],
        messages=[
            {"role": "system", "content": sql_prompt},
            {"role": "user", "content": question}
        ],
        temperature=0.0
    )
    return chat.choices[0].message.content

print("Raw response for 'fans':")
print(get_raw_response("fans"))
print("\nRaw response for 'laptops':")
print(get_raw_response("laptops"))
