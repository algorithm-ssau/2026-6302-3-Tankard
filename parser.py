"""
Парсер статистики «Мир Танков» через tankist.net (без Lesta API key).

Единственная публичная точка входа для кода и CLI:

    from parser import parse_player_stats

    result = parse_player_stats("MyNickname")
    print(result.files.main)
    print(result.profile["wn8"])
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

__all__ = [
    "parse_player_stats",
    "ParsePlayerResult",
    "PlayerStatsFiles",
    "ParserError",
]

SOURCE_BASE_URL = "https://tankist.net"
DEFAULT_TIMEOUT = 20
DEFAULT_MIN_BATTLES = 20
DEFAULT_TOP_N = 20
DEFAULT_MAIN_OUTPUT = "player_stats.json"
DEFAULT_OUTPUT_DIR = "parsed_output"

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


class ParserError(RuntimeError):
    """Ошибка загрузки или разбора статистики игрока."""


@dataclass(frozen=True)
class PlayerStatsFiles:
    """Пути к JSON-файлам после сохранения (см. parse_player_stats)."""

    main: Path
    output_dir: Path
    raw_payload: Path
    profile_full: Path
    tanks_full: Path
    tank_stats_normalized: Path
    summaries: Path
    top_tanks: Path

    def as_dict(self) -> dict[str, str]:
        return {name: str(path) for name, path in self.__dict__.items()}


@dataclass
class ParsePlayerResult:
    """
    Результат parse_player_stats.

    Данные в памяти: main, raw_payload, profile, tanks_full, tanks, summaries, top_tanks.
    Файлы на диске (если save_to_disk=True): поле files.
    """

    nickname: str
    account_id: int | None
    min_battles: int

    main: dict[str, Any]
    raw_payload: dict[str, Any]
    profile: dict[str, Any]
    tanks_full: list[dict[str, Any]]
    tanks: list[dict[str, Any]]
    summaries: dict[str, Any]
    top_tanks: dict[str, Any]

    files: PlayerStatsFiles | None = None
    params: dict[str, Any] = field(default_factory=dict)

    @property
    def wn8(self) -> float | None:
        value = self.profile.get("wn8")
        return float(value) if value is not None else None


class _TankistStatsParser:
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
    def _build_top_lists(tanks: list[TankPerformance], min_battles: int, top_n: int) -> dict[str, Any]:
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

    def build_result(
        self,
        nickname: str,
        *,
        min_battles: int,
        top_n: int,
    ) -> ParsePlayerResult:
        payload = self.fetch_player_payload(nickname)
        tanks = self.build_tank_performance(payload)
        class_summary = self.build_class_summary(tanks, min_battles=min_battles)
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
                if battles
                else None,
                "avg_damage_per_battle": round(damage_dealt / battles, 2) if battles else None,
                "avg_frags_per_battle": self._safe_div(float(profile_stats.get("frags") or 0), battles),
                "avg_spots_per_battle": self._safe_div(float(profile_stats.get("spotted") or 0), battles),
                "avg_xp_per_battle": self._safe_div(float(profile_stats.get("xp") or 0), battles),
            },
        }

        per_type = self._weighted_group_summary(tanks, key_fn=lambda t: t.type, min_battles=min_battles)
        per_nation = self._weighted_group_summary(tanks, key_fn=lambda t: t.nation, min_battles=min_battles)
        per_tier = self._weighted_group_summary(tanks, key_fn=lambda t: t.tier, min_battles=min_battles)
        top_lists = self._build_top_lists(tanks, min_battles=min_battles, top_n=top_n)
        tanks_normalized = [asdict(item) for item in tanks]
        tanks_full = list(payload.get("tanks") or [])

        main = {
            "meta": {
                "source": "tankist.net (unofficial, no Lesta API key)",
                "source_endpoint": f"{SOURCE_BASE_URL}/api/stat/<nickname>",
                "game": "Мир Танков",
                "collected_at_utc": datetime.now(timezone.utc).isoformat(),
                "nickname": profile["nickname"],
                "account_id": profile["account_id"],
            },
            "profile": profile,
            "class_summary": [asdict(item) for item in class_summary],
            "tank_stats": tanks_normalized,
            "group_summaries": {
                "by_type": per_type,
                "by_nation": per_nation,
                "by_tier": per_tier,
            },
            "top_tanks": top_lists,
            "insights": {
                "best_vehicle_class": best_class,
                "min_battles_for_class_summary": min_battles,
            },
        }

        summaries = {
            "by_type": per_type,
            "by_nation": per_nation,
            "by_tier": per_tier,
            "class_summary": [asdict(item) for item in class_summary],
        }

        return ParsePlayerResult(
            nickname=str(profile["nickname"]),
            account_id=profile.get("account_id"),
            min_battles=min_battles,
            main=main,
            raw_payload=payload,
            profile=profile,
            tanks_full=tanks_full,
            tanks=tanks_normalized,
            summaries=summaries,
            top_tanks=top_lists,
            params={"top_n": top_n, "timeout": self.timeout},
        )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def _save_result_files(
    result: ParsePlayerResult,
    *,
    output: Path,
    out_dir: Path,
) -> PlayerStatsFiles:
    _write_json(output, {**MAIN_FILE_DESCRIPTION, **result.main})

    extra: dict[str, dict[str, Any]] = {
        "raw_payload.json": {**RAW_PAYLOAD_DESCRIPTION, "data": result.raw_payload},
        "profile_full.json": {**PROFILE_DESCRIPTION, "data": result.profile},
        "tanks_full.json": {**TANKS_FULL_DESCRIPTION, "data": result.tanks_full},
        "tank_stats_normalized.json": {**TANKS_NORMALIZED_DESCRIPTION, "data": result.tanks},
        "summaries.json": {**SUMMARIES_DESCRIPTION, "data": result.summaries},
        "top_tanks.json": {**TOP_TANKS_DESCRIPTION, "data": result.top_tanks},
    }

    paths: dict[str, Path] = {}
    for filename, payload in extra.items():
        path = out_dir / filename
        _write_json(path, payload)
        paths[filename] = path.resolve()

    return PlayerStatsFiles(
        main=output.resolve(),
        output_dir=out_dir.resolve(),
        raw_payload=paths["raw_payload.json"],
        profile_full=paths["profile_full.json"],
        tanks_full=paths["tanks_full.json"],
        tank_stats_normalized=paths["tank_stats_normalized.json"],
        summaries=paths["summaries.json"],
        top_tanks=paths["top_tanks.json"],
    )


def parse_player_stats(
    nickname: str,
    *,
    output: str | Path = DEFAULT_MAIN_OUTPUT,
    out_dir: str | Path = DEFAULT_OUTPUT_DIR,
    min_battles: int = DEFAULT_MIN_BATTLES,
    top_n: int = DEFAULT_TOP_N,
    timeout: int = DEFAULT_TIMEOUT,
    save_to_disk: bool = True,
    verbose: bool = False,
) -> ParsePlayerResult:
    """
    Загрузить статистику игрока, нормализовать и (по умолчанию) сохранить все JSON.

    Args:
        nickname: Ник в «Мире Танков» (минимум 3 символа).
        output: Путь к главному файлу player_stats.json.
        out_dir: Папка для остальных JSON (raw_payload, profile, tanks, summaries, top_tanks).
        min_battles: Минимум боёв на танке для агрегатов и топов.
        top_n: Сколько танков в каждом топе.
        timeout: Таймаут HTTP-запроса к tankist.net, секунды.
        save_to_disk: False — только данные в памяти, без записи файлов.
        verbose: True — вывести пути к сохранённым файлам в stdout.

    Returns:
        ParsePlayerResult с полями main, profile, tanks, summaries, top_tanks и paths в files.

    Raises:
        ParserError: неверный ник, игрок не найден или ошибка источника.
    """
    if nickname.strip() == "PLAYER_NICK":
        raise ParserError("Укажи реальный nickname игрока, а не PLAYER_NICK")

    result = _TankistStatsParser(timeout=timeout).build_result(
        nickname,
        min_battles=min_battles,
        top_n=top_n,
    )

    if not save_to_disk:
        return result

    files = _save_result_files(result, output=Path(output), out_dir=Path(out_dir))
    result.files = files

    if verbose:
        print(f"Готово: {files.main}")
        print(f"Дополнительно: {files.output_dir}")

    return result


def _build_cli() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(
        description="Парсер статистики Мир Танков (обёртка над parse_player_stats)",
    )
    cli.add_argument("--nickname", required=True, help="Ник игрока")
    cli.add_argument("--output", default=DEFAULT_MAIN_OUTPUT, help="Путь к player_stats.json")
    cli.add_argument("--out-dir", default=DEFAULT_OUTPUT_DIR, help="Папка для дополнительных JSON")
    cli.add_argument(
        "--min-battles",
        type=int,
        default=DEFAULT_MIN_BATTLES,
        help="Мин. боёв на танке для агрегатов и топов",
    )
    cli.add_argument("--top-n", type=int, default=DEFAULT_TOP_N, help="Размер каждого топа танков")
    return cli


def main() -> None:
    args = _build_cli().parse_args()
    parse_player_stats(
        args.nickname,
        output=args.output,
        out_dir=args.out_dir,
        min_battles=args.min_battles,
        top_n=args.top_n,
        verbose=True,
    )


if __name__ == "__main__":
    main()
