# ai_agent.py
import requests
from typing import Dict, Any

class AIStatsAnalyzer:
    def __init__(self, model_name: str = "qwen2.5:7b-instruct", ollama_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.ollama_url = ollama_url
        self._check_ollama()
    
    def _check_ollama(self):
        """Проверяет, что Ollama сервер запущен и модель доступна"""
        try:
            resp = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            resp.raise_for_status()
            models = resp.json().get("models", [])
            model_names = [m["name"] for m in models]
            
            found = any(self.model_name in name for name in model_names)
            if not found:
                print(f"⚠️ Модель {self.model_name} не найдена. Доступные: {model_names}")
        except Exception as e:
            raise Exception(f"Ollama не отвечает. Запусти 'ollama serve' в терминале. Ошибка: {e}")
    
    def _prepare_prompt(self, stats: Dict[str, Any]) -> str:
        profile = stats.get("profile", {})
        meta = stats.get("meta", {})
        calculated = profile.get("calculated", {})
        class_summary = stats.get("class_summary", [])
        top_tanks = stats.get("top_tanks", {})
        
        # Топ-3 танка
        top_wn8 = top_tanks.get("by_wn8", [])[:3]
        top_tanks_text = ""
        for t in top_wn8:
            top_tanks_text += f"- {t.get('name')}: WN8={t.get('wn8'):.0f}, винрейт={t.get('win_rate')}%, боев={t.get('battles')}\n"
        
        # Классы простыми словами
        class_text = ""
        type_names = {
            "heavyTank": "Тяжёлые", "mediumTank": "Средние", 
            "lightTank": "Лёгкие", "AT-SPG": "ПТ-САУ", "SPG": "Артиллерия"
        }
        for c in class_summary[:4]:
            name = type_names.get(c.get('vehicle_type'), c.get('vehicle_type'))
            class_text += f"- {name}: WN8={c.get('avg_wn8', 0):.0f}, винрейт={c.get('win_rate', 0)}%\n"
        
        prompt = f"""ТЫ ОБЯЗАН ОТВЕЧАТЬ ТОЛЬКО НА РУССКОМ ЯЗЫКЕ.
    Статистика игрока World of Tanks:
    - WN8: {profile.get('wn8')}
    - Винрейт: {calculated.get('win_rate_percent', 0)}%
    - Боев: {calculated.get('battles', 0):,}

    Классы:
    {class_text}

    Лучшие танки:
    {top_tanks_text}

    Напиши короткий анализ (4-6 предложений): Какой у игрока уровень? Что у него получается лучше всего? Что у него хуже всего? Один конкретный совет."""
        
        return prompt
    
    def analyze(self, stats: Dict[str, Any]) -> str:
        """Отправляет статистику в Ollama и возвращает анализ"""
        if not stats:
            return "❌ Нет данных для анализа. Сначала загрузи статистику игрока."
        
        prompt = self._prepare_prompt(stats)
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "max_tokens": 400,
                        "top_p": 0.9,
                        "repeat_penalty": 1.1
                    }
                },
                timeout=300
            )
            response.raise_for_status()
            result = response.json()
            raw_response = result.get("response", "Не удалось получить ответ от модели")
            
            # Небольшая пост-очистка (минимальная)
            lines = raw_response.split('\n')
            cleaned = []
            seen_empty = False
            for line in lines:
                if line.strip() == "":
                    if not seen_empty:
                        cleaned.append(line)
                        seen_empty = True
                else:
                    cleaned.append(line)
                    seen_empty = False
            
            return '\n'.join(cleaned)
            
        except requests.exceptions.Timeout:
            return "⏰ Анализ занимает слишком много времени. Попробуй ещё раз."
        except requests.exceptions.ConnectionError:
            return "🔌 Не могу подключиться к Ollama. Запусти 'ollama serve' в терминале"
        except Exception as e:
            return f"❌ Ошибка при анализе: {str(e)}"