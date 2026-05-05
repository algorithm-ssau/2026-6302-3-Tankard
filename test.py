from parser import TankistStatsParser
import json

parser = TankistStatsParser()

# Получаем полный результат
result = parser.collect_player_stats("eremea", 20)

# Доступные части:
# 1. Основная статистика с описаниями
main_stats = result["player_stats"]

# 2. Сырые данные от источника
raw_data = result["raw_payload"]

# 3. Профиль игрока
profile = result["profile_full"]

# 4. Нормализованные танки
tanks = result["tank_stats_normalized"]

# 5. Агрегации (по типам, нациям, уровням)
summaries = result["summaries"]

# 6. Топы танков
top_tanks = result["top_tanks"]

with open("stats.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print("Файл сохранен: stats.json")
