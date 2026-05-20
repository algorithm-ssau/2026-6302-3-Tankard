import openai
from openai import OpenAI

# Твой API-ключ (замени на настоящий, если этот пример не работает)
API_KEY = "sk-uvwx1234uvwx1234uvwx1234uvwx1234uvwx1234"


def ask_ai(prompt: str) -> str:
    """
    Отправляет текстовый промпт в GPT-3.5-turbo, возвращает ответ.
    """
    client = OpenAI(api_key=API_KEY)

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Ошибка: {e}"


# Пример использования
if __name__ == "__main__":
    user_input = input("Введите ваш промпт: ")
    answer = ask_ai(user_input)
    print("\nОтвет ИИ:\n", answer)