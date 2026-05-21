import flet as ft

class TanksTab(ft.Column):
    """Вкладка со списком танков с поддержкой сортировки по любому столбцу"""

    def __init__(self, stats: dict):
        self.tanks = stats.get("tanks", [])
        self.sort_column_index = 4
        self.sort_ascending = False
        self.sorted_tanks = self._sort_tanks()
        
        super().__init__(spacing=10, expand=True)
        
        self.data_table = self._create_data_table()
        
        # Оборачиваем DataTable в Container с expand=True для растягивания
        table_container = ft.Container(
            content=self.data_table,
            expand=True,  # Растягиваем контейнер
            padding=0,
        )

        vertical_scroll_col = ft.Column(
            controls=[self.data_table],
            scroll=ft.ScrollMode.ALWAYS,
            expand=True)
        
        self.controls = [ft.Text(f"Всего танков: {len(self.tanks)}", size=16, weight=ft.FontWeight.BOLD), vertical_scroll_col]

    def _sort_tanks(self):
        tanks_copy = self.tanks.copy()
        reverse = not self.sort_ascending
        key_func = self._get_key_func(self._get_column_field_by_index(self.sort_column_index))
        tanks_copy.sort(key=key_func, reverse=reverse)
        return tanks_copy

    def _get_column_field_by_index(self, index: int) -> str:
        fields = [
            "name", "nation", "type", "tier", "battles", "wins", "winrate",
            "avg_damage", "avg_frags", "avg_spotted", "avg_defence_points",
            "wn8"
        ]
        return fields[index] if index < len(fields) else "battles"

    def _get_key_func(self, column):
        def key_func(tank):
            value = tank.get(column, 0)
            if column in ['battles', 'wins', 'tier', 'tank_id', 'order']:
                return int(value) if value is not None else 0
            elif column in ['wn8', 'avg_damage', 'avg_frags', 'avg_spotted', 'avg_defence_points', 'winrate']:
                return float(value) if value is not None else 0.0
            else:
                return str(value) if value is not None else ''
        return key_func

    def _create_diff_cell(self, avg_value: float, diff_value: float, format_str: str, suffix: str = "") -> ft.DataCell:
        """Создаёт ячейку с основным значением и diff под ним с цветом"""
        
        if format_str == ",.0f":
            main_text = f"{avg_value:,.0f}{suffix}"
        elif format_str == ".2f":
            main_text = f"{avg_value:.2f}{suffix}"
        elif format_str == ".1f":
            main_text = f"{avg_value:.1f}{suffix}"
        else:
            main_text = f"{avg_value}{suffix}"
        
        if diff_value > 0:
            diff_color = ft.Colors.GREEN_400
            sign = "+"
        elif diff_value < 0:
            diff_color = ft.Colors.RED_400
            sign = ""
        else:
            diff_color = ft.Colors.GREY_500
            sign = ""
        
        if format_str == ",.0f":
            diff_text = f"{sign}{diff_value:,.0f}{suffix}"
        elif format_str == ".2f":
            diff_text = f"{sign}{diff_value:.2f}{suffix}"
        elif format_str == ".1f":
            diff_text = f"{sign}{diff_value:.1f}{suffix}"
        else:
            diff_text = f"{sign}{diff_value}{suffix}"
        
        return ft.DataCell(
            content=ft.Column(
                [
                    ft.Text(main_text, size=14, weight=ft.FontWeight.BOLD),
                    ft.Text(diff_text, size=12, color=diff_color),
                ],
                spacing=1,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            )
        )

    def _create_data_table(self):
        """Создаёт DataTable с объединёнными значениями и diff"""
        col_defs = [
            ("Название", "name", "text", None, None, None, 150),  # Добавлена ширина
            ("Нация", "nation", "text", None, None, None, 100),
            ("Тип", "type", "text", None, None, None, 120),
            ("Уровень", "tier", "int", None, None, None, 80),
            ("Бои", "battles", "int", None, ",", None, 100),
            ("Победы", "wins", "int", None, ",", None, 100),
            ("Винрейт", "winrate", "float_with_diff", ".1f", "%", "diff_winrate", 100),
            ("Урон", "avg_damage", "float_with_diff", ",.0f", "", "diff_damage", 110),
            ("Фраги", "avg_frags", "float_with_diff", ".2f", "", "diff_frags", 90),
            ("Обнаруж.", "avg_spotted", "float_with_diff", ".2f", "", "diff_spotted", 100),
            ("Защита", "avg_defence_points", "float_with_diff", ".2f", "", "diff_defence_points", 100),
            ("WN8", "wn8", "float", ".0f", "", None, 100),
        ]

        # Создаём колонки с фиксированной шириной
        columns = []
        for idx, (header, _, col_type, _, _, _, width) in enumerate(col_defs):
            columns.append(
                ft.DataColumn(
                    ft.Text(header, weight=ft.FontWeight.BOLD),
                    on_sort=lambda e, col_idx=idx: self._on_sort(e, col_idx),
                    numeric=True if col_type in ["int", "float", "float_with_diff"] else False,
                    # width=width,  # Раскомментировать если нужна фиксированная ширина
                )
            )

        # Строим строки таблицы
        rows = []
        for tank in self.sorted_tanks[:50]:
            cells = []
            for _, field, col_type, fmt, suffix, diff_field, _ in col_defs:
                raw = tank.get(field, 0) if field in tank else "N/A"
                
                if col_type == "float_with_diff" and diff_field:
                    avg_value = float(raw) if isinstance(raw, (int, float)) else 0.0
                    diff_value = float(tank.get(diff_field, 0)) if diff_field in tank else 0.0
                    cells.append(self._create_diff_cell(avg_value, diff_value, fmt, suffix))
                
                elif col_type == "float":
                    value = float(raw) if isinstance(raw, (int, float)) else 0.0
                    if fmt == ",.0f":
                        text = f"{value:,.0f}{suffix}"
                    elif fmt == ".2f":
                        text = f"{value:.2f}{suffix}"
                    elif fmt == ".1f":
                        text = f"{value:.1f}{suffix}"
                    else:
                        text = str(raw)
                    cells.append(ft.DataCell(ft.Text(text, size=14, text_align=ft.TextAlign.RIGHT)))
                
                elif col_type == "int":
                    value = int(raw) if isinstance(raw, (int, float)) else 0
                    if fmt == ",":
                        text = f"{value:,}{suffix}"
                    else:
                        text = str(value)
                    cells.append(ft.DataCell(ft.Text(text, size=14, text_align=ft.TextAlign.RIGHT)))
                
                else:
                    text = str(raw)
                    if field == "name" and len(text) > 30:
                        text = text[:27] + "..."
                    cells.append(ft.DataCell(ft.Text(text, size=14)))
            
            rows.append(ft.DataRow(cells=cells))

        return ft.DataTable(
            columns=columns,
            rows=rows,
            heading_row_color=ft.Colors.BLUE_GREY_900,
            heading_text_style=ft.TextStyle(color=ft.Colors.WHITE, size=14),
            column_spacing=15,
            sort_column_index=self.sort_column_index,
            sort_ascending=self.sort_ascending,
            expand=True,  # Теперь DataTable растягивается на всю ширину
            width=float("inf"),  # Бесконечная ширина для заполнения пространства
        )

    def _on_sort(self, e: ft.DataColumnSortEvent, column_index: int):
        if self.sort_column_index == column_index:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column_index = column_index
            self.sort_ascending = True

        self.sorted_tanks = self._sort_tanks()
        new_table = self._create_data_table()
        vertical_scroll_col = self.controls[1]
        vertical_scroll_col.controls[0] = new_table
        self.data_table = new_table
        self.update()
