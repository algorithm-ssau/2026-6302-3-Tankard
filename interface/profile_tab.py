import flet as ft
import datetime

def create_profile_tab(stats: dict) -> ft.Container:
    meta = stats.get("profile_meta", {})
    prof = stats.get("profile_stat", {})
    types_summ = stats.get("types_summ", {})
    tanks_list = stats.get("tanks", [])

    # --- Функция для получения названия танка по ID ---
    def get_tank_name(id):
        for tank in tanks_list:
            tank_id = tank.get("tank_id")
            if tank_id == id:
                return tank.get("name")
        return f"ID {id}" if id else "N/A"

    # --- Преобразование временных меток ---
    def format_timestamp(ts):
        if ts and isinstance(ts, (int, float)):
            return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        return "N/A"

    created_at = format_timestamp(meta.get("created_at"))
    updated_at = format_timestamp(meta.get("updated_at"))
    last_battle_time = format_timestamp(meta.get("last_battle_time"))

    # --- Основные параметры ---
    battles = prof.get("battles", 0)
    wins = prof.get("wins", 0)
    losses = prof.get("losses", 0)
    draws = prof.get("draws", 0)
    win_rate = round(prof.get("winrate", 0), 2) if battles else 0
    survival_rate = prof.get("survival_rate", 0)  # уже есть в данных
    survived_battles = prof.get("survived_battles", 0)

    # --- Урон и фраги ---
    avg_damage = round(prof.get("avg_damage", 0), 0)
    total_damage = prof.get("damage_dealt", 0)
    damage_received = prof.get("damage_received", 0)
    avg_damage_blocked = prof.get("avg_damage_blocked", 0)
    avg_damage_assisted = prof.get("avg_damage_assisted", 0)
    avg_assist_track = prof.get("avg_damage_assisted_track", 0)
    avg_assist_radio = prof.get("avg_damage_assisted_radio", 0)

    avg_frags = round(prof.get("avg_frags", 0), 2)
    total_frags = prof.get("frags", 0)

    # --- Точность ---
    shots = prof.get("shots", 0)
    hits = prof.get("hits", 0)
    hit_percent = prof.get("hits_percents", 0)
    piercings = prof.get("piercings", 0)
    piercings_received = prof.get("piercings_received", 0)
    direct_hits_received = prof.get("direct_hits_received", 0)
    no_damage_hits_received = prof.get("no_damage_direct_hits_received", 0)
    explosion_hits = prof.get("explosion_hits", 0)
    explosion_hits_received = prof.get("explosion_hits_received", 0)

    # --- Опыт ---
    avg_xp = round(prof.get("battle_avg_xp", 0), 0)
    total_xp = prof.get("xp", 0)
    max_xp = prof.get("max_xp", 0)
    max_xp_tank = get_tank_name(prof.get("max_xp_tank_id", "N/A"))

    # --- Максимальные достижения ---
    max_damage = prof.get("max_damage", 0)
    max_damage_tank = get_tank_name(prof.get("max_damage_tank_id", "N/A"))
    max_frags = prof.get("max_frags", 0)
    max_frags_tank = get_tank_name(prof.get("max_frags_tank_id", "N/A"))

    # --- Разведка и капы ---
    spotted = prof.get("spotted", 0)
    avg_spotted = round(spotted / battles, 2) if battles else 0
    capture_points = prof.get("capture_points", 0)
    dropped_capture_points = prof.get("dropped_capture_points", 0)

    # --- Стан и осколки ---
    stun_number = prof.get("stun_number", 0)
    stun_assisted_damage = prof.get("stun_assisted_damage", 0)
    battles_on_stun_vehicles = prof.get("battles_on_stunning_vehicles", 0)

    # --- Прочее ---
    tanking_factor = prof.get("tanking_factor", 0)
    wn8 = prof.get("wn8", 0)

    # Определяем цвет WN8 (примерная градация)
    if wn8 < 300:
        wn8_color = ft.Colors.RED_900
    elif wn8 < 600:
        wn8_color = ft.Colors.RED_400
    elif wn8 < 900:
        wn8_color = ft.Colors.ORANGE_400
    elif wn8 < 1300:
        wn8_color = ft.Colors.YELLOW_700
    elif wn8 < 1800:
        wn8_color = ft.Colors.GREEN_400
    else:
        wn8_color = ft.Colors.BLUE_400

    # --- Лучший класс по среднему WN8 из types_summ ---
    best_class = "N/A"
    best_wn8 = -1
    if types_summ:
        for class_name, class_stats in types_summ.items():
            class_wn8 = class_stats.get("avg_wn8", 0)
            if class_wn8 > best_wn8:
                best_wn8 = class_wn8
                best_class = class_name

    # ========== КАРТОЧКА 1: Профиль и метаданные ==========
    card_profile = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text(f"Никнейм: {meta.get('nickname', 'N/A')}", size=16, weight=ft.FontWeight.BOLD),
                ft.Text(f"ID аккаунта: {meta.get('account_id', 'N/A')}", size=14),
                ft.Text(f"Глобальный рейтинг: {meta.get('global_rating', 'N/A')}", size=14),
                ft.Text(f"Источник: {meta.get('source', 'N/A')}", size=12, color=ft.Colors.GREY_600),
                ft.Divider(),
                ft.Text("Временные метки:", size=12, weight=ft.FontWeight.BOLD),
                ft.Text(f"Создан: {created_at}", size=11, color=ft.Colors.GREY_700),
                ft.Text(f"Обновлён: {updated_at}", size=11, color=ft.Colors.GREY_700),
                ft.Text(f"Последний бой: {last_battle_time}", size=11, color=ft.Colors.GREY_700),
                ft.Text(f"Сбор данных: {meta.get('collected_at_utc', 'N/A')[:19]}", size=11, color=ft.Colors.GREY_500),
            ], spacing=6),
            padding=15,
        ),
        expand=True,
    )

    # ========== КАРТОЧКА 2: Общая статистика боёв ==========
    card_battles = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("📊 Боевая статистика", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text(f"Всего боёв: {battles:,}", size=14),
                ft.Text(f"Побед: {wins:,} | Поражений: {losses:,} | Ничьих: {draws:,}", size=12),
                ft.Text(f"Процент побед: {win_rate}%", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400 if win_rate >= 50 else ft.Colors.RED_400),
                ft.Row([ft.Text("Выживаемость:", size=13), ft.Text(f"{survival_rate}% ({survived_battles:,} боев)", size=13)]),
                ft.Row([ft.Text("Фактор танкования:", size=13), ft.Text(f"{tanking_factor:.2f}", size=13)]),
                ft.Text(f"Очки захвата: {capture_points:,} | Сбито очков: {dropped_capture_points:,}", size=12)
            ], spacing=8),
            padding=15,
        ),
        expand=True,
    )

    # ========== КАРТОЧКА 3: Урон и фраги ==========
    card_damage = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("💥 Урон и фраги", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text(f"Средний урон: {avg_damage:,.0f}", size=14),
                ft.Text(f"Всего нанесено: {total_damage:,}", size=12),
                ft.Text(f"Получено урона: {damage_received:,}", size=12),
                ft.Text(f"Ср. заблокировано: {avg_damage_blocked:.0f}", size=12),
                ft.Text(f"Ср. ассистированный урон: {avg_damage_assisted:.0f}", size=12),
                ft.Text(f"  - по гуслям: {avg_assist_track:.0f}", size=11, color=ft.Colors.GREY_700),
                ft.Text(f"  - по разведке: {avg_assist_radio:.0f}", size=11, color=ft.Colors.GREY_700),
                ft.Text(f"Средние фраги: {avg_frags:.2f} (всего {total_frags:,})", size=14),
            ], spacing=7),
            padding=15,
        ),
        expand=True,
    )

    # ========== КАРТОЧКА 4: Точность и попадания ==========
    card_accuracy = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("🎯 Точность", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text(f"Процент попаданий: {hit_percent}%", size=14),
                ft.Text(f"Выстрелов: {shots:,} | Попаданий: {hits:,}", size=12),
                ft.Text(f"Пробитий: {piercings:,}", size=12),
                ft.Text(f"Пробитий по вам: {piercings_received:,}", size=12),
                ft.Text(f"Прямых попаданий получено: {direct_hits_received:,}", size=12),
                ft.Text(f"Из них без урона: {no_damage_hits_received:,}", size=12),
                ft.Text(f"Фугасных попаданий (своих): {explosion_hits:,}", size=12),
                ft.Text(f"Фугасных попаданий по вам: {explosion_hits_received:,}", size=12),
            ], spacing=7),
            padding=15,
        ),
        expand=True,
    )

    # ========== КАРТОЧКА 5: Опыт и максимумы ==========
    card_maxima = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("🏆 Достижения", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text(f"Средний опыт: {avg_xp:.0f} (всего {total_xp:,})", size=13),
                ft.Text(f"Макс. опыт: {max_xp} ({max_xp_tank})", size=12),
                ft.Text(f"Макс. урон: {max_damage:,} ({max_damage_tank})", size=12),
                ft.Text(f"Макс. фрагов: {max_frags} ({max_frags_tank})", size=12),
                ft.Text(f"Лучший класс: {best_class}" if best_class != "N/A" else "Лучший класс: не определён", size=12)
            ], spacing=8),
            padding=15,
        ),
        expand=True,
    )

    # ========== КАРТОЧКА 6: Разведка, стан и WN8 ==========
    card_vision = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("👁️ Разведка и стан", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text(f"Средняя разведка: {avg_spotted:.2f} (всего {spotted:,})", size=13),
                ft.Text(f"Стан: {stun_number} раз | Урон от стана: {stun_assisted_damage:,}", size=12),
                ft.Text(f"Бои на технике со станом: {battles_on_stun_vehicles}", size=12),
                ft.Divider(),
                ft.Text(f"Рейтинг WN8:", size=14, weight=ft.FontWeight.BOLD),
                ft.Text(f"{wn8}", size=20, weight=ft.FontWeight.BOLD, color=wn8_color),
            ], spacing=8),
            padding=15,
        ),
        expand=True,
    )

    # Собираем всё в адаптивную сетку
    return ft.Container(
        content=ft.Column(
            [
                ft.ResponsiveRow(
                    [
                        ft.Container(content=card_profile, col={"sm": 12, "md": 6, "lg": 4}),
                        ft.Container(content=card_battles, col={"sm": 12, "md": 6, "lg": 4}),
                        ft.Container(content=card_damage, col={"sm": 12, "md": 6, "lg": 4}),
                        ft.Container(content=card_accuracy, col={"sm": 12, "md": 6, "lg": 4}),
                        ft.Container(content=card_maxima, col={"sm": 12, "md": 6, "lg": 4}),
                        ft.Container(content=card_vision, col={"sm": 12, "md": 6, "lg": 4}),
                    ],
                    spacing=15,
                    run_spacing=15,
                ),
            ],
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=20,
        expand=True,
    )
