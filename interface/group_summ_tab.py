import flet as ft

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
