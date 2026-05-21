import flet as ft
import asyncio
import concurrent.futures

from parser import TankistStatsParser, ParserError
from AI     import analyze_stats
from interface.tanks_tab      import create_tanks_tab
from interface.profile_tab    import create_profile_tab
from interface.group_summ_tab import create_group_summaries_tab
from interface.tops_tab       import create_top_tanks_tab

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

async def ai_analysis(page: ft.Page, ai_input: ft.TextField, stats: dict):
    ai_input.value = "🤔 Анализирую статистику... (20-60 секунд)"
    page.update()
    
    try:
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(pool, analyze_stats, stats)
        ai_input.value = result
    except Exception as e:
        ai_input.value = f"❌ Ошибка анализа: {str(e)}"
    finally:
        page.update()


def main(page: ft.Page):
    page.title = "Анализатор игровой статистики World of Tanks"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    
    interface = StatsInterface()
    
    # Элементы интерфейса
    nickname_field = ft.TextField(label="Введите никнейм игрока", width=400, autofocus=True, text_size=16,)
    
    search_button = ft.ElevatedButton("Получить статистику", width=200)
    error_text = ft.Text("", color=ft.Colors.RED_400, size=14, visible=False)
    
    main_tabs = ft.Tabs(length=4, selected_index=0, visible=False, content=ft.Column(expand=True, controls=[
                ft.TabBar(tab_alignment=ft.TabAlignment.CENTER,
                    tabs=[ft.Tab(label="Профиль"), ft.Tab(label="Танки"), ft.Tab(label="Сводки"), ft.Tab(label="Топы")]),
                ft.TabBarView(expand=True, controls=[
                    ft.Container(expand=True),
                    ft.Container(expand=True),
                    ft.Container(expand=True),
                    ft.Container(expand=True)
                    ])]))
    
    # Поле для ИИ-агента
    ai_input   = ft.TextField(label="Анализ от ИИ", multiline=True, min_lines=5, max_lines=15, read_only=True, expand=True)
    ai_section = ft.Column([ft.Divider(height=20), ai_input],visible=False,expand=True,)
    

    def update_ui(stats: dict):
        try:
            tab_bar_view = main_tabs.content.controls[1]
            tab_bar_view.controls[0].content = create_profile_tab(stats)
            tab_bar_view.controls[1].content = create_tanks_tab(stats)
            tab_bar_view.controls[2].content = create_group_summaries_tab(stats)
            tab_bar_view.controls[3].content = create_top_tanks_tab(stats)
            
            main_tabs.visible = True
            ai_section.visible = True
            page.update()
            asyncio.create_task(ai_analysis(page, ai_input, stats))
            
        except Exception as e: print(f"Ошибка обновления UI: {e}")
    
    def on_search_click(e):
        nickname = nickname_field.value.strip()
        
        if not nickname:
            error_text.value = "Введите никнейм игрока!"
            error_text.visible = True
            page.update()
            return
        
        try:
            stats = interface.fetch_player_stats(nickname)
            update_ui(stats)
        except Exception as e:
            error_text.value = f"Ошибка: {str(e)}"
            error_text.visible = True
        finally: page.update()
    
    search_button.on_click = on_search_click
    nickname_field.on_submit = on_search_click
    
    page.add(ft.SafeArea(expand=True, content=ft.Column(
        spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER,expand=True, controls=[
                    ft.Row([nickname_field, search_button], alignment=ft.MainAxisAlignment.CENTER, spacing=20), error_text,
                    ft.Container(content=main_tabs, expand=True),
                    ft.Container(content=ai_section, height=200)])))


if __name__ == "__main__":
    ft.app(target=main)