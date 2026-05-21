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
        tanks_section = "Конкретная техника по классам:\n"

        for type_name in top_by_type.keys():
            tanks = top_by_type[type_name]
            if not tanks:
                continue
            
            tanks_section += f"\n--- {type_name} ---"

            for tank in tanks:
                tanks_section += (
                    f"  Тип: {tank.get('type', '?')}\n"
                    f"  Название: {tank.get('name', '?')}\n"
                    f"  WN8: {tank.get('wn8', 0):.2f}\n"
                    f"  Побед: {tank.get('wins', 0)}\n"
                    f"  Боёв: {tank.get('battles', 0)}\n"
                    f"  Ср. фраги: {tank.get('avg_frags', 0):.2f}\n"
                    f"  Ср. урон: {tank.get('avg_damage', 0):.2f}\n"
                    f"  Ср. засвет: {tank.get('avg_spotted', 0):.2f}\n"
                    f"  Ср. очки защиты: {tank.get('avg_defence_points', 0):.2f}\n"
                    f"  Винрейт: {tank.get('winrate', 0):.2f}%\n"
                    f"  Отклонение фрагов: {tank.get('diff_frags', 0):.3f}\n"
                    f"  Отклонение урона: {tank.get('diff_damage', 0):.2f}\n"
                    f"  Отклонение засвета: {tank.get('diff_spotted', 0):.3f}\n"
                    f"  Отклонение очков защиты: {tank.get('diff_defence_points', 0):.3f}\n"
                    f"  Отклонение винрейта: {tank.get('diff_winrate', 0):.2f}%\n\n"
                )

        # ----- 4. Инструкция -----
        instruction = """
Твоя задача — дать текстовый анализ статистики игрока в World of Tanks.

ЗАПРЕЩЕНО:
- Копировать в ответ цифры, таблицы или любые статистические выкладки из запроса.
- Повторять список танков или перечислять показатели.
- Выдавать структуру "общая статистика -> по классам -> по танкам -> выводы" с цифрами.

РАЗРЕШЕНО и НУЖНО:
- Только твои выводы, наблюдения и рекомендации на естественном русском языке.
- Упоминать конкретные танки и классы, но без дублирования их статистики (достаточно сказать "ИС-6" или "САУ").
- Обязательно ответить на вопросы:
  1. Какие классы у него получаются хорошо, какие — плохо? Почему?
  2. Есть ли расхождение между тем, на чём он часто играет, и тем, на чём показывает лучший WN8? Назови конкретные примеры танков.
  3. Какие главные ошибки в его игре видны по цифрам (например, низкий спот на лёгких танках, недостаточный урон на ТТ и т.д.)?
  4. Дай 3-5 конкретных советов по улучшению: какие танки стоит играть чаще/реже, на чём сменить тактику, какой класс развивать.

Формат ответа: сплошной текст, абзацы, без маркированных списков (если только они не для перечисления советов). Общий объём — не более 4-5 абзацев.
"""

        prompt = general_info + class_summary + tanks_section + instruction
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


