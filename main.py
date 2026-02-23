import flet as ft
import json
import subprocess
import datetime
import threading
import time
import re

# =============================================================================
# 1. GLOBAL CONFIGURATION & CONSTANTS
# =============================================================================

ARQUIVO_CONFIG = "config.json"
ARQUIVO_LOG = "historico_log.csv"

# --- Control Flag ---
cancelar_processo = False

# =============================================================================
# 2. BACKEND LOGIC
# =============================================================================


def carregar_configuracoes():
    """
    Reads the JSON file containing the Organizational Unit (OU) mappings.
    Returns:
        dict: Target OUs or an error message.
    """
    try:
        with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"CRITICAL ERROR: Please create config.json": ""}
    except json.JSONDecodeError:
        return {"ERROR: Malformed config.json file": ""}


def limpar_hostname(nome):
    """
    Sanitizes the hostname string: removes special chars, spaces,
    and converts to Uppercase.
    Example: ' pc-01, ' -> 'PC-01'
    """
    return re.sub(r"[^a-zA-Z0-9-]", "", nome).upper()


def registrar_log(dados_linha):
    """
    Appends the operation result to the local CSV log file.
    """
    try:
        with open(ARQUIVO_LOG, "a", encoding="utf-8") as f:
            for linha in dados_linha:
                f.write(f"{linha}\n")
    except Exception as e:
        print(f"Error saving log: {e}")


def executar_powershell(hostname, target_path):
    """
    Builds and executes the PowerShell script to move the AD object.

    Args:
        hostname (str): The computer name.
        target_path (str): The LDAP Distinguished Name (DN) of the target OU.

    Returns:
        str: Script stdout or caught error message.
    """
    # --- Encapsulated PowerShell ---
    script_ps = f"""
    try {{
        $pc = Get-ADComputer -Identity '{hostname}' -ErrorAction Stop
        Move-ADObject -Identity $pc -TargetPath '{target_path}'
        Write-Host 'SUCESSO'
    }} catch {{
        Write-Host "ERRO: $_"
    }}
    """

    # --- Configuration ---
    info_startup = subprocess.STARTUPINFO()
    info_startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    try:
        resultado = subprocess.run(
            ["powershell", "-Command", script_ps],
            capture_output=True,
            text=True,
            startupinfo=info_startup,
        )
        return resultado.stdout.strip()
    except Exception as e:
        return f"SYSTEM ERROR: {str(e)}"


# =============================================================================
# 3. FLET APPLICATION
# =============================================================================


def main(page: ft.Page):

    # --- Window Configuration ---
    page.title = "MoveIT - AD Automation"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 700
    page.window_height = 750
    page.padding = 25
    page.vertical_alignment = ft.MainAxisAlignment.START

    # --- Load Initial ---
    destinos_ad = carregar_configuracoes()

    # -------------------------------------------------------------------------
    # UI COMPONENTS
    # -------------------------------------------------------------------------

    # --- App Header ---
    lbl_titulo = ft.Text(
        value="MoveIT - AD Automation",
        size=28,
        weight=ft.FontWeight.BOLD,
        color="white",
    )

    lbl_subtitulo = ft.Text(
        value="Ferramenta de Migração e Organização de Ativos", size=14, color="grey"
    )

    # --- Destination Selection ---
    dd_destino = ft.Dropdown(
        label="Destino (OU)",
        hint_text="Selecione a Unidade Organizacional de destino...",
        options=[ft.dropdown.Option(text=k, key=v) for k, v in destinos_ad.items()],
        width=700,
        border_radius=8,
        content_padding=15,
        text_size=15,
    )

    # --- Hostname List ---
    txt_input = ft.TextField(
        label="Lista de Hostnames",
        hint_text="Cole a lista aqui (Um por linha, ou separados por vírgula)...",
        multiline=True,
        min_lines=6,
        max_lines=8,
        width=700,
        border_radius=8,
        text_size=14,
    )

    # --- Progress Indicators ---
    barra_progresso = ft.ProgressBar(
        width=700, color="blue", bgcolor="#222222", value=0, visible=False
    )

    lbl_status_progresso = ft.Text(
        value="", visible=False, weight=ft.FontWeight.BOLD, size=14
    )

    # --- Log Console ---
    coluna_logs = ft.Column(
        controls=[ft.Text("Aguardando comando...", color="grey", italic=True)],
        scroll=ft.ScrollMode.AUTO,
        auto_scroll=True,
    )

    container_logs = ft.Container(
        content=coluna_logs,
        height=200,
        width=700,
        bgcolor="#111111",
        padding=15,
        border_radius=10,
        border=ft.border.all(1, "#333333"),
    )

    # -------------------------------------------------------------------------
    # UI UPDATE FUNCTIONS
    # -------------------------------------------------------------------------

    async def ui_iniciar_tarefa(total_items):
        """Prepares the UI for the start of the process."""
        barra_progresso.visible = True
        barra_progresso.value = 0
        lbl_status_progresso.visible = True

        coluna_logs.controls.clear()

        # --- Lock Inputs ---
        txt_input.disabled = True
        dd_destino.disabled = True
        btn_processar.disabled = True
        btn_cancelar.disabled = False

        page.update()

    async def ui_atualizar_progresso(valor, texto):
        """Updates the progress bar."""
        barra_progresso.value = valor
        lbl_status_progresso.value = texto
        page.update()

    async def ui_adicionar_log(mensagem, cor_texto):
        """Appends a new line to the virtual console."""
        coluna_logs.controls.append(
            ft.Text(value=mensagem, color=cor_texto, font_family="Consolas", size=13)
        )
        page.update()

    async def ui_finalizar_tarefa(sucesso, total):
        """Restores the UI state."""
        barra_progresso.value = 1 if total > 0 else 0
        barra_progresso.color = "green"

        lbl_status_progresso.value = (
            f"Processo finalizado: {sucesso}/{total} máquinas movidas."
        )

        # --- Unlock Inputs ---
        txt_input.disabled = False
        dd_destino.disabled = False
        btn_processar.disabled = False
        btn_cancelar.disabled = True

        page.update()

    # -------------------------------------------------------------------------
    # WORKER THREAD
    # -------------------------------------------------------------------------

    def thread_processamento(caminho_ou, texto_bruto):
        global cancelar_processo

        # ---Input Processing ---
        tokens = re.split(r"[,\n;\s]+", texto_bruto)
        lista_maquinas = [limpar_hostname(t) for t in tokens if t.strip()]

        total = len(lista_maquinas)
        cont_sucesso = 0
        buffer_csv = []

        # --- Update Initial UI ---
        page.run_task(ui_iniciar_tarefa, total)

        # --- Validate Empty list ---
        if total == 0:
            page.run_task(ui_adicionar_log, "⚠️ A lista está vazia.", "yellow")
            page.run_task(ui_finalizar_tarefa, 0, 0)
            return

        # --- Execution Loop ---
        for i, hostname in enumerate(lista_maquinas):
            if cancelar_processo:
                page.run_task(ui_adicionar_log, "🛑 Operação interrompida.", "red")
                buffer_csv.append(f"CANCELLED_BY_USER,,{datetime.datetime.now()}")
                break

            progresso_atual = i / total
            page.run_task(
                ui_atualizar_progresso,
                progresso_atual,
                f"Processando {i + 1} de {total}: {hostname}...",
            )

            # --- Execute AD Action ---
            resultado = executar_powershell(hostname, caminho_ou)
            timestamp = datetime.datetime.now()

            if "SUCESSO" in resultado:
                cont_sucesso += 1
                page.run_task(ui_adicionar_log, f"✅ {hostname} -> Movido", "green")
                buffer_csv.append(f"{hostname},Success,{timestamp}")
            else:
                msg_erro = resultado.replace("ERRO:", "").strip()
                if "cannot find an object" in msg_erro:
                    msg_erro = "Hostname not found in AD"

                page.run_task(ui_adicionar_log, f"❌ {hostname}: {msg_erro}", "red")
                buffer_csv.append(f"{hostname},Error: {msg_erro},{timestamp}")

            time.sleep(0.1)

        # ---Finalization ---
        registrar_log(buffer_csv)
        page.run_task(ui_finalizar_tarefa, cont_sucesso, total)

    # -------------------------------------------------------------------------
    # EVENT HANDLERS
    # -------------------------------------------------------------------------

    def ao_clicar_processar(e):
        global cancelar_processo

        if not dd_destino.value:
            coluna_logs.controls.append(
                ft.Text("⚠️ Selecione um destino primeiro!", color="yellow")
            )
            page.update()
            return

        if not txt_input.value:
            coluna_logs.controls.append(
                ft.Text("⚠️ Insira os hostnames!", color="yellow")
            )
            page.update()
            return

        cancelar_processo = False

        threading.Thread(
            target=thread_processamento,
            args=(dd_destino.value, txt_input.value),
            daemon=True,
        ).start()

    def ao_clicar_cancelar(e):
        global cancelar_processo
        cancelar_processo = True
        btn_cancelar.disabled = True
        page.update()

    # -------------------------------------------------------------------------
    # ACTION BUTTONS
    # -------------------------------------------------------------------------

    btn_processar = ft.ElevatedButton(
        content=ft.Text(value="INICIAR MIGRAÇÃO", size=14, weight=ft.FontWeight.BOLD),
        style=ft.ButtonStyle(
            bgcolor="green",
            color="white",
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        width=200,
        height=50,
        on_click=ao_clicar_processar,
    )

    btn_cancelar = ft.ElevatedButton(
        content=ft.Text(value="CANCELAR", size=14, weight=ft.FontWeight.BOLD),
        style=ft.ButtonStyle(
            bgcolor="red",
            color="white",
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        width=200,
        height=45,
        disabled=True,
        on_click=ao_clicar_cancelar,
    )

    # -------------------------------------------------------------------------
    # FINAL LAYOUT ASSEMBLY
    # -------------------------------------------------------------------------

    page.add(
        ft.Column(
            controls=[
                lbl_titulo,
                lbl_subtitulo,
                ft.Container(height=15),
                txt_input,
                dd_destino,
                ft.Container(height=20),
                ft.Row(
                    controls=[btn_processar, btn_cancelar],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                ),
                ft.Container(height=20),
                lbl_status_progresso,
                barra_progresso,
                container_logs,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )


if __name__ == "__main__":
    ft.app(target=main)
