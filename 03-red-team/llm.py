import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url=os.environ['LLM_BASE_URL'],
    api_key=os.environ['LLM_API_KEY']
)

MODEL = os.environ['LLM_MODEL']

def chat(system, user, temperature=0.7):
    r = client.chat.completions.create(
        model=MODEL,
        temperature=temperature,
        max_tokens=400,
        messages=[
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user}
        ]
    )
    return r.choices[0].message.content
