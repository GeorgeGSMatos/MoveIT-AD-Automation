import flet as ft
import json
import subprocess
import datetime
import threading
import time
import re

CONFIG_PATH = "config.json"
cancelar_processo = False

def main(page: ft.Page):
    page.title = "MoveIT"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 750
    page.window_height = 600
    page.padding = 20
    page.vertical_alignment = ft.MainAxisAlignment.START

    # --- Carregar Config ---

    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            destinos = json.load(f)
    except FileNotFoundError:
        destinos = {"Erro": "Crie o arquivo config.json"}

    # --- Elementos da UI ---
    
    # 1. Dropdown
    dd_destino = ft.Dropdown(
        label="Selecione o Destino",
        hint_text="Para onde os computadores vão?",
        options=[ft.dropdown.Option(text=nome, key=path) for nome, path in destinos.items()],
        width=710,
        border_radius=10,
        content_padding=15
    )

    # 2. Input
    txt_input = ft.TextField(
        label="Lista de Ativos",
        hint_text="Insira aqui...",
        multiline=True,
        min_lines=1,
        max_lines=10,
        width=710,
        border_radius=10
    )

    # 3. Barra de Progresso
    progress_bar = ft.ProgressBar(width=710, color="blue", bgcolor="#222222", value=0, visible=False)
    lbl_progress = ft.Text("", visible=False, weight="bold")

    # 4. Log
    txt_log = ft.Column(
        controls=[ft.Text("Aguardando início do processamento...", color="grey", italic=True)], 
        scroll=ft.ScrollMode.AUTO, 
        height=180
    )
    
    container_log = ft.Container(
        content=txt_log, 
        bgcolor=ft.colors.BLACK54, 
        padding=15, 
        border_radius=10,
        border=ft.border.all(1, ft.colors.GREY_800),
        width=710
    )

    # --- Lógica ---

    def limpar_nome(nome):
        return re.sub(r'[^a-zA-Z0-9-]', '', nome).upper()

    def mover_no_ad(nome_pc, target_path):
        ps_command = f"""
        try {{
            $pc = Get-ADComputer -Identity '{nome_pc}' -ErrorAction Stop
            Move-ADObject -Identity $pc -TargetPath '{target_path}'
            Write-Host 'SUCESSO'
        }} catch {{
            Write-Host "ERRO: $_"
        }}
        """
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
        return result.stdout.strip()

    def thread_processamento(target_ou, texto_bruto):
        global cancelar_processo
        
        tokens = re.split(r'[,\n;\s]+', texto_bruto)
        lista_pcs = [limpar_nome(t) for t in tokens if t.strip()]
        
        total = len(lista_pcs)
        count_sucesso = 0
        log_para_arquivo = []

        page.run_task(atualizar_ui_inicio, total)

        if total == 0:
            page.run_task(adicionar_log, "⚠️ Nenhum computador válido identificado.", "yellow")
            page.run_task(atualizar_ui_fim, 0, 0)
            return

        for i, nome_pc in enumerate(lista_pcs):
            if cancelar_processo:
                page.run_task(adicionar_log, "🛑 Processo cancelado pelo usuário.", "red")
                log_para_arquivo.append(f"CANCELADO,,{datetime.datetime.now()}")
                break

            progresso = (i) / total
            page.run_task(atualizar_progresso, progresso, f"Processando {i+1} de {total}: {nome_pc}...")

            resultado = mover_no_ad(nome_pc, target_ou)

            if "SUCESSO" in resultado:
                count_sucesso += 1
                page.run_task(adicionar_log, f"✅ {nome_pc}: Movido!", "green")
                log_para_arquivo.append(f"{nome_pc},Sucesso,{datetime.datetime.now()}")
            else:
                erro_msg = resultado.replace("ERRO:", "").strip()
                if "cannot find an object" in erro_msg: erro_msg = "PC não encontrado"
                page.run_task(adicionar_log, f"❌ {nome_pc}: {erro_msg}", "red")
                log_para_arquivo.append(f"{nome_pc},Erro: {erro_msg},{datetime.datetime.now()}")
            
            time.sleep(0.1)

        salvar_log_arquivo(log_para_arquivo)
        page.run_task(atualizar_ui_fim, count_sucesso, total)

    # --- Atualização de UI ---

    async def atualizar_ui_inicio(total):
        txt_log.controls.clear()
        progress_bar.visible = True
        progress_bar.value = 0
        lbl_progress.visible = True
        btn_processar.disabled = True
        btn_cancelar.disabled = False
        txt_input.disabled = True
        dd_destino.disabled = True
        page.update()

    async def atualizar_progresso(valor, texto):
        progress_bar.value = valor
        lbl_progress.value = texto
        page.update()

    async def adicionar_log(texto, cor):
        txt_log.controls.append(ft.Text(texto, color=cor, size=13, font_family="Consolas"))
        page.update()

    async def atualizar_ui_fim(sucesso, total):
        progress_bar.value = 1 if total > 0 else 0
        progress_bar.color = "green"
        lbl_progress.value = f"Concluído: {sucesso} de {total} ativos movidos."
        btn_processar.disabled = False
        btn_cancelar.disabled = True
        txt_input.disabled = False
        dd_destino.disabled = False
        page.update()

    def salvar_log_arquivo(dados):
        try:
            with open("historico_log.csv", "a", encoding='utf-8') as f:
                for linha in dados:
                    f.write(f"{linha}\n")
        except: pass

    # --- Botões ---

    def clique_processar(e):
        global cancelar_processo
        if not dd_destino.value or not txt_input.value:
            return
        cancelar_processo = False
        threading.Thread(target=thread_processamento, args=(dd_destino.value, txt_input.value), daemon=True).start()

    def clique_cancelar(e):
        global cancelar_processo
        cancelar_processo = True
        btn_cancelar.disabled = True
        page.update()

    btn_processar = ft.ElevatedButton(
        text="PROCESSAR",
        icon=ft.icons.PLAY_ARROW,
        on_click=clique_processar,
        style=ft.ButtonStyle(
            bgcolor=ft.colors.GREEN_700, 
            color=ft.colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=8)
        ),
        height=45,
        width=200
    )

    btn_cancelar = ft.ElevatedButton(
        text="CANCELAR",
        icon=ft.icons.CANCEL,
        on_click=clique_cancelar,
        style=ft.ButtonStyle(
            bgcolor=ft.colors.RED_700, 
            color=ft.colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=8)
        ),
        disabled=True,
        height=45,
        width=200
    )

    # --- Layout ---
    
    page.add(
        ft.Text("MoveIT", size=26, weight="bold", color="white"),
        ft.Text("Insira o patrimônio dos ativos abaixo (separados por vírgula ou linha):", size=12, color="grey"),
        txt_input,
        dd_destino,
        ft.Container(height=10),
        ft.Row([btn_processar, btn_cancelar], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
        ft.Container(height=10),
        lbl_progress,
        progress_bar,
        container_log
    )

ft.app(target=main)