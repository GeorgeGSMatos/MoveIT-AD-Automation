# 🚀 MoveIT - AD Automation Tool

![Python]
![Flet]
![PowerShell]
![Platform]
![Status]

> **Enterprise tool for mass migration and organization of Active Directory assets.**

**MoveIT** is a Desktop solution designed to streamline IT and Service Desk workflows. It provides a modern graphical interface to execute complex AD object movements, ensuring security, data validation, and audit logging.

---

## ✨ Key Features

* **Modern GUI:** Built with **Flet** (Python), featuring a native Dark Mode interface.
* **Batch Processing:** Move hundreds of computers simultaneously by simply pasting a list of hostnames.
* **Backend Security:** Utilizes native PowerShell commands (`Move-ADObject`) with pre-execution validation (`Get-ADComputer`).
* **Non-Blocking Execution:** Processing runs on separate **Threads**, keeping the interface responsive at all times.
* **Audit Logs:** Automatically generates a `.csv` log file with the status (Success/Error) and timestamp for every operation.
* **Data Sanitization:** Automatic cleanup of extra spaces and invalid characters in hostnames.

---

## ⚙️ Prerequisites

To run the software (either source code or executable), the environment must meet the following requirements:

1.  **Operating System:** Windows 10/11 or Windows Server.
2.  **Permissions:** The logged-in user must have **write permissions** on the target Active Directory OUs.
3.  **RSAT Installed:** Remote Server Administration Tools (Active Directory PowerShell Module) must be enabled.

---

## 🚀 Configuration

The system uses a JSON file to map available destinations (OUs).

1.  In the root folder, create or edit the `config.json` file.
2.  Follow the format below (Key = Display Name, Value = LDAP Path):

```json
{
    "Computers - Finance": "OU=Finance,OU=Computers,DC=company,DC=com",
    "Computers - HR": "OU=HR,OU=Computers,DC=company,DC=com",
    "IT Lab": "OU=Lab,OU=IT,DC=company,DC=com",
    "Decommissioned": "OU=Disabled Users,DC=company,DC=com"
}