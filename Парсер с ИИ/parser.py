from __future__ import annotations

import argparse
import json
import requests
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ----------------------------------------------------------------------
# Константы
SOURCE_BASE_URL = "https://tankist.net"
DEFAULT_TIMEOUT = 20

# ----------------------------------------------------------------------
# Описания схем (для JSON-файлов)
MAIN_FILE_DESCRIPTION = {
    "_description": "Главный файл с нормализованной статистикой игрока, агрегатами и топами.",
    "_schema": {
        "meta": "Источник, время выгрузки, ник, account_id.",
        "profile": "Профиль игрока: сырые поля + вычисленные метрики.",
        "class_summary": "Агрегация по классам техники (с учетом min_battles).",
        "tank_stats": "Нормализованная статистика по каждому танку.",
        "group_summaries": "Агрегаты по типам, нациям и уровням.",
        "top_tanks": "Топы техники по разным метрикам.",
        "insights": "Базовые выводы и параметры расчета.",
    },
}

RAW_PAYLOAD_DESCRIPTION = {
    "_description": "Полный сырой ответ endpoint без изменений.",
    "_schema": {
        "success": "Статус ответа источника.",
        "nickname": "Ник игрока.",
        "account_id": "ID аккаунта.",
        "global_rating": "Личный рейтинг.",
        "wn8": "Итоговый WN8 игрока.",
        "stats": "Общая статистика игрока (как отдает источник).",
        "tanks": "Список танков с метриками и метаданными.",
    },
}

PROFILE_DESCRIPTION = {
    "_description": "Профиль игрока и вычисленные производные метрики.",
    "_schema": {
        "stats_raw": "Сырые поля общей статистики игрока от источника.",
        "calculated": "Вычисленные метрики (winrate, avg по бою и т.д.).",
    },
}

TANKS_FULL_DESCRIPTION = {
    "_description": "Сырые танковые записи от источника (полный набор полей).",
    "_schema": {
        "tank_id": "ID танка.",
        "tank": "Справочная информация по танку (тип, нация, уровень, имя и др.).",
        "battles/wins/winrate": "Показатели боев и побед.",
        "damage/frags/spotted/defence_points": "Средние показатели за бой.",
        "wn8": "WN8 по танку.",
        "diff": "Разница относительно ожидаемых значений (если есть).",
    },
}

TANKS_NORMALIZED_DESCRIPTION = {
    "_description": "Нормализованный список танков в стабильной структуре.",
    "_schema": {
        "tank_id/name/short_name": "Идентификация танка.",
        "type/nation/tier": "Класс, нация и уровень танка.",
        "battles/wins/losses/win_rate": "Результативность на танке.",
        "avg_damage/avg_frags/avg_spotted/avg_defence_points": "Средние метрики.",
        "wn8": "WN8 по танку.",
    },
}

SUMMARIES_DESCRIPTION = {
    "_description": "Сводные агрегаты по группам техники.",
    "_schema": {
        "class_summary": "Агрегация по основным классам техники.",
        "by_type": "Агрегация по типу техники (ключ key = type).",
        "by_nation": "Агрегация по нации (ключ key = nation).",
        "by_tier": "Агрегация по уровню (ключ key = tier).",
        "fields": "battles, win_rate, avg_damage, avg_frags, avg_spotted, avg_defence_points, avg_wn8.",
    },
}

TOP_TANKS_DESCRIPTION = {
    "_description": "Топы танков по разным метрикам с единым фильтром min_battles.",
    "_schema": {
        "criteria": "Параметры отбора (min_battles, top_n).",
        "by_wn8": "Лучшие по WN8.",
        "by_win_rate": "Лучшие по проценту побед.",
        "by_avg_damage": "Лучшие по среднему урону.",
        "by_avg_frags": "Лучшие по средним фрагам.",
        "by_battles": "Самые наигранные танки.",
    },
}

# ----------------------------------------------------------------------
# Dataclasses
@dataclass
class TankPerformance:
    tank_id: int
    name: str
    short_name: str
    type: str
    nation: str
    tier: int
    battles: int
    wins: int
    losses: int
    win_rate: float
    avg_damage: float
    avg_frags: float
    avg_spotted: float
    avg_defence_points: float
    wn8: float

@dataclass
class ClassSummary:
    vehicle_type: str
    battles: int
    win_rate: float
    avg_damage: float
    avg_frags: float
    avg_spotted: float
    avg_defence_points: float
    avg_wn8: float

# ----------------------------------------------------------------------
# Парсер
class ParserError(RuntimeError):
    pass

class TankistStatsParser:
    def __init__(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        self.timeout = timeout

    def fetch_player_payload(self, nickname: str) -> dict[str, Any]:
        if not nickname or len(nickname.strip()) < 3:
            raise ParserError("Ник должен содержать минимум 3 символа.")
        url = f"{SOURCE_BASE_URL}/api/stat/{requests.utils.quote(nickname.strip())}"
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        if not payload.get("success"):
            raise ParserError(payload.get("message") or "Не удалось получить статистику игрока.")
        return payload

    def build_tank_performance(self, payload: dict[str, Any]) -> list[TankPerformance]:
        tanks: list[TankPerformance] = []
        for item in payload.get("tanks", []):
            tank_meta = item.get("tank") or {}
            battles = int(item.get("battles") or 0)
            if battles <= 0:
                continue
            wins = int(item.get("wins") or 0)
            losses = max(0, battles - wins)
            tanks.append(
                TankPerformance(
                    tank_id=int(item.get("tank_id") or 0),
                    name=str(tank_meta.get("name") or ""),
                    short_name=str(tank_meta.get("short_name") or tank_meta.get("name") or ""),
                    type=str(tank_meta.get("type") or "unknown"),
                    nation=str(tank_meta.get("nation") or "unknown"),
                    tier=int(tank_meta.get("tier") or 0),
                    battles=battles,
                    wins=wins,
                    losses=losses,
                    win_rate=round(float(item.get("winrate") or 0), 2),
                    avg_damage=round(float(item.get("damage") or 0), 2),
                    avg_frags=round(float(item.get("frags") or 0), 3),
                    avg_spotted=round(float(item.get("spotted") or 0), 3),
                    avg_defence_points=round(float(item.get("defence_points") or 0), 3),
                    wn8=round(float(item.get("wn8") or 0), 2),
                )
            )
        return sorted(tanks, key=lambda x: x.battles, reverse=True)

    def build_class_summary(self, tanks: list[TankPerformance], min_battles: int) -> list[ClassSummary]:
        grouped: dict[str, dict[str, float]] = defaultdict(
            lambda: {
                "battles": 0,
                "wins": 0,
                "total_damage": 0,
                "total_frags": 0,
                "total_spotted": 0,
                "total_defence": 0,
                "total_wn8_weighted": 0,
            }
        )
        for tank in tanks:
            if tank.battles < min_battles:
                continue
            g = grouped[tank.type]
            g["battles"] += tank.battles
            g["wins"] += tank.wins
            g["total_damage"] += tank.avg_damage * tank.battles
            g["total_frags"] += tank.avg_frags * tank.battles
            g["total_spotted"] += tank.avg_spotted * tank.battles
            g["total_defence"] += tank.avg_defence_points * tank.battles
            g["total_wn8_weighted"] += tank.wn8 * tank.battles

        result: list[ClassSummary] = []
        for vehicle_type, stat in grouped.items():
            battles = int(stat["battles"])
            if battles <= 0:
                continue
            result.append(
                ClassSummary(
                    vehicle_type=vehicle_type,
                    battles=battles,
                    win_rate=round(stat["wins"] * 100 / battles, 2),
                    avg_damage=round(stat["total_damage"] / battles, 2),
                    avg_frags=round(stat["total_frags"] / battles, 3),
                    avg_spotted=round(stat["total_spotted"] / battles, 3),
                    avg_defence_points=round(stat["total_defence"] / battles, 3),
                    avg_wn8=round(stat["total_wn8_weighted"] / battles, 2),
                )
            )
        return sorted(result, key=lambda x: (x.avg_wn8, x.win_rate, x.battles), reverse=True)

    @staticmethod
    def _weighted_group_summary(
        tanks: list[TankPerformance], key_fn: Any, min_battles: int
    ) -> list[dict[str, Any]]:
        grouped: dict[str, dict[str, float]] = defaultdict(
            lambda: {
                "battles": 0,
                "wins": 0,
                "total_damage": 0,
                "total_frags": 0,
                "total_spotted": 0,
                "total_defence": 0,
                "total_wn8_weighted": 0,
                "tank_count": 0,
            }
        )
        for tank in tanks:
            if tank.battles < min_battles:
                continue
            group_key = str(key_fn(tank))
            g = grouped[group_key]
            g["battles"] += tank.battles
            g["wins"] += tank.wins
            g["total_damage"] += tank.avg_damage * tank.battles
            g["total_frags"] += tank.avg_frags * tank.battles
            g["total_spotted"] += tank.avg_spotted * tank.battles
            g["total_defence"] += tank.avg_defence_points * tank.battles
            g["total_wn8_weighted"] += tank.wn8 * tank.battles
            g["tank_count"] += 1

        rows: list[dict[str, Any]] = []
        for key, stat in grouped.items():
            battles = int(stat["battles"])
            if battles <= 0:
                continue
            rows.append(
                {
                    "key": key,
                    "tank_count": int(stat["tank_count"]),
                    "battles": battles,
                    "win_rate": round(stat["wins"] * 100 / battles, 2),
                    "avg_damage": round(stat["total_damage"] / battles, 2),
                    "avg_frags": round(stat["total_frags"] / battles, 3),
                    "avg_spotted": round(stat["total_spotted"] / battles, 3),
                    "avg_defence_points": round(stat["total_defence"] / battles, 3),
                    "avg_wn8": round(stat["total_wn8_weighted"] / battles, 2),
                }
            )
        return sorted(rows, key=lambda x: (x["avg_wn8"], x["win_rate"], x["battles"]), reverse=True)

    @staticmethod
    def _build_top_lists(tanks: list[TankPerformance], min_battles: int, top_n: int = 20) -> dict[str, Any]:
        qualified = [t for t in tanks if t.battles >= min_battles]
        as_rows = [asdict(t) for t in qualified]
        return {
            "criteria": {"min_battles": min_battles, "top_n": top_n},
            "by_wn8": sorted(as_rows, key=lambda x: x["wn8"], reverse=True)[:top_n],
            "by_win_rate": sorted(as_rows, key=lambda x: x["win_rate"], reverse=True)[:top_n],
            "by_avg_damage": sorted(as_rows, key=lambda x: x["avg_damage"], reverse=True)[:top_n],
            "by_avg_frags": sorted(as_rows, key=lambda x: x["avg_frags"], reverse=True)[:top_n],
            "by_battles": sorted(as_rows, key=lambda x: x["battles"], reverse=True)[:top_n],
        }

    @staticmethod
    def _safe_div(num: float, den: float) -> float | None:
        if not den:
            return None
        return round(num / den, 4)

    def collect_player_stats(self, nickname: str, min_battles_for_class_summary: int) -> dict[str, Any]:
        payload = self.fetch_player_payload(nickname)
        tanks = self.build_tank_performance(payload)
        class_summary = self.build_class_summary(tanks, min_battles=min_battles_for_class_summary)
        best_class = class_summary[0].vehicle_type if class_summary else None

        profile_stats = payload.get("stats") or {}
        battles = float(profile_stats.get("battles") or 0)
        wins = float(profile_stats.get("wins") or 0)
        losses = float(profile_stats.get("losses") or 0)
        draws = float(profile_stats.get("draws") or 0)
        damage_dealt = float(profile_stats.get("damage_dealt") or 0)

        profile = {
            "nickname": payload.get("nickname") or nickname,
            "account_id": payload.get("account_id"),
            "global_rating": payload.get("global_rating"),
            "wn8": payload.get("wn8"),
            "created_at": payload.get("created_at"),
            "updated_at": payload.get("updated_at"),
            "last_battle_time": payload.get("last_battle_time"),
            "stats_raw": profile_stats,
            "calculated": {
                "battles": int(battles),
                "wins": int(wins),
                "losses": int(losses),
                "draws": int(draws),
                "win_rate_percent": round((wins / battles) * 100, 2) if battles else None,
                "survival_rate_percent": round(float(profile_stats.get("survived_battles") or 0) * 100 / battles, 2)
                if battles else None,
                "avg_damage_per_battle": round(damage_dealt / battles, 2) if battles else None,
                "avg_frags_per_battle": self._safe_div(float(profile_stats.get("frags") or 0), battles),
                "avg_spots_per_battle": self._safe_div(float(profile_stats.get("spotted") or 0), battles),
                "avg_xp_per_battle": self._safe_div(float(profile_stats.get("xp") or 0), battles),
            },
        }

        per_type = self._weighted_group_summary(tanks, key_fn=lambda t: t.type, min_battles=min_battles_for_class_summary)
        per_nation = self._weighted_group_summary(tanks, key_fn=lambda t: t.nation, min_battles=min_battles_for_class_summary)
        per_tier = self._weighted_group_summary(tanks, key_fn=lambda t: t.tier, min_battles=min_battles_for_class_summary)
        top_lists = self._build_top_lists(tanks, min_battles=min_battles_for_class_summary)

        main_player_json = {
            "meta": {
                "source": "tankist.net (unofficial, no Lesta API key)",
                "source_endpoint": f"{SOURCE_BASE_URL}/api/stat/<nickname>",
                "game": "Мир Танков",
                "collected_at_utc": datetime.now(timezone.utc).isoformat(),
                "nickname": payload.get("nickname") or nickname,
                "account_id": payload.get("account_id"),
            },
            "profile": profile,
            "class_summary": [asdict(item) for item in class_summary],
            "tank_stats": [asdict(item) for item in tanks],
            "group_summaries": {
                "by_type": per_type,
                "by_nation": per_nation,
                "by_tier": per_tier,
            },
            "top_tanks": top_lists,
            "insights": {
                "best_vehicle_class": best_class,
                "min_battles_for_class_summary": min_battles_for_class_summary,
            },
        }

        return {
            "player_stats": main_player_json,
            "raw_payload": payload,
            "profile_full": profile,
            "tanks_full": payload.get("tanks", []),
            "tank_stats_normalized": [asdict(item) for item in tanks],
            "summaries": {
                "by_type": per_type,
                "by_nation": per_nation,
                "by_tier": per_tier,
                "class_summary": [asdict(item) for item in class_summary],
            },
            "top_tanks": top_lists,
        }

# ----------------------------------------------------------------------
# AI-агент на основе Ollamacurl http://localhost:11434/api/tags
class OllamaAnalyzer:
    def __init__(self, model: str = "llama3.2:1b", url: str = "http://localhost:11434/api/generate"):
        self.model = model
        self.url = url

    def _build_prompt(self, stats: dict[str, Any]) -> str:
        p = stats["profile"]
        cs = stats.get("class_summary", [])
        top = stats.get("top_tanks", {})
        by_wn8 = top.get("by_wn8", [])
        by_battles = top.get("by_battles", [])
        nickname = p.get("nickname", "Игрок")

        # Хороший промпт — задаёт роль, формат и контекст
        prompt = f"""Ты — опытный аналитик и тренер по игре World of Tanks. 
Твоя задача — проанализировать статистику игрока и дать конкретные, практические советы для улучшения его игры.

Вот статистика игрока {nickname}:

Общие показатели:
- WN8 (рейтинг мастерства): {p['wn8']}
- Процент побед: {p['calculated']['win_rate_percent']}%
- Выживаемость: {p['calculated']['survival_rate_percent']}%
- Средний урон за бой: {p['calculated']['avg_damage_per_battle']}
- Средние фраги (уничтожения) за бой: {p['calculated']['avg_frags_per_battle']}
- Средние засветы за бой: {p['calculated']['avg_spots_per_battle']}

Классы техники (от лучшего к худшему по WN8):
"""
        for cls in cs:
            prompt += f"- {cls['vehicle_type']}: WN8={cls['avg_wn8']}, винрейт={cls['win_rate']}%, сыграно боев={cls['battles']}\n"

        prompt += "\nТоп-5 танков по WN8:\n"
        for t in by_wn8[:5]:
            prompt += f"- {t['short_name']} ({t['type']}, {t['nation']}, уровень {t['tier']}): WN8={t['wn8']}, винрейт={t['win_rate']}%, боев={t['battles']}\n"

        prompt += "\nСамые наигранные танки (по количеству боев):\n"
        for t in by_battles[:5]:
            prompt += f"- {t['short_name']}: {t['battles']} боев, WN8={t['wn8']}, винрейт={t['win_rate']}%\n"

        prompt += """
Проанализируй эти данные и дай ответ в следующем формате:

1. Ключевые выводы (2-3 предложения, в чём основные проблемы и сильные стороны).
2. Конкретные рекомендации (3-5 пунктов) — что игроку нужно делать, чтобы улучшить свою статистику. Советы должны быть практичными: например, на каких танках больше играть, какой стиль боя изменить, над какими метриками работать.

Ответ напиши на русском языке, дружелюбно и по делу.
"""
        return prompt

    def analyze(self, stats: dict[str, Any]) -> str:
        prompt = self._build_prompt(stats)
        try:
            response = requests.post(
                self.url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7}
                },
                timeout=120
            )
            response.raise_for_status()
            return response.json()["response"]
        except requests.exceptions.ConnectionError:
            return "❌ Не удалось подключиться к Ollama. Убедитесь, что Ollama запущен (команда 'ollama serve') и модель скачана ('ollama pull " + self.model + "')."
        except Exception as e:
            return f"❌ Ошибка при обращении к Ollama: {e}"

# ----------------------------------------------------------------------
# Командная строка и main
def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Парсер статистики World of Tanks + AI-агент (Ollama)")
    parser.add_argument("--nickname", required=True, help="Ник игрока")
    parser.add_argument("--output", default="player_stats.json", help="Путь к главному JSON")
    parser.add_argument("--out-dir", default="parsed_output", help="Папка для дополнительных JSON")
    parser.add_argument("--min-battles", type=int, default=20, help="Минимум боев на танке для учёта в агрегатах")
    parser.add_argument("--analyze", action="store_true", help="Запустить AI-агента (требуется Ollama)")
    return parser

def main() -> None:
    args = build_cli().parse_args()
    if args.nickname == "PLAYER_NICK":
        raise SystemExit("Укажите реальный ник игрока, например: --nickname eremea")

    # Парсинг
    parser = TankistStatsParser()
    parsed = parser.collect_player_stats(
        nickname=args.nickname,
        min_battles_for_class_summary=args.min_battles,
    )

    # Создание папок
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_dir = Path(args.out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Сохранение основного JSON
    main_payload = {**MAIN_FILE_DESCRIPTION, **parsed["player_stats"]}
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(main_payload, f, ensure_ascii=False, indent=2)

    # Сохранение дополнительных JSON
    extra_files = {
        "raw_payload.json": {**RAW_PAYLOAD_DESCRIPTION, "data": parsed["raw_payload"]},
        "profile_full.json": {**PROFILE_DESCRIPTION, "data": parsed["profile_full"]},
        "tanks_full.json": {**TANKS_FULL_DESCRIPTION, "data": parsed["tanks_full"]},
        "tank_stats_normalized.json": {**TANKS_NORMALIZED_DESCRIPTION, "data": parsed["tank_stats_normalized"]},
        "summaries.json": {**SUMMARIES_DESCRIPTION, "data": parsed["summaries"]},
        "top_tanks.json": {**TOP_TANKS_DESCRIPTION, "data": parsed["top_tanks"]},
    }
    for filename, data in extra_files.items():
        with (output_dir / filename).open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Готово: основной файл -> {output_path}")
    print(f"📁 Дополнительные JSON -> {output_dir}")

    # AI-анализ, если запрошен
    if args.analyze:
        print("\n🤖 Запуск AI-агента (локальная модель Ollama)...")
        analyzer = OllamaAnalyzer(model="lakomoor/vikhr-llama-3.2-1b-instruct:q4_0")
        advice = analyzer.analyze(parsed["player_stats"])
        print("\n" + "="*60)
        print("📊 AI-АНАЛИЗ СТАТИСТИКИ")
        print("="*60)
        print(advice)
        print("="*60)

        # Сохраняем анализ в файл
        analysis_path = output_dir / "ai_analysis.txt"
        with analysis_path.open("w", encoding="utf-8") as f:
            f.write(advice)
        print(f"💾 Анализ сохранён в {analysis_path}")

if __name__ == "__main__":
    main()
