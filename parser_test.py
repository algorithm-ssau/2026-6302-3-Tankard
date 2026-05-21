
from parser import TankistStatsParser
import json

parser = TankistStatsParser()

# Получаем полный результат
result = parser.collect_player_stats("eremea")

with open("git_ignore/stats.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print("Файл сохранен: stats.json")
