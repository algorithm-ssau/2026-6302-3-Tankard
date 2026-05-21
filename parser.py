from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

import requests

SOURCE_BASE_URL = "https://tankist.net"
DEFAULT_TIMEOUT = 20

TYPES = {"SPG":"САУ", "lightTank":"Легкий Танк", "mediumTank":"Средний Танк", "AT-SPG":"ПТ-САУ", "heavyTank":"Тяжелый Танк"}
NATIONS = {"ussr":"СССР", "france":"Франция", "germany":"Германия", "usa":"США", "sweden":"Швеция", "italy":"Италия",
           "uk":"Великобритания", "czech":"Чехословакия", "china":"Китай", "japan":"Япония", "poland":"Польша", "poland":"Польша"}

class ParserError(RuntimeError): pass

@dataclass
class TankPerformance:
    tank_id: int
    tier: int
    type: str
    nation: str
    name: str
    order: int

    wn8: float
    wins: int
    battles: int
    avg_frags: float
    avg_damage: float
    avg_spotted: float
    avg_defence_points: float
    winrate: float
    
    diff_frags: float | None = None
    diff_damage: float | None = None
    diff_spotted: float | None = None
    diff_defence_points: float | None = None
    diff_winrate: float | None = None
    

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


    def profile_meta(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "source": "tankist.net",
            "source_endpoint": f"{SOURCE_BASE_URL}/api/stat/<nickname>",
            "game": "Мир Танков",
            "collected_at_utc": datetime.now(timezone.utc).isoformat(),
            "nickname": payload.get("nickname"),
            "account_id": payload.get("account_id"),
            "global_rating": payload.get("global_rating"),
            "created_at": payload.get("created_at"),
            "updated_at": payload.get("updated_at"),
            "last_battle_time": payload.get("last_battle_time")
        }
    
    def profile_stat(self, payload: dict[str, Any]) -> dict[str, Any]:
        stats = payload.get("stats", {})
        battles = stats.get("battles")
        survived = stats.get("survived_battles")
        return {
            "battles": battles,
            "wins": stats.get("wins"),
            "losses": stats.get("losses"),
            "draws": stats.get("draws"),
            "winrate": stats.get("winrate"),
            "damage_dealt": stats.get("damage_dealt"),
            "damage_received": stats.get("damage_received"),
            "avg_damage": stats.get("avg_damage"),
            "avg_damage_blocked": stats.get("avg_damage_blocked"),
            "avg_damage_assisted": stats.get("avg_damage_assisted"),
            "avg_damage_assisted_track": stats.get("avg_damage_assisted_track"),
            "avg_damage_assisted_radio": stats.get("avg_damage_assisted_radio"),
            "frags": stats.get("frags"),
            "avg_frags": stats.get("avg_frags"),
            "xp": stats.get("xp"),
            "battle_avg_xp": stats.get("battle_avg_xp"),
            "max_xp": stats.get("max_xp"),
            "max_xp_tank_id": stats.get("max_xp_tank_id"),
            "max_damage": stats.get("max_damage"),
            "max_damage_tank_id": stats.get("max_damage_tank_id"),
            "max_frags": stats.get("max_frags"),
            "max_frags_tank_id": stats.get("max_frags_tank_id"),
            "survived_battles": stats.get("survived_battles"),
            "survival_rate": round((survived / battles) * 100, 2) if battles else 0,
            "hits": stats.get("hits"),
            "shots": stats.get("shots"),
            "hits_percents": stats.get("hits_percents"),
            "piercings": stats.get("piercings"),
            "piercings_received": stats.get("piercings_received"),
            "direct_hits_received": stats.get("direct_hits_received"),
            "no_damage_direct_hits_received": stats.get("no_damage_direct_hits_received"),
            "explosion_hits": stats.get("explosion_hits"),
            "explosion_hits_received": stats.get("explosion_hits_received"),
            "capture_points": stats.get("capture_points"),
            "dropped_capture_points": stats.get("dropped_capture_points"),
            "avg_dropped_capture_points": stats.get("avg_dropped_capture_points"),
            "spotted": stats.get("spotted"),
            "stun_number": stats.get("stun_number"),
            "stun_assisted_damage": stats.get("stun_assisted_damage"),
            "battles_on_stunning_vehicles": stats.get("battles_on_stunning_vehicles"),
            "tanking_factor": stats.get("tanking_factor"),
            "wn8": payload.get("wn8")
        }

    def build_tank_performance(self, payload: dict[str, Any]) -> list[TankPerformance]:
        tanks: list[TankPerformance] = []
        
        for item in payload.get("tanks", []):
            tank_meta = item.get("tank") or {}
            diff_data = item.get("diff") or {}

            battles = int(item.get("battles") or 0)
            if battles <= 0:
                continue
            
            tanks.append(TankPerformance(
                tank_id         = int(item.get("tank_id")               or 0),
                tier            = int(tank_meta.get("tier")             or 0),
                type            = str(TYPES.get(tank_meta.get("type"))      or "unknown"),
                nation          = str(NATIONS.get(tank_meta.get("nation"))  or "unknown"),
                name            = str(tank_meta.get("name")             or ""),
                order           = int(tank_meta.get("order")            or 0),

                wn8                 = round(float(item.get("wn8")               or 0), 2),
                battles             = battles,
                avg_damage          = round(float(item.get("damage")            or 0), 2),
                avg_frags           = round(float(item.get("frags")             or 0), 3),
                avg_spotted         = round(float(item.get("spotted")           or 0), 3),
                avg_defence_points  = round(float(item.get("defence_points")    or 0), 3),
                wins                = int(item.get("wins")                      or 0),
                winrate             = round(float(item.get("winrate")           or 0), 2),

                diff_frags          = round(diff_data.get("frags", 0), 3)           if diff_data else None,
                diff_damage         = round(diff_data.get("damage", 0), 2)          if diff_data else None,
                diff_spotted        = round(diff_data.get("spotted", 0), 3)         if diff_data else None,
                diff_defence_points = round(diff_data.get("defence_points", 0), 3)  if diff_data else None,
                diff_winrate        = round(diff_data.get("winrate", 0), 2)         if diff_data else None,
                )
            )
        return sorted(tanks, key=lambda x: x.battles, reverse=True)
    

    def get_nations_summary(self, tanks: list[TankPerformance]) -> dict[str, dict[str, Any]]:
        result = {}
        
        for display_nation in NATIONS.values():
            nation_tanks = [t for t in tanks if t.nation == display_nation]
            if not nation_tanks: continue
            count = len(nation_tanks)

            result[display_nation] = {
                "battles": sum(t.battles for t in nation_tanks), 
                "win_rate": round(sum(t.winrate for t in nation_tanks) / count, 2),
                "avg_damage": round(sum(t.avg_damage for t in nation_tanks) / count, 2),
                "avg_frags": round(sum(t.avg_frags for t in nation_tanks) / count, 3),
                "avg_spotted": round(sum(t.avg_spotted for t in nation_tanks) / count, 3),
                "avg_defence_points": round(sum(t.avg_defence_points for t in nation_tanks) / count, 3),
                "avg_wn8": round(sum(t.wn8 for t in nation_tanks) / count, 2)}

        return result

    def get_tiers_summary(self, tanks: list[TankPerformance]) -> dict[str, dict[str, Any]]:
        result = {}
        
        for tier in range(1, 10):
            tier_tanks = [t for t in tanks if t.tier == tier]
            if not tier_tanks: continue
            count = len(tier_tanks)

            result[tier] = {
                "battles": sum(t.battles for t in tier_tanks), 
                "win_rate": round(sum(t.winrate for t in tier_tanks) / count, 2),
                "avg_damage": round(sum(t.avg_damage for t in tier_tanks) / count, 2),
                "avg_frags": round(sum(t.avg_frags for t in tier_tanks) / count, 3),
                "avg_spotted": round(sum(t.avg_spotted for t in tier_tanks) / count, 3),
                "avg_defence_points": round(sum(t.avg_defence_points for t in tier_tanks) / count, 3),
                "avg_wn8": round(sum(t.wn8 for t in tier_tanks) / count, 2)}

        return result

    def get_types_summary(self, tanks: list[TankPerformance]) -> dict[str, dict[str, Any]]:
        result = {}
        
        for display_name in TYPES.values():
            type_tanks = [t for t in tanks if t.type == display_name]
            if not type_tanks: continue
            count = len(type_tanks)

            result[display_name] = {
                "battles": sum(t.battles for t in type_tanks), 
                "win_rate": round(sum(t.winrate for t in type_tanks) / count, 2),
                "avg_damage": round(sum(t.avg_damage for t in type_tanks) / count, 2),
                "avg_frags": round(sum(t.avg_frags for t in type_tanks) / count, 3),
                "avg_spotted": round(sum(t.avg_spotted for t in type_tanks) / count, 3),
                "avg_defence_points": round(sum(t.avg_defence_points for t in type_tanks) / count, 3),
                "avg_wn8": round(sum(t.wn8 for t in type_tanks) / count, 2)}

        return result

    def top_by_type(self, tanks: list[TankPerformance]) -> dict[str, list[dict[str, Any]]]:
        result = {}
        
        for display_name in TYPES.values():
            type_tanks = [t for t in tanks if t.type == display_name]
            
            by_battles = sorted(type_tanks, key=lambda x: x.battles, reverse=True)[:5]
            by_wn8     = sorted(type_tanks, key=lambda x: x.wn8, reverse=True)[:5]
            
            seen = set()
            combined = []
            for tank in by_battles + by_wn8:
                if tank.tank_id not in seen:
                    combined.append(tank)
                    seen.add(tank.tank_id)
            
            result[display_name] = [asdict(t) for t in combined]
        return result

    def collect_player_stats(self, nickname: str) -> dict[str, Any]:
        payload = self.fetch_player_payload(nickname)
        tanks   = self.build_tank_performance(payload)

        return {
            "profile_meta": self.profile_meta(payload),
            "profile_stat": self.profile_stat(payload),
            "nations_summ": self.get_nations_summary(tanks),
            "tiers_summ":   self.get_tiers_summary(tanks),
            "types_summ":   self.get_types_summary(tanks),
            "top_by_type":  self.top_by_type(tanks),
            "tanks": [asdict(t) for t in tanks],
        }
