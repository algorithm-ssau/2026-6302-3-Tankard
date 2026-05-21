import flet as ft

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