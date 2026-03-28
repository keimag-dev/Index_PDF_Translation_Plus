import flet as ft
import time
import asyncio
import os
from collections import defaultdict

# --- ユーザー提供のconfig.pyをインポート ---
# This file is expected to be in the same directory as main.py.
try:
    import config
except ImportError:
    # Fallback if config.py is not found
    print("Error: config.py not found. Using dummy data.")
    class DummyConfig:
        translators = [
            {"category": "コピペ翻訳", "label": "DeepL Web", "description": "deepl.comでPDF中の文章をコピペ翻訳します．", "object": "CopyAndPaste"},
            {"category": "コピペ翻訳", "label": "Google Web", "description": "translate.google.comでPDF中の文章をコピペ翻訳します．", "object": "CopyAndPaste"},
            {"category": "ローカルLLM翻訳", "label": "C3TR-Adapter-Q4_k_m.gguf", "description": "**【必要RAM:8.3GB】**すごいモデルです。", "object": "LocalLLM"},
            {"category": "API翻訳", "label": "Awesome API", "description": "すごいAPIで翻訳します。", "object": "API"},
        ]
    config = DummyConfig()


class AppState:
    """Class to manage the application's state."""
    def __init__(self):
        self.selected_file_path = None
        self.selected_file_name = None
        self.selected_translator_label = None
        self.selected_translator_category = None
        self.api_key = ""

    def set_file(self, path, name):
        self.selected_file_path = path
        self.selected_file_name = name

    def reset(self):
        self.selected_file_path = None
        self.selected_file_name = None
        self.selected_translator_label = None
        self.selected_translator_category = None
        self.api_key = ""

# Instantiate the app state
APP_STATE = AppState()

def main(page: ft.Page):
    page.title = "Indqx PDF 翻訳 Plus"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE_GREY)
    page.window_width = 800
    page.window_min_width = 400
    page.window_height = 720
    page.window_min_height = 600
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # --- Router setup for page navigation ---
    def route_change(route):
        page.views.clear()
        page.views.append(
            ft.View(
                "/",
                [login_view()],
                padding=0,
                vertical_alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        if page.route == "/main":
            page.views.append(
                 ft.View(
                    "/main",
                    [main_view()],
                    # FINAL CORRECTION: Removed bgcolor to let the theme handle it.
                    appbar=ft.AppBar(title=ft.Text("PDF翻訳へようこそ")),
                    bgcolor=ft.Colors.BLUE_GREY_50,
                )
            )
        elif page.route == "/translate":
             page.views.append(
                 ft.View(
                    "/translate",
                    [translation_view()],
                    # FINAL CORRECTION: Removed bgcolor to let the theme handle it.
                    appbar=ft.AppBar(title=ft.Text("翻訳処理中")),
                    bgcolor=ft.Colors.BLUE_GREY_50,
                )
            )
        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop


    # --- 1. Login/Signup Screen ---
    def login_view():
        def login_click(e):
            page.go("/main")

        login_card = ft.Card(
            width=400,
            elevation=8,
            content=ft.Container(
                bgcolor=ft.Colors.WHITE,
                padding=ft.padding.symmetric(vertical=30, horizontal=40),
                border_radius=ft.border_radius.all(8),
                content=ft.Column(
                    spacing=20,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Indqx PDF 翻訳 Plus", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text("ログイン", size=18),
                        ft.TextField(
                            label="メールアドレス",
                            autofocus=True,
                            border=ft.InputBorder.OUTLINE,
                            prefix_icon=ft.Icons.EMAIL_OUTLINED
                        ),
                        ft.TextField(
                            label="パスワード",
                            password=True,
                            can_reveal_password=True,
                            border=ft.InputBorder.OUTLINE,
                            prefix_icon=ft.Icons.LOCK_OUTLINE
                        ),
                        ft.ElevatedButton(
                            text="ログイン",
                            on_click=login_click,
                            width=float("inf"),
                            height=45,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ft.Text("アカウントをお持ちでないですか？"),
                                ft.TextButton("サインアップ", on_click=lambda e: print("サインアップ画面へ"))
                            ]
                        )
                    ]
                )
            )
        )
        
        return ft.Container(
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=[ft.Colors.BLUE_GREY_50, ft.Colors.BLUE_GREY_200],
            ),
            alignment=ft.alignment.center,
            content=login_card
        )


    # --- 2. Main Screen ---
    def main_view():
        def on_dialog_result(e: ft.FilePickerResultEvent):
            if e.files:
                file = e.files[0]
                APP_STATE.set_file(file.path, file.name)
                picked_files.value = f"選択されたファイル: {file.name}"
                drag_target.border = ft.border.all(2, ft.Colors.GREEN_500)
                page.update()

        def on_drag_will_accept(e):
            drag_target.border = ft.border.all(3, ft.Colors.BLUE_400)
            drag_target.bgcolor = ft.Colors.BLUE_GREY_50
            page.update()

        def on_drag_leave(e):
            drag_target.border = ft.border.all(2, ft.Colors.BLUE_GREY_200)
            drag_target.bgcolor = ft.Colors.WHITE
            page.update()

        def on_drop(e: ft.DragTargetEvent):
            file_path = page.get_files(e.data)[0].path
            file_name = os.path.basename(file_path)
            APP_STATE.set_file(file_path, file_name)
            picked_files.value = f"選択されたファイル: {file_name}"
            drag_target.border = ft.border.all(2, ft.Colors.GREEN_500)
            drag_target.bgcolor = ft.Colors.WHITE
            page.update()
        
        def on_translator_change(e):
            APP_STATE.selected_translator_label = e.control.value
            for translator in config.translators:
                if translator["label"] == e.control.value:
                    APP_STATE.selected_translator_category = translator.get("category", "")
                    break
            
            if APP_STATE.selected_translator_category == "API翻訳":
                api_key_field.visible = True
            else:
                api_key_field.visible = False
            page.update()

        def start_translation(e):
            if not APP_STATE.selected_file_path or not APP_STATE.selected_translator_label:
                page.snack_bar = ft.SnackBar(ft.Text("ファイルと翻訳方法を選択してください。"), bgcolor=ft.Colors.RED_200)
                page.snack_bar.open = True
                page.update()
                return
            
            if api_key_field.visible and not api_key_field.value:
                page.snack_bar = ft.SnackBar(ft.Text("APIキーを入力してください。"), bgcolor=ft.Colors.RED_200)
                page.snack_bar.open = True
                page.update()
                return

            APP_STATE.api_key = api_key_field.value
            print(f"翻訳開始: \n  ファイル: {APP_STATE.selected_file_name}\n  翻訳方法: {APP_STATE.selected_translator_label}\n  カテゴリ: {APP_STATE.selected_translator_category}\n  APIキー: {APP_STATE.api_key[:4]}...")
            page.go("/translate")

        file_picker = ft.FilePicker(on_result=on_dialog_result)
        page.overlay.append(file_picker)

        picked_files = ft.Text("ファイルが選択されていません", color=ft.Colors.BLUE_GREY_600)

        drag_target = ft.DragTarget(
            on_will_accept=on_drag_will_accept,
            on_leave=on_drag_leave,
            on_accept=on_drop,
            group="pdf",
            content=ft.Container(
                height=150,
                border=ft.border.all(2, ft.Colors.BLUE_GREY_200),
                border_radius=ft.border_radius.all(12),
                bgcolor=ft.Colors.WHITE,
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.UPLOAD_FILE, size=40, color=ft.Colors.BLUE_GREY_400),
                        ft.Text("ここにファイルをドラッグ＆ドロップ", color=ft.Colors.BLUE_GREY_600),
                        ft.Text("または", color=ft.Colors.BLUE_GREY_400),
                        ft.ElevatedButton("ファイルを選択", on_click=lambda _: file_picker.pick_files(allow_multiple=False, allowed_extensions=["pdf"])),
                    ]
                )
            )
        )

        categorized_translators = defaultdict(list)
        for t in config.translators:
            category = t.get("category", "その他")
            categorized_translators[category].append(t)

        translator_options_group = ft.RadioGroup(content=ft.Column(), on_change=on_translator_change)
        
        translator_cards = []
        for category, translators in categorized_translators.items():
            options = []
            for translator in translators:
                options.append(
                    ft.Row(
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        controls=[
                            ft.Radio(value=translator["label"]),
                            ft.Column(
                                expand=True,
                                spacing=2,
                                controls=[
                                    ft.Markdown(
                                        f"**{translator['label']}**",
                                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
                                    ),
                                    ft.Markdown(
                                        translator["description"],
                                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                                        opacity=0.8
                                    ),
                                ]
                            )
                        ]
                    )
                )
            
            translator_cards.append(
                ft.Card(
                    elevation=2,
                    content=ft.Container(
                        padding=15,
                        content=ft.Column([
                            ft.Text(category, weight=ft.FontWeight.BOLD, size=16),
                            ft.Column(options, spacing=10),
                        ])
                    )
                )
            )
        translator_options_group.content = ft.Column(controls=translator_cards, spacing=15)
        
        api_key_field = ft.TextField(
            label="APIキー", password=True, can_reveal_password=True,
            visible=False, border=ft.InputBorder.OUTLINE,
        )

        return ft.Container(
            padding=20,
            content=ft.Column(
                scroll=ft.ScrollMode.ADAPTIVE,
                spacing=25,
                controls=[
                    ft.Column([
                        ft.Text("1. 翻訳するPDFファイルを選択", size=20, weight=ft.FontWeight.W_600),
                        drag_target,
                        picked_files,
                    ]),
                    ft.Column([
                        ft.Text("2. 翻訳方法を選択", size=20, weight=ft.FontWeight.W_600),
                        translator_options_group,
                        api_key_field,
                    ]),
                    ft.ElevatedButton(
                        "翻訳を開始",
                        icon=ft.Icons.TRANSLATE,
                        on_click=start_translation,
                        height=50,
                        width=float("inf"),
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                            bgcolor=ft.Colors.BLUE_600,
                            color=ft.Colors.WHITE,
                        )
                    )
                ]
            )
        )

    # --- 3. Translation-in-Progress Screen ---
    def translation_view():
        progress_bar = ft.ProgressBar(value=0, bar_height=10)
        progress_text = ft.Text("0%", size=16)
        eta_text = ft.Text("残り時間: 計算中...", italic=True)

        step1_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN)
        step1_text = ft.Text("テキストを抽出")
        step2_icon = ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED, color=ft.Colors.GREY)
        step2_text = ft.Text("翻訳中")
        step3_icon = ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED, color=ft.Colors.GREY)
        step3_text = ft.Text("PDFを作成")
        
        steps_display = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            controls=[
                ft.Row([step1_icon, step1_text]),
                ft.Row([ft.Text("→"), step2_icon, step2_text]),
                ft.Row([ft.Text("→"), step3_icon, step3_text]),
            ]
        )

        original_text_field = ft.TextField(
            label="原文 (コピー用)", multiline=True, read_only=True,
            value="ここにPDFから抽出されたテキストが表示されます。\nこのテキストをコピーして、お好みの翻訳サイト（DeepL, Google翻訳など）に貼り付けて翻訳してください。",
            border=ft.InputBorder.OUTLINE, min_lines=10, max_lines=10,
        )
        translated_text_field = ft.TextField(
            label="翻訳結果をここに貼り付け", multiline=True,
            hint_text="翻訳サイトで生成された訳文を貼り付けてください...",
            border=ft.InputBorder.OUTLINE, min_lines=10, max_lines=10,
        )
        
        def continue_with_paste(e):
            if not translated_text_field.value:
                page.snack_bar = ft.SnackBar(ft.Text("翻訳結果を貼り付けてください。"), bgcolor=ft.Colors.RED_200)
                page.snack_bar.open = True
                page.update()
                return
            
            copy_paste_ui.visible = False
            progress_container.visible = True
            asyncio.create_task(run_step3())

        copy_paste_ui = ft.Container(
            visible=False, padding=ft.padding.symmetric(vertical=10),
            content=ft.Column(
                spacing=20,
                controls=[
                    ft.Text("ステップ 2/3: 翻訳結果を貼り付け", size=18, weight=ft.FontWeight.W_600),
                    ft.Text("以下の原文をコピーし、任意のWeb翻訳サービスで翻訳後、結果を下のボックスに貼り付けてください。"),
                    ft.ResponsiveRow(
                        controls=[
                            ft.Column(col={"md": 6}, controls=[original_text_field]),
                            ft.Column(col={"md": 6}, controls=[translated_text_field]),
                        ], spacing=20,
                    ),
                    ft.ElevatedButton("この翻訳結果で続ける", on_click=continue_with_paste, icon=ft.Icons.CHECK)
                ]
            )
        )
        
        progress_container = ft.Column(
            spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                progress_bar,
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[progress_text, eta_text])
            ]
        )

        main_column = ft.Column(
            alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=30,
            controls=[steps_display, ft.Divider(), progress_container, copy_paste_ui]
        )
        
        async def run_translation_process():
            step1_icon.name = ft.Icons.CHECK_CIRCLE
            step1_icon.color = ft.Colors.GREEN
            step2_icon.name = ft.Icons.SYNC
            step2_icon.color = ft.Colors.BLUE
            page.update()

            for i in range(21):
                progress_bar.value = i / 100
                progress_text.value = f"{i}%"
                eta_text.value = f"残り時間: 約 {(100 - i) * 0.1:.1f} 秒"
                await asyncio.sleep(0.05)
                page.update()

            if APP_STATE.selected_translator_category == "コピペ翻訳":
                progress_container.visible = False
                copy_paste_ui.visible = True
                page.update()
            else:
                for i in range(21, 81):
                    progress_bar.value = i / 100
                    progress_text.value = f"{i}%"
                    eta_text.value = f"残り時間: 約 {(100 - i) * 0.1:.1f} 秒"
                    await asyncio.sleep(0.1)
                    page.update()
                await run_step3()

        async def run_step3():
            step2_icon.name = ft.Icons.CHECK_CIRCLE
            step2_icon.color = ft.Colors.GREEN
            step3_icon.name = ft.Icons.SYNC
            step3_icon.color = ft.Colors.BLUE
            page.update()

            for i in range(81, 101):
                progress_bar.value = i / 100
                progress_text.value = f"{i}%"
                eta_text.value = f"残り時間: 約 {(100 - i) * 0.1:.1f} 秒"
                await asyncio.sleep(0.05)
                page.update()
            
            step3_icon.name = ft.Icons.CHECK_CIRCLE
            step3_icon.color = ft.Colors.GREEN
            eta_text.value = "翻訳完了！"
            page.update()
            
            await asyncio.sleep(2)
            APP_STATE.reset()
            page.go("/main")

        page.run_task(run_translation_process)

        return ft.Container(
            padding=ft.padding.symmetric(vertical=20, horizontal=40),
            content=main_column
        )

    page.go(page.route)

if __name__ == "__main__":
    ft.app(target=main)