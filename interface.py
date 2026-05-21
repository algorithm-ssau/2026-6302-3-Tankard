import flet as ft
from parser import TankistStatsParser, ParserError
from ai_agent import AIStatsAnalyzer
from tanksTab import TanksTab
import asyncio
import concurrent.futures


class StatsInterface:
    def __init__(self):
        self.parser = TankistStatsParser()

    def fetch_player_stats(self, nickname: str) -> dict | None:
        try:
            result = self.parser.collect_player_stats(nickname)
            return result
        except ParserError as e:
            raise Exception(str(e))
        except Exception as e:
            raise Exception(f"Ошибка при получении данных: {str(e)}")


import datetime
import flet as ft

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

def create_tanks_tab(stats: dict) -> ft.Column:
    return TanksTab(stats)


def create_group_summaries_tab(stats: dict) -> ft.Container:
    """Вкладка с групповыми сводками (по типам, нациям, уровням)"""
    # Данные уже имеют нужный формат: словарь {ключ: {battles, win_rate, avg_damage, ...}}
    types_raw = stats.get("types_summ", {})
    nations_raw = stats.get("nations_summ", {})
    tiers_raw = stats.get("tiers_summ", {})
    
    def dict_to_list(data: dict) -> list:
        """Преобразует словарь {key: stats} в список [{"key": key, ...}]"""
        result = []
        for key, values in data.items():
            entry = {
                "key": key,
                "battles": values.get("battles", 0),
                "win_rate": values.get("win_rate", 0),
                "avg_damage": values.get("avg_damage", 0),
                "avg_frags": values.get("avg_frags", 0),
                "avg_wn8": values.get("avg_wn8", 0),
            }
            result.append(entry)
        return result
    
    types_list = dict_to_list(types_raw)
    nations_list = dict_to_list(nations_raw)
    tiers_list = dict_to_list(tiers_raw)
    
    # Таблицы
    type_table = _create_group_table(types_list)
    nation_table = _create_group_table(nations_list)
    tier_table = _create_group_table(tiers_list)
    
    type_content = ft.Container(content=ft.ListView(controls=[type_table]), padding=10, expand=True)
    nation_content = ft.Container(content=ft.ListView(controls=[nation_table]), padding=10, expand=True)
    tier_content = ft.Container(content=ft.ListView(controls=[tier_table]), padding=10, expand=True)
    
    inner_tabs = ft.Tabs(
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(tabs=[ft.Tab("По типам"), ft.Tab("По нациям"), ft.Tab("По уровням")]),
                ft.TabBarView(expand=True, controls=[type_content, nation_content, tier_content]),
            ],
        ),
        length=3,
        selected_index=0,
        expand=True,
    )
    
    return ft.Container(content=inner_tabs, padding=20, expand=True)


def _create_group_table(group_data: list) -> ft.DataTable:
    """Создание таблицы для групповых сводок (список словарей с ключами key, battles, win_rate, ...)"""
    rows = []
    for group in group_data:
        rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(group.get("key", "N/A"))[:30])),
                    ft.DataCell(ft.Text(f"{group.get('battles', 0):,}")),
                    ft.DataCell(ft.Text(f"{group.get('win_rate', 0)}%")),
                    ft.DataCell(ft.Text(f"{group.get('avg_damage', 0):,.0f}")),
                    ft.DataCell(ft.Text(f"{group.get('avg_frags', 0):.2f}")),
                    ft.DataCell(ft.Text(f"{group.get('avg_wn8', 0):.0f}")),
                ]
            )
        )
    
    return ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Группа", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Бои", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Винрейт", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Урон", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Фраги", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("WN8", weight=ft.FontWeight.BOLD)),
        ],
        rows=rows,
        heading_row_color=ft.Colors.BLUE_GREY_900,
        heading_text_style=ft.TextStyle(color=ft.Colors.WHITE),
    )


def create_top_tanks_tab(stats: dict) -> ft.Container:
    """Вкладка с топами танков (по WN8, винрейту, урону, фрагам, боям)"""
    tanks = stats.get("tanks", [])
    min_battles = 20  # минимальное число боев для попадания в топы
    
    # Фильтруем танки с достаточным числом боев
    filtered_tanks = [t for t in tanks if t.get("battles", 0) >= min_battles]
    
    # Сортируем и берем топ-10 по каждому критерию
    top_by_wn8 = sorted(filtered_tanks, key=lambda x: x.get("wn8", 0), reverse=True)[:10]
    top_by_winrate = sorted(filtered_tanks, key=lambda x: x.get("winrate", 0), reverse=True)[:10]
    top_by_avg_damage = sorted(filtered_tanks, key=lambda x: x.get("avg_damage", 0), reverse=True)[:10]
    top_by_avg_frags = sorted(filtered_tanks, key=lambda x: x.get("avg_frags", 0), reverse=True)[:10]
    top_by_battles = sorted(filtered_tanks, key=lambda x: x.get("battles", 0), reverse=True)[:10]
    
    # Таблицы
    table_wn8 = _create_top_table(top_by_wn8)
    table_winrate = _create_top_table(top_by_winrate)
    table_damage = _create_top_table(top_by_avg_damage)
    table_frags = _create_top_table(top_by_avg_frags)
    table_battles = _create_top_table(top_by_battles)
    
    inner_tabs = ft.Tabs(
        length=5,
        selected_index=0,
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(tabs=[ft.Tab("По WN8"), ft.Tab("По винрейту"), ft.Tab("По урону"), ft.Tab("По фрагам"), ft.Tab("По боям")]),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        ft.Container(content=ft.ListView(controls=[table_wn8]), padding=10, expand=True),
                        ft.Container(content=ft.ListView(controls=[table_winrate]), padding=10, expand=True),
                        ft.Container(content=ft.ListView(controls=[table_damage]), padding=10, expand=True),
                        ft.Container(content=ft.ListView(controls=[table_frags]), padding=10, expand=True),
                        ft.Container(content=ft.ListView(controls=[table_battles]), padding=10, expand=True),
                    ],
                ),
            ],
        ),
    )
    
    return ft.Container(
        content=ft.Column([
            ft.Text(f"Топы формируются из танков с минимум {min_battles} боями", size=12, color=ft.Colors.GREY_500),
            inner_tabs,
        ]),
        padding=20,
        expand=True,
    )


def _create_top_table(tanks: list) -> ft.DataTable:
    """Создает таблицу для топов (список танков)"""
    rows = []
    for i, tank in enumerate(tanks, 1):
        rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(i), weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(tank.get("name", "N/A")[:25])),
                    ft.DataCell(ft.Text(str(tank.get("battles", 0)))),
                    ft.DataCell(ft.Text(f"{tank.get('winrate', 0)}%")),
                    ft.DataCell(ft.Text(f"{tank.get('avg_damage', 0):,.0f}")),
                    ft.DataCell(ft.Text(f"{tank.get('wn8', 0):.0f}")),
                ]
            )
        )
    
    return ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("#", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Танк", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Бои", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Винрейт", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Урон", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("WN8", weight=ft.FontWeight.BOLD)),
        ],
        rows=rows,
        heading_row_color=ft.Colors.BLUE_GREY_900,
        heading_text_style=ft.TextStyle(color=ft.Colors.WHITE),
    )


async def update_ai_analysis_async(page: ft.Page, ai_input: ft.TextField, ai_analyst, stats: dict):
    """Асинхронно обновляет поле с анализом ИИ (не блокирует UI)"""
    if not stats:
        ai_input.value = ""
        page.update()
        return
    
    if ai_analyst is None:
        ai_input.value = "⚠️ ИИ-аналитик не доступен. Запусти 'ollama serve' в терминале"
        page.update()
        return
    
    ai_input.value = "🤔 Анализирую статистику... (20-60 секунд)"
    page.update()
    
    try:
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(pool, ai_analyst.analyze, stats)
        ai_input.value = result
    except Exception as e:
        ai_input.value = f"❌ Ошибка анализа: {str(e)}"
    finally:
        page.update()


def main(page: ft.Page):
    page.title = "Анализатор игровой статистики World of Tanks"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.window_width = 800
    page.window_height = 1200
    
    interface = StatsInterface()
    
    # Создаём ИИ-аналитика (если доступен)
    try:
        ai_analyst = AIStatsAnalyzer(model_name="qwen2.5:7b-instruct")
        print("✅ ИИ-аналитик готов")
    except Exception as e:
        print(f"⚠️ ИИ-аналитик не готов: {e}")
        ai_analyst = None
    
    # Элементы интерфейса
    nickname_field = ft.TextField(
        label="Введите никнейм игрока",
        width=400,
        hint_text="например, AMWAY777",
        autofocus=True,
        text_size=16,
    )
    
    search_button = ft.ElevatedButton("Получить статистику", width=200)
    error_text = ft.Text("", color=ft.Colors.RED_400, size=14, visible=False)
    loading_indicator = ft.ProgressRing(width=30, height=30, visible=False)
    
    main_tabs = ft.Tabs(
        length=4,
        selected_index=0,
        visible=False,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tab_alignment=ft.TabAlignment.CENTER,
                    tabs=[ft.Tab(label="Профиль"), ft.Tab(label="Танки"), ft.Tab(label="Сводки"), ft.Tab(label="Топы")],
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        ft.Container(expand=True),
                        ft.Container(expand=True),
                        ft.Container(expand=True),
                        ft.Container(expand=True),
                    ],
                ),
            ],
        ),
    )
    
    # Поле для ИИ-агента
    ai_input = ft.TextField(
        label="🤖 Анализ от ИИ-агента",
        hint_text="Анализ появится автоматически после загрузки статистики...",
        multiline=True,
        min_lines=5,
        max_lines=15,
        read_only=True,
        expand=True,
    )
    
    ai_section = ft.Column(
        [ft.Divider(height=20), ft.Text("🤖 Анализ от ИИ-агента", size=18, weight=ft.FontWeight.BOLD), ai_input],
        visible=False,
        expand=True,
    )
    
    status_text = ft.Text("", size=12, color=ft.Colors.GREY_400, visible=False)
    
    def update_ui_with_stats(stats: dict):
        """Обновляет интерфейс новыми данными"""
        try:
            tab_bar_view = main_tabs.content.controls[1]
            tab_bar_view.controls[0].content = create_profile_tab(stats)
            tab_bar_view.controls[1].content = create_tanks_tab(stats)
            tab_bar_view.controls[2].content = create_group_summaries_tab(stats)
            tab_bar_view.controls[3].content = create_top_tanks_tab(stats)
            
            main_tabs.visible = True
            ai_section.visible = True
            
            collected_at = stats.get("profile_meta", {}).get("collected_at_utc", "неизвестно")
            status_text.value = f"📊 Данные загружены | Обновлено: {collected_at[:19]}"
            status_text.visible = True
            
            page.update()
            
            # Запускаем асинхронный ИИ-анализ
            asyncio.create_task(update_ai_analysis_async(page, ai_input, ai_analyst, stats))
            
        except Exception as e:
            print(f"Ошибка обновления UI: {e}")
    
    def on_search_click(e):
        nickname = nickname_field.value.strip()
        
        if not nickname:
            error_text.value = "❌ Введите никнейм игрока!"
            error_text.visible = True
            page.update()
            return
        
        error_text.visible = False
        search_button.disabled = True
        loading_indicator.visible = True
        page.update()
        
        try:
            stats = interface.fetch_player_stats(nickname)
            if stats:
                update_ui_with_stats(stats)
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"✅ Статистика для {nickname} успешно загружена!"),
                    bgcolor=ft.Colors.GREEN_700,
                )
                page.snack_bar.open = True
        except Exception as e:
            error_text.value = f"❌ Ошибка: {str(e)}"
            error_text.visible = True
            main_tabs.visible = False
            ai_section.visible = False
            status_text.visible = False
        finally:
            search_button.disabled = False
            loading_indicator.visible = False
            page.update()
    
    search_button.on_click = on_search_click
    nickname_field.on_submit = on_search_click
    
    page.add(
        ft.SafeArea(
            expand=True,
            content=ft.Column(
                [
                    ft.Row([nickname_field, search_button, loading_indicator], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                    error_text,
                    ft.Container(content=main_tabs, expand=True),
                    ft.Container(content=ai_section, height=200),
                    ft.Row([status_text], alignment=ft.MainAxisAlignment.CENTER),
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            ),
        )
    )


if __name__ == "__main__":
    ft.app(target=main)