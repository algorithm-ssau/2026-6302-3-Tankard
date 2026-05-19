# WoT Stats Parser (No Lesta API)

Парсер статистики игрока «Мир Танков» без `application_id` Lesta API.

**Источник:** `https://tankist.net/api/stat/<nickname>`

## Быстрый старт

```python
from parser import parse_player_stats

result = parse_player_stats("MyNickname")

# Данные в памяти
print(result.nickname, result.wn8)
print(result.tanks[0])
print(result.summaries["by_type"])

# Пути к сохранённым JSON
print(result.files.main)
print(result.files.as_dict())
```

CLI (то же самое):

```bash
pip install -r requirements.txt
python parser.py --nickname MyNickname
```

## Единственная функция для кода

| Функция | Назначение |
|---------|------------|
| `parse_player_stats(nickname, ...)` | Загрузка, нормализация, сохранение JSON |

Всё остальное в `parser.py` — внутренняя реализация (`_TankistStatsParser` и т.д.), вызывать не нужно.

### Параметры

| Параметр | По умолчанию | Описание |
|----------|--------------|----------|
| `output` | `player_stats.json` | Главный JSON |
| `out_dir` | `parsed_output` | Папка с остальными файлами |
| `min_battles` | `20` | Порог боёв для агрегатов и топов |
| `top_n` | `20` | Размер каждого топа |
| `save_to_disk` | `True` | `False` — только память, без файлов |
| `verbose` | `False` | Печать путей в консоль |

### Результат `ParsePlayerResult`

| Поле | Содержимое |
|------|------------|
| `main` | Всё в одном объекте (как `player_stats.json` без `_description`) |
| `raw_payload` | Сырой ответ tankist.net |
| `profile` | Профиль + `stats_raw` + `calculated` |
| `tanks_full` | Танки как от API (включая `diff`) |
| `tanks` | Нормализованные танки |
| `summaries` | Агрегаты по типу / нации / уровню / классу |
| `top_tanks` | Топы по WN8, WR, урону, фрагам, боям |
| `files` | `PlayerStatsFiles` с путями (если `save_to_disk=True`) |

### Файлы на диске

- `player_stats.json` — главный файл
- `parsed_output/raw_payload.json`
- `parsed_output/profile_full.json`
- `parsed_output/tanks_full.json`
- `parsed_output/tank_stats_normalized.json`
- `parsed_output/summaries.json`
- `parsed_output/top_tanks.json`

## Важно

- Неофициальный источник; при смене API на tankist.net нужно обновить парсер.
- Средние по всем игрокам на весь список техники этим парсером **не** выгружаются — только статистика одного аккаунта (в т.ч. `diff` к ожидаемым значениям в `tanks_full`).
