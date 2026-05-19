import flet as ft
import json
from pathlib import Path
from parser import TankistStatsParser, ParserError
from ai_agent import AIStatsAnalyzer
import asyncio
import concurrent.futures

class StatsInterface:
    def __init__(self):
        self.parser = TankistStatsParser()
        self.current_stats = None

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

class_names = {
        "SPG": "Арта",
        "heavyTank": "Тяжелый танк",
        "AT-SPG": "ПТ-САУ",
        "mediumTank": "Средний танк",
        "lightTank": "Легкий танк",
    }
nation_names = {
        "ussr": "СССР",
        "germany": "Германия",
        "usa": "США",
        "china": "Китай",
        "france": "Франция",
        "uk": "Великобритания",
        "japan": "Япония",
        "czech": "Чехия",
        "poland": "Польша",
        "sweden": "Швеция",
        "italy": "Италия",
    }

def create_profile_tab(stats: dict) -> ft.Container:
    """Вкладка с общим профилем игрока"""
    profile = stats.get("profile", {})
    meta = stats.get("meta", {})
    calculated = profile.get("calculated", {})
    insights = stats.get("insights", {})
    
    # Карточка 1: Основная информация
    card_profile = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Основная информация", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text(f"Никнейм: {meta.get('nickname', 'N/A')}", size=14),
                ft.Text(f"Account ID: {meta.get('account_id', 'N/A')}", size=12),
                ft.Text(f"Глобальный рейтинг: {meta.get('global_rating', 'N/A')}", size=14),
                ft.Text(f"Общий WN8: {profile.get('wn8', 'N/A')}", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400),
                ft.Text(f"Дата сбора: {meta.get('collected_at_utc', 'N/A')[:19]}", size=11, color=ft.Colors.GREY_500),
            ]),
            padding=15,
        ),
        expand=True,
    )
    
    # Карточка 2: Игровая статистика
    card_stats = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Игровая статистика", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text(f"Всего боев: {calculated.get('battles', 0):,}", size=14),
                ft.Text(f"Побед: {calculated.get('wins', 0):,} | Поражений: {calculated.get('losses', 0):,} | Ничьих: {calculated.get('draws', 0):,}", size=12),
                ft.Text(f"Процент побед: {calculated.get('win_rate_percent', 0)}%", size=15, weight=ft.FontWeight.BOLD),
                ft.Text(f"Средний урон: {calculated.get('avg_damage_per_battle', 0):,.0f}", size=14),
                ft.Text(f"Средние фраги: {calculated.get('avg_frags_per_battle', 0):.2f}", size=14),
                ft.Text(f"Средние разведданные: {calculated.get('avg_spots_per_battle', 0):.2f}", size=12),
                ft.Text(f"Средний опыт: {calculated.get('avg_xp_per_battle', 0):.0f}", size=14),
                ft.Text(f"Выживаемость: {calculated.get('survival_rate_percent', 0)}%", size=14),
            ]),
            padding=15,
        ),
        expand=True,
    )
    
    # Карточка 3: Аналитика
    card_analytics = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Аналитика", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text(f"Лучший класс: {insights.get('best_vehicle_class', 'N/A')}", size=14),
                ft.Text(f"Порог боев для учета: {insights.get('min_battles_for_class_summary', 20)}", size=12),
            ]),
            padding=15,
        ),
        expand=True,
    )
    
    return ft.Container(
        content=ft.Column(
            [
                ft.ResponsiveRow(
                    [
                        ft.Container(
                            content=card_profile,
                            col={"sm": 12, "md": 6, "lg": 4},
                        ),
                        ft.Container(
                            content=card_stats,
                            col={"sm": 12, "md": 6, "lg": 4},
                        ),
                        ft.Container(
                            content=card_analytics,
                            col={"sm": 12, "md": 12, "lg": 4},
                        ),
                    ],
                    spacing=10,
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
                ft.ListView(
                    controls=[data_table],
                    expand=True,
                ),
            ],
            spacing=10,
            expand=True,
        ),
        padding=20,
        expand=True,
    )

def create_group_summaries_tab(stats: dict) -> ft.Container:
    """Вкладка с групповыми сводками"""
    groups = stats.get("group_summaries", {})

    # Маппинг для перевода значений
    def translate_type(value):
        return class_names.get(value, value)
    
    def translate_nation(value):
        return nation_names.get(value, value)
    
    def translate_tier(value):
        return str(value)
    
    # Создаем контейнеры для каждой вкладки с обработкой названий
    type_content = ft.Container(
        content=ft.ListView(
            controls=[_create_group_table(
                groups.get("by_type", []),
                name_translator=translate_type
            )],
            expand=True,
        ),
        padding=10,
        expand=True,
    )
    
    nation_content = ft.Container(
        content=ft.ListView(
            controls=[_create_group_table(
                groups.get("by_nation", []),
                name_translator=translate_nation
            )],
            expand=True,
        ),
        padding=10,
        expand=True,
    )
    
    tier_content = ft.Container(
        content=ft.ListView(
            controls=[_create_group_table(
                groups.get("by_tier", []),
                name_translator=translate_tier
            )],
            expand=True,
        ),
        padding=10,
        expand=True,
    )
    
    inner_tabs = ft.Tabs(
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab("По типам"),
                        ft.Tab("По нациям"),
                        ft.Tab("По уровням"),
                    ],
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        type_content,
                        nation_content,
                        tier_content,
                    ],
                ),
            ],
        ),
        length=3,
        selected_index=0,
        expand=True,
    )
    
    return ft.Container(content=inner_tabs, padding=20, expand=True)


def _create_group_table(group_data: list, name_translator=None) -> ft.DataTable:
    """Создание таблицы для групповых сводок с опциональным переводом названий"""
    if name_translator is None:
        name_translator = lambda x: x
    
    rows = []
    for group in group_data:
        # Переводим название группы, если есть переводчик
        group_name = name_translator(group.get("key", "N/A"))
        
        rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(group_name)[:30])),
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
                        ft.Container(
                            content=ft.ListView(
                                controls=[_create_top_table(tops.get("by_wn8", []))],
                                expand=True,
                            ),
                            padding=10,
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.ListView(
                                controls=[_create_top_table(tops.get("by_win_rate", []))],
                                expand=True,
                            ),
                            padding=10,
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.ListView(
                                controls=[_create_top_table(tops.get("by_avg_damage", []))],
                                expand=True,
                            ),
                            padding=10,
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.ListView(
                                controls=[_create_top_table(tops.get("by_avg_frags", []))],
                                expand=True,
                            ),
                            padding=10,
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.ListView(
                                controls=[_create_top_table(tops.get("by_battles", []))],
                                expand=True,
                            ),
                            padding=10,
                            expand=True,
                        ),
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
    page.window_width = 800
    page.window_height = 1200
    
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

    main_tabs = ft.Tabs(
        length=4,
        selected_index=0,
        visible=False,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tab_alignment=ft.TabAlignment.CENTER,
                    tabs=[
                        ft.Tab(label="Профиль"),
                        ft.Tab(label="Танки"),
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
        expand=True,  # Растягиваем по ширине
    )

    ai_section = ft.Column(
        [
            ft.Divider(height=20),
            ft.Text("🤖 Анализ от ИИ-агента", size=18, weight=ft.FontWeight.BOLD),
            ai_input,
        ],
        visible=False,
        expand=True,  # Чтобы Column тоже растягивался
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
            
            collected_at = stats.get("meta", {}).get("collected_at_utc", "неизвестно")
            status_text.value = f"📊 Данные загружены | Обновлено: {collected_at[:19]}"
            status_text.visible = True
            
            page.update()
            
            # Запускаем асинхронный ИИ-анализ (не блокирует UI!)
            asyncio.create_task(update_ai_analysis_async(page, ai_input, ai_analyst, stats))
            
        except Exception as e:
            print(f"Ошибка обновления UI: {e}")
    
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
                    # Верхняя строка поиска - фиксированная
                    ft.Row(
                        [nickname_field, search_button, loading_indicator],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=20,
                    ),
                    
                    # Ошибки - фиксированная
                    error_text,
                    
                    # Основные вкладки - занимают всё доступное пространство
                    ft.Container(
                        content=main_tabs,
                        expand=True,
                    ),
                    
                    # AI секция - фиксированная высота
                    ft.Container(
                        content=ai_section,
                        height=200,
                    ),
                    
                    # Статус бар - фиксированный
                    ft.Row([status_text], alignment=ft.MainAxisAlignment.CENTER),
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            ),
        )
    )

if __name__ == "__main__":
    ft.app(
        target=main,
        host="192.168.0.105", 
        port=8501, 
        view=ft.AppView.WEB_BROWSER
    )
