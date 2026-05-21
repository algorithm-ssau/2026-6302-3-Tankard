from groq import Groq
from typing import Any

def build_prompt(data: dict[str, Any]) -> str:
    pass

def ask_ai(prompt: str) -> str:

    api_key = ""
    with open(r'git_ignore/api_key.txt', 'r', encoding='utf-8') as file:
        api_key = file.read()

    client = Groq(api_key)

    response = client.chat.completions.create(
        messages    = [{"role": "user", "content": "{prompt}"}],
        model       = "meta-llama/llama-4-scout-17b-16e-instruct",
        temperature = 0.7,
        max_tokens  = 1024)
    
    return response.choices[0].message.content
