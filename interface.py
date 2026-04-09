import flet as ft
import json

def parser(nickname: str):
    if nickname == "testuser":
        stats = {
            "nickname": "TestUser",
            "level": 42,
            "rating": 1850,
            "wins": 120,
            "losses": 45,
            "winrate": 72.7,
            "games_played": 165,
            "kills": 1340,
            "deaths": 980,
            "assists": 560,
            "kda": 1.94
        }
        return stats
    return False

def ai_agent(data: dict):
    return "анализ ИИ"

def main(page: ft.Page):
    page.title = "Анализатор игровой статистики"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # Элементы интерфейса
    result_column = ft.Column(controls=[], spacing=10, visible=False)
    error_text = ft.Text(value="", color=ft.Colors.RED_400, size=16, visible=False)

    def on_search_click(e):
        error_text.visible = False
        result_column.visible = False
        result_column.controls.clear()
        page.update()

        nickname = nickname_field.value.strip()
        if not nickname:
            error_text.value = "Введите никнейм!"
            error_text.visible = True
            page.update()
            return

        stats = parser(nickname)
        
        if stats is False:
            error_text.value = f"Игрок с никнеймом '{nickname}' не найден."
            error_text.visible = True
            page.update()
            return

        stats_json_str = json.dumps(stats, indent=4, ensure_ascii=False)
        analysis = ai_agent(stats)

        # Добавляем в колонку элементы с результатами
        result_column.controls.append(ft.Text("Статистика игрока:", size=18, weight=ft.FontWeight.BOLD))
        result_column.controls.append(ft.Text(stats_json_str, font_family="monospace", size=14))
        result_column.controls.append(ft.Divider(height=20, thickness=1))
        result_column.controls.append(ft.Text("Анализ от ИИ-агента:", size=18, weight=ft.FontWeight.BOLD))
        result_column.controls.append(ft.Text(analysis, size=14))
        
        result_column.visible = True
        page.update()

    nickname_field = ft.TextField(label="Введите никнейм игрока", width=300, 
        hint_text="например, testuser", autofocus=True, on_submit=on_search_click)
    search_button = ft.ElevatedButton(content=ft.Text("Найти и проанализировать"), on_click=on_search_click, width=300)

    # Сборка интерфейса
    page.add(
        ft.Column(
            [
                ft.Text("Анализатор игрового профиля", size=24, weight=ft.FontWeight.BOLD),
                nickname_field,
                search_button,
                error_text,
                result_column
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        )
    )

ft.app(target=main)
