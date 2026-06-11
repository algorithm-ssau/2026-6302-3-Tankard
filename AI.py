from groq import Groq
from typing import Any

API_KEY_PATH = "git_ignore/api_key.txt"
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

class AI:
    def __init__(self):
        self.client = Groq(api_key=self.load_api_key())

    @staticmethod
    def load_api_key() -> str:
        try:
            with open(API_KEY_PATH, "r", encoding="utf-8") as f:
                key = f.read().strip()
            if not key:
                raise ValueError("API-ключ не может быть пустым.")
            return key
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Файл с API-ключом не найден: {API_KEY_PATH}") from e


    def analyze_stats(self, stats: dict[str, Any]) -> str:
        top_by_type = stats.get("top_by_type", {})

        tanks_section = "Лучшие танки игрока по каждому классу (данные только для тех классов, что есть):\n"
        for type_name, tanks in top_by_type.items():
            if not tanks:
                continue
            tanks_section += f"\n[{type_name}]\n"
            for tank in tanks:
                tanks_section += (
                    f"- {tank.get('name', '?')}: WN8={tank.get('wn8', 0):.1f}, "
                    f"победы={tank.get('winrate', 0):.1f}%, боев={tank.get('battles', 0)}, "
                    f"откл. урона={tank.get('diff_damage', 0):.1f}, "
                    f"откл. фрагов={tank.get('diff_frags', 0):.2f}, "
                    f"откл. засвета={tank.get('diff_spotted', 0):.2f}, "
                    f"откл. винрейта={tank.get('diff_winrate', 0):.1f}%, "
                    f"откл. защиты={tank.get('diff_defence_points', 0):.2f}\n"
                )

        instruction = """
Ты — наставник в World of Tanks. Говори живым русским языком, на «ты», ёмко.
Обращайся как мужик к мужику иначе не поймут.

У тебя есть ТОЛЬКО эти данные. Не додумывай классы или танки, которых нет.

**Что означают diff_* (отклонение от среднего игрока на этом танке):**
- Отрицательные → хуже среднего. Положительные → лучше.
- Урон и фраги оба в минусе → танк используется неэффективно (ранняя смерть, плохие позиции).
- Засвет в минусе на ЛТ → плохо разведываешь.
- Защита в минусе на ТТ → плохо работаешь броней.
- Урон в минусе, фраги в плюсе → ты добиваешь чужое, а не наносишь первичный урон.
- Урон в плюсе, фраги в минусе → много стреляешь, но мало добиваешь.

**ЗАПРЕЩЕНО:**
- Называть числа (WN8, проценты, diff_*).
- Перечислять танки списком или пересказывать данные.
- Писать канцелярит («демонстрирует», «анализ показывает», «вышеизложенное»).
- Начинать с «твоя главная проблема» — сразу к делу.

**ТВОЙ ОТВЕТ — сплошной текст. Без заголовков.**
**Если данных мало или они противоречивы** — честно скажи: «Данных немного, но вот что вижу...» — и дай полезные рекомендации.
**Никогда не используй слово «отклонение»** — говори «выше/ниже среднего», «лучше/хуже типичного игрока».
**В конце дай рекомендацию какую ветку ему качать, к какому танку стремиться.
"""

        prompt = tanks_section + instruction
        return self.get_response(prompt)

    def get_response(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=MODEL,
                temperature=0.7,
                max_tokens=1024
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Ошибка при получении ответа от ИИ: {e}"


