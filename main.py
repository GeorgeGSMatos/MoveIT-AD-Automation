"""
MoveIT - Ferramenta de Automação para Active Directory.

Aplicação desktop construída com Flet que automatiza a migração em massa
de objetos (computadores) entre Unidades Organizacionais (OUs) no Active
Directory, com sanitização de dados na entrada e geração de telemetria
estruturada (logs CSV) para rastreabilidade.
"""

import datetime
import json
import re
import subprocess
import threading
import time

import flet as ft

# ==============================================================================
# 1. CONFIGURAÇÃO GLOBAL E CONSTANTES
# ==============================================================================

ARQUIVO_CONFIG: str = "config.json"
ARQUIVO_LOG: str = "historico_log.csv"

cancelar_processo: bool = False
"""Flag global de controle para interrupção do processamento em lote."""

# ==============================================================================
# 2. LÓGICA DE BACKEND (CAMADA DE DADOS E EXECUÇÃO)
# ==============================================================================


# --- 2.1. Carregamento de Configuração ---


def carregar_configuracoes() -> dict[str, str]:
    """Carrega o dicionário de destinos (OUs) a partir do arquivo JSON.

    Lê o arquivo ``config.json`` que mapeia nomes amigáveis de destino
    para seus respectivos caminhos LDAP (Distinguished Names).

    Returns:
        Dicionário ``{nome_exibição: caminho_ldap}`` ou mensagem de erro
        encapsulada em dicionário caso o arquivo esteja ausente ou corrompido.
    """
    try:
        with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"ERRO CRÍTICO: Crie o arquivo config.json": ""}
    except json.JSONDecodeError:
        return {"ERRO: Arquivo config.json mal formatado": ""}


# --- 2.2. Sanitização de Dados (Data Cleansing) ---


def limpar_hostname(nome: str) -> str:
    """Sanitiza o hostname removendo caracteres inválidos e padronizando.

    Aplica Regex para eliminar qualquer caractere que não seja
    alfanumérico ou hífen, e converte o resultado para maiúsculas.

    Args:
        nome: String bruta do hostname informado pelo usuário.

    Returns:
        Hostname limpo e padronizado em maiúsculas.

    Examples:
        >>> limpar_hostname(" pc-01, ")
        'PC-01'
    """
    return re.sub(r"[^a-zA-Z0-9-]", "", nome).upper()


# --- 2.3. Persistência de Telemetria (Logging) ---


def registrar_log(dados_linha: list[str]) -> None:
    """Persiste os resultados das operações no arquivo de log CSV.

    Cada linha contém hostname, status da operação e timestamp,
    gerando dados estruturados para auditoria e análise futura.

    Args:
        dados_linha: Lista de strings formatadas em CSV para gravação.
    """
    try:
        with open(ARQUIVO_LOG, "a", encoding="utf-8") as f:
            for linha in dados_linha:
                f.write(f"{linha}\n")
    except Exception as e:
        print(f"Erro ao salvar log: {e}")


# --- 2.4. Execução PowerShell (Conector AD) ---


def executar_powershell(hostname: str, target_path: str) -> str:
    """Executa o script PowerShell para mover o objeto no Active Directory.

    Realiza validação prévia (``Get-ADComputer``) da existência do ativo
    antes de executar a movimentação (``Move-ADObject``), funcionando
    como uma verificação de integridade referencial.

    Args:
        hostname: Nome do computador a ser movido.
        target_path: Distinguished Name (DN) LDAP da OU de destino.

    Returns:
        Saída do script contendo 'SUCESSO' ou mensagem de erro capturada.
    """
    script_ps = f"""
    try {{
        $pc = Get-ADComputer -Identity '{hostname}' -ErrorAction Stop
        Move-ADObject -Identity $pc -TargetPath '{target_path}'
        Write-Host 'SUCESSO'
    }} catch {{
        Write-Host "ERRO: $_"
    }}
    """

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
        return f"ERRO DE SISTEMA: {str(e)}"


# ==============================================================================
# 3. APLICAÇÃO FLET (CAMADA DE APRESENTAÇÃO)
# ==============================================================================


def main(page: ft.Page) -> None:
    """Ponto de entrada da aplicação Flet.

    Configura a janela, monta os componentes de interface, define os
    handlers de evento e orquestra o fluxo de processamento em lote
    através de threads dedicadas.

    Args:
        page: Instância da página principal fornecida pelo framework Flet.
    """

    # --- 3.1. Configuração da Janela ---

    page.title = "MoveIT - AD Automation"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 700
    page.window_height = 750
    page.padding = 25
    page.vertical_alignment = ft.MainAxisAlignment.START

    destinos_ad: dict[str, str] = carregar_configuracoes()

    # --- 3.2. Componentes de Interface ---

    lbl_titulo = ft.Text(
        value="MoveIT - AD Automation",
        size=28,
        weight=ft.FontWeight.BOLD,
        color="white",
    )

    lbl_subtitulo = ft.Text(
        value="Ferramenta de Migração e Organização de Ativos", size=14, color="grey"
    )

    dd_destino = ft.Dropdown(
        label="Destino (OU)",
        hint_text="Selecione a Unidade Organizacional de destino...",
        options=[ft.dropdown.Option(text=k, key=v) for k, v in destinos_ad.items()],
        width=700,
        border_radius=8,
        content_padding=15,
        text_size=15,
    )

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

    barra_progresso = ft.ProgressBar(
        width=700, color="blue", bgcolor="#222222", value=0, visible=False
    )

    lbl_status_progresso = ft.Text(
        value="", visible=False, weight=ft.FontWeight.BOLD, size=14
    )

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

    # --- 3.3. Funções de Atualização da Interface ---

    async def ui_iniciar_tarefa(total_items: int) -> None:
        """Prepara a interface para o início do processamento em lote."""
        barra_progresso.visible = True
        barra_progresso.value = 0
        lbl_status_progresso.visible = True

        coluna_logs.controls.clear()

        txt_input.disabled = True
        dd_destino.disabled = True
        btn_processar.disabled = True
        btn_cancelar.disabled = False

        page.update()

    async def ui_atualizar_progresso(valor: float, texto: str) -> None:
        """Atualiza a barra de progresso e o rótulo de status."""
        barra_progresso.value = valor
        lbl_status_progresso.value = texto
        page.update()

    async def ui_adicionar_log(mensagem: str, cor_texto: str) -> None:
        """Adiciona uma nova linha ao console virtual de logs."""
        coluna_logs.controls.append(
            ft.Text(value=mensagem, color=cor_texto, font_family="Consolas", size=13)
        )
        page.update()

    async def ui_finalizar_tarefa(sucesso: int, total: int) -> None:
        """Restaura o estado da interface após a conclusão do processamento."""
        barra_progresso.value = 1 if total > 0 else 0
        barra_progresso.color = "green"

        lbl_status_progresso.value = (
            f"Processo finalizado: {sucesso}/{total} máquinas movidas."
        )

        txt_input.disabled = False
        dd_destino.disabled = False
        btn_processar.disabled = False
        btn_cancelar.disabled = True

        page.update()

    # --- 3.4. Thread de Processamento (Worker) ---

    def thread_processamento(caminho_ou: str, texto_bruto: str) -> None:
        """Executa o pipeline de migração em lote em thread separada.

        Realiza tokenização e sanitização dos hostnames, itera sobre cada
        ativo executando a movimentação via PowerShell, e persiste os
        resultados no log CSV ao final.

        Args:
            caminho_ou: Distinguished Name (DN) LDAP da OU de destino.
            texto_bruto: Texto bruto com hostnames inseridos pelo usuário.
        """
        global cancelar_processo

        tokens = re.split(r"[,\n;\s]+", texto_bruto)
        lista_maquinas = [limpar_hostname(t) for t in tokens if t.strip()]

        total = len(lista_maquinas)
        cont_sucesso = 0
        buffer_csv: list[str] = []

        page.run_task(ui_iniciar_tarefa, total)

        if total == 0:
            page.run_task(ui_adicionar_log, "⚠️ A lista está vazia.", "yellow")
            page.run_task(ui_finalizar_tarefa, 0, 0)
            return

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

        registrar_log(buffer_csv)
        page.run_task(ui_finalizar_tarefa, cont_sucesso, total)

    # --- 3.5. Handlers de Evento ---

    def ao_clicar_processar(e: ft.ControlEvent) -> None:
        """Valida os campos e inicia o processamento em thread dedicada."""
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

    def ao_clicar_cancelar(e: ft.ControlEvent) -> None:
        """Sinaliza a interrupção do processamento em lote."""
        global cancelar_processo
        cancelar_processo = True
        btn_cancelar.disabled = True
        page.update()

    # --- 3.6. Botões de Ação ---

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

    # --- 3.7. Montagem do Layout ---

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
