import flet as ft
import json
from pathlib import Path
from parser import TankistStatsParser, ParserError
from ai_agent import AIStatsAnalyzer
import asyncio
import concurrent.futures

STATS_FILE = Path("stats.json")

class StatsInterface:
    def __init__(self):
        self.parser = TankistStatsParser()
        self.current_stats = None
        
    def load_stats_from_file(self) -> dict | None:
        """Загружает статистику из файла если он существует"""
        if STATS_FILE.exists():
            try:
                with open(STATS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Ошибка загрузки файла: {e}")
        return None
    
    def save_stats_to_file(self, stats: dict):
        """Сохраняет статистику в файл"""
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    
    def fetch_player_stats(self, nickname: str) -> dict | None:
        """Получает статистику игрока через парсер"""
        try:
            result = self.parser.collect_player_stats(
                nickname, 
                min_battles_for_class_summary=20
            )
            return result["player_stats"]
        except ParserError as e:
            raise Exception(str(e))
        except Exception as e:
            raise Exception(f"Ошибка при получении данных: {str(e)}")

def create_profile_tab(stats: dict) -> ft.Container:
    """Вкладка с общим профилем игрока"""
    profile = stats.get("profile", {})
    meta = stats.get("meta", {})
    calculated = profile.get("calculated", {})
    insights = stats.get("insights", {})
    
    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Основная информация", size=18, weight=ft.FontWeight.BOLD),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(f"Никнейм: {meta.get('nickname', 'N/A')}", size=16),
                            ft.Text(f"Account ID: {meta.get('account_id', 'N/A')}", size=14),
                            ft.Text(f"Глобальный рейтинг: {meta.get('global_rating', 'N/A')}", size=14),
                            ft.Text(f"Общий WN8: {profile.get('wn8', 'N/A')}", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400),
                            ft.Text(f"Дата сбора: {meta.get('collected_at_utc', 'N/A')[:19]}", size=12, color=ft.Colors.GREY_500),
                        ]),
                        padding=15,
                    ),
                ),
                
                ft.Text("Игровая статистика", size=18, weight=ft.FontWeight.BOLD),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(f"Всего боев: {calculated.get('battles', 0):,}", size=15),
                            ft.Text(f"Побед: {calculated.get('wins', 0):,} | Поражений: {calculated.get('losses', 0):,} | Ничьих: {calculated.get('draws', 0):,}", size=14),
                            ft.Text(f"Процент побед: {calculated.get('win_rate_percent', 0)}%", size=15, weight=ft.FontWeight.BOLD),
                            ft.Text(f"Средний урон за бой: {calculated.get('avg_damage_per_battle', 0):,.0f}", size=14),
                            ft.Text(f"Средние фраги: {calculated.get('avg_frags_per_battle', 0):.2f}", size=14),
                            ft.Text(f"Средние разведданные: {calculated.get('avg_spots_per_battle', 0):.2f}", size=14),
                            ft.Text(f"Средний опыт: {calculated.get('avg_xp_per_battle', 0):.0f}", size=14),
                            ft.Text(f"Выживаемость: {calculated.get('survival_rate_percent', 0)}%", size=14),
                        ]),
                        padding=15,
                    ),
                ),
                
                ft.Text("Аналитика", size=18, weight=ft.FontWeight.BOLD),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(f"Лучший класс техники: {insights.get('best_vehicle_class', 'N/A')}", size=14),
                            ft.Text(f"Порог боев для учета: {insights.get('min_battles_for_class_summary', 20)}", size=12),
                        ]),
                        padding=15,
                    ),
                ),
            ],
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=20,
        expand=True,
    )

def create_tanks_tab(stats: dict) -> ft.Container:
    """Вкладка со списком танков"""
    tanks = stats.get("tank_stats", [])
    
    rows = []
    for tank in tanks[:50]:
        rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(tank.get("name", "N/A")[:30])),
                    ft.DataCell(ft.Text(tank.get("type", "N/A"))),
                    ft.DataCell(ft.Text(str(tank.get("tier", "N/A")))),
                    ft.DataCell(ft.Text(f"{tank.get('battles', 0):,}")),
                    ft.DataCell(ft.Text(f"{tank.get('win_rate', 0)}%")),
                    ft.DataCell(ft.Text(f"{tank.get('avg_damage', 0):,.0f}")),
                    ft.DataCell(ft.Text(f"{tank.get('avg_frags', 0):.2f}")),
                    ft.DataCell(ft.Text(f"{tank.get('wn8', 0):.0f}")),
                ]
            )
        )
    
    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Название", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Тип", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Уровень", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Бои", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Винрейт", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Урон", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Фраги", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("WN8", weight=ft.FontWeight.BOLD)),
        ],
        rows=rows,
        heading_row_color=ft.Colors.BLUE_GREY_900,
        heading_text_style=ft.TextStyle(color=ft.Colors.WHITE),
        column_spacing=20,
        expand=True,
    )
    
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(f"Всего танков: {len(tanks)}", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("Показаны первые 50 танков по количеству боев", size=12, color=ft.Colors.GREY_500),
                ft.Container(content=data_table, expand=True),
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=20,
        expand=True,
    )

def create_class_summary_tab(stats: dict) -> ft.Container:
    """Вкладка с агрегацией по классам"""
    classes = stats.get("class_summary", [])
    
    rows = []
    for cls in classes:
        rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(cls.get("vehicle_type", "N/A"))),
                    ft.DataCell(ft.Text(f"{cls.get('battles', 0):,}")),
                    ft.DataCell(ft.Text(f"{cls.get('win_rate', 0)}%")),
                    ft.DataCell(ft.Text(f"{cls.get('avg_damage', 0):,.0f}")),
                    ft.DataCell(ft.Text(f"{cls.get('avg_frags', 0):.2f}")),
                    ft.DataCell(ft.Text(f"{cls.get('avg_wn8', 0):.0f}")),
                ]
            )
        )
    
    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Класс", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Бои", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Винрейт", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Урон", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Фраги", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("WN8", weight=ft.FontWeight.BOLD)),
        ],
        rows=rows,
        heading_row_color=ft.Colors.BLUE_GREY_900,
        heading_text_style=ft.TextStyle(color=ft.Colors.WHITE),
        expand=True,
    )
    
    return ft.Container(content=data_table, padding=20, expand=True)

def create_group_summaries_tab(stats: dict) -> ft.Container:
    """Вкладка с групповыми сводками"""
    groups = stats.get("group_summaries", {})
    
    inner_tabs = ft.Tabs(
        length=3,
        selected_index=0,
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label="По типам"),
                        ft.Tab(label="По нациям"),
                        ft.Tab(label="По уровням"),
                    ],
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        ft.Container(content=_create_group_table(groups.get("by_type", [])), padding=10, expand=True),
                        ft.Container(content=_create_group_table(groups.get("by_nation", [])), padding=10, expand=True),
                        ft.Container(content=_create_group_table(groups.get("by_tier", [])), padding=10, expand=True),
                    ],
                ),
            ],
        ),
    )
    
    return ft.Container(content=inner_tabs, padding=20, expand=True)

def _create_group_table(data: list) -> ft.DataTable:
    """Создает таблицу для групповых данных"""
    rows = []
    for item in data:
        rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(item.get("key", "N/A")))),
                    ft.DataCell(ft.Text(f"{item.get('battles', 0):,}")),
                    ft.DataCell(ft.Text(f"{item.get('tank_count', 0)}")),
                    ft.DataCell(ft.Text(f"{item.get('win_rate', 0)}%")),
                    ft.DataCell(ft.Text(f"{item.get('avg_damage', 0):,.0f}")),
                    ft.DataCell(ft.Text(f"{item.get('avg_wn8', 0):.0f}")),
                ]
            )
        )
    
    return ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Группа", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Бои", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Танков", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Винрейт", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Урон", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("WN8", weight=ft.FontWeight.BOLD)),
        ],
        rows=rows,
        heading_row_color=ft.Colors.BLUE_GREY_900,
        heading_text_style=ft.TextStyle(color=ft.Colors.WHITE),
        expand=True,
    )

def create_top_tanks_tab(stats: dict) -> ft.Container:
    """Вкладка с топами танков"""
    tops = stats.get("top_tanks", {})
    criteria = tops.get("criteria", {})
    
    inner_tabs = ft.Tabs(
        length=5,
        selected_index=0,
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label="По WN8"),
                        ft.Tab(label="По винрейту"),
                        ft.Tab(label="По урону"),
                        ft.Tab(label="По фрагам"),
                        ft.Tab(label="По боям"),
                    ],
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        ft.Container(content=_create_top_table(tops.get("by_wn8", [])), expand=True),
                        ft.Container(content=_create_top_table(tops.get("by_win_rate", [])), expand=True),
                        ft.Container(content=_create_top_table(tops.get("by_avg_damage", [])), expand=True),
                        ft.Container(content=_create_top_table(tops.get("by_avg_frags", [])), expand=True),
                        ft.Container(content=_create_top_table(tops.get("by_battles", [])), expand=True),
                    ],
                ),
            ],
        ),
    )
    
    return ft.Container(
        content=ft.Column([
            ft.Text(f"Топы формируются из танков с минимум {criteria.get('min_battles', 20)} боями", 
                   size=12, color=ft.Colors.GREY_500),
            inner_tabs,
        ]),
        padding=20,
        expand=True,
    )

def _create_top_table(tanks: list) -> ft.DataTable:
    """Создает таблицу для топов"""
    rows = []
    for i, tank in enumerate(tanks[:10], 1):
        rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(i), weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(tank.get("name", "N/A")[:25])),
                    ft.DataCell(ft.Text(str(tank.get("battles", 0)))),
                    ft.DataCell(ft.Text(f"{tank.get('win_rate', 0)}%")),
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
        expand=True,
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
        # Запускаем синхронный метод analyze в отдельном потоке через run_in_executor
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
    page.window_width = 1200
    page.window_height = 800
    
    interface = StatsInterface()
    
    # Создаём ИИ-аналитика
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
    
    search_button = ft.ElevatedButton(
        "Получить статистику",
        width=200,
    )
    
    error_text = ft.Text("", color=ft.Colors.RED_400, size=14, visible=False)
    loading_indicator = ft.ProgressRing(width=30, height=30, visible=False)
    
    # Создаем Tabs
    main_tabs = ft.Tabs(
        length=5,
        selected_index=0,
        visible=False,
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tab_alignment=ft.TabAlignment.CENTER,
                    tabs=[
                        ft.Tab(label="Профиль"),
                        ft.Tab(label="Танки"),
                        ft.Tab(label="Классы"),
                        ft.Tab(label="Сводки"),
                        ft.Tab(label="Топы"),
                    ],
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        ft.Container(expand=True),
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
    )
    
    ai_section = ft.Column(
        [
            ft.Divider(height=20),
            ft.Text("🤖 Анализ от ИИ-агента", size=18, weight=ft.FontWeight.BOLD),
            ai_input,
        ],
        visible=False,
    )
    
    status_text = ft.Text("", size=12, color=ft.Colors.GREY_400, visible=False)
    
    def update_ui_with_stats(stats: dict):
        """Обновляет интерфейс новыми данными"""
        try:
            tab_bar_view = main_tabs.content.controls[1]
            tab_bar_view.controls[0].content = create_profile_tab(stats)
            tab_bar_view.controls[1].content = create_tanks_tab(stats)
            tab_bar_view.controls[2].content = create_class_summary_tab(stats)
            tab_bar_view.controls[3].content = create_group_summaries_tab(stats)
            tab_bar_view.controls[4].content = create_top_tanks_tab(stats)
            
            main_tabs.visible = True
            ai_section.visible = True
            
            collected_at = stats.get("meta", {}).get("collected_at_utc", "неизвестно")
            status_text.value = f"📊 Данные загружены | Обновлено: {collected_at[:19]}"
            status_text.visible = True
            
            page.update()
            
            # Запускаем асинхронный ИИ-анализ (не блокирует UI!)
            asyncio.create_task(update_ai_analysis_async(page, ai_input, ai_analyst, stats))
            
        except Exception as e:
            print(f"Ошибка обновления UI: {e}")
    
    def load_from_file():
        """Загружает данные из файла при старте"""
        stats = interface.load_stats_from_file()
        if stats:
            interface.current_stats = stats
            update_ui_with_stats(stats)
        else:
            main_tabs.visible = False
            ai_section.visible = False
            page.update()
    
    def on_search_click(e):
        """Обработчик поиска статистики"""
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
                interface.save_stats_to_file(stats)
                interface.current_stats = stats
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
    
    # Сборка интерфейса
    page.add(
        ft.SafeArea(
            expand=True,
            content=ft.Column(
                [
                    ft.Row(
                        [ft.Icon(ft.Icons.ANALYTICS, size=40), 
                         ft.Text("Анализатор игровой статистики WoT", size=28, weight=ft.FontWeight.BOLD)],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Divider(height=20),
                    ft.Row(
                        [nickname_field, search_button, loading_indicator],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=20,
                    ),
                    error_text,
                    main_tabs,
                    ai_section,
                    ft.Row([status_text], alignment=ft.MainAxisAlignment.CENTER),
                ],
                spacing=15,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            ),
        )
    )
    
    load_from_file()

if __name__ == "__main__":
    ft.app(target=main)