# 🚀 MoveIT - AD Automation Tool

Ferramenta de automação desenvolvida para agilizar a movimentação de ativos (computadores) entre Unidades Organizacionais (OUs) no Active Directory.

Desenvolvido para uso interno no setor de TI, substituindo processos manuais repetitivos por uma interface gráfica ágil e amigável.*

## 🛠️ Tecnologias Utilizadas

* **Python 3.10+**
* **Flet** (Interface Gráfica Flutter para Python)
* **PowerShell** (Integração com Active Directory via `Move-ADObject`)
* **Threading** (Processamento assíncrono para não travar a UI)
* **PyInstaller** (Compilação para executável standalone)

## ✨ Funcionalidades

* **Paste & Go:** Entrada de dados flexível (aceita listas do Excel, CSV ou texto bruto).
* **Sanitização Automática:** Limpeza de caracteres inválidos nos hostnames.
* **Interface Responsiva:** Barra de progresso e logs em tempo real sem travamentos.
* **Log de Auditoria:** Geração automática de histórico (`historico_log.csv`).
* **Configurável:** Destinos (OUs) mapeados via arquivo JSON externo.

## ⚠️ Requisitos

* Para a movimentação funcionar, a máquina deve ter o **RSAT (Active Directory module for Windows PowerShell)** instalado.
* O usuário deve ter permissões administrativas no AD.

---
*Desenvolvido por George GS Matos*