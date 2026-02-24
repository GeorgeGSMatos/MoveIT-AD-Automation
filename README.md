# 🚀 MoveIT - AD Automation Tool

![Python](https://img.shields.io/badge/python-3.12+-blue.svg?style=flat&logo=python&logoColor=white)
![Flet](https://img.shields.io/badge/frontend-Flet-purple.svg?style=flat&logo=flet&logoColor=white)
![PowerShell](https://img.shields.io/badge/backend-PowerShell-5391FE.svg?style=flat&logo=powershell&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg?style=flat&logo=windows&logoColor=white)
![Status](https://img.shields.io/badge/status-Stable-green.svg?style=flat)

> **Enterprise tool for mass migration and organization of Active Directory assets.**

---

## 📖 The Story Behind MoveIT

Picture this: It's Friday afternoon, and a ticket drops requesting the migration of 50 workstations to a new department's Organizational Unit (OU). 

The traditional way? Open *Active Directory Users and Computers (ADUC)*, search for each hostname, right-click, select "Move", carefully navigate a massive LDAP tree so you don't drop it in the wrong folder... and repeat this 50 times. 

It was tedious, highly susceptible to human error (the dreaded "accidental drag-and-drop"), and left absolutely zero audit trail. 

**MoveIT was born out of this exact frustration.** I realized that IT Support and Service Desk teams were spending hours on a task that a machine could do in seconds. We needed a bridge between the raw power of PowerShell and a friendly, mistake-proof user interface. MoveIT transforms a 30-minute risky chore into a 30-second safe, audited, and automated process.

---

## 💡 The Problems We Solved

* **The Manual Toil:** Replaced individual searches and clicks with **Batch Processing**. Paste a list of 100 hostnames, and MoveIT handles the rest.
* **The "Oops" Factor:** Navigating complex LDAP paths is error-prone. We abstracted this into a simple, friendly **Dropdown Menu** mapped via a JSON file.
* **The Phantom Moves:** Moving objects in ADUC doesn't generate an easy-to-read report. MoveIT generates an **automatic CSV Audit Log** with timestamps and success/error status for every single asset.
* **The Unresponsive Scripts:** Standard scripts freeze the screen while running. MoveIT uses **Asynchronous Threading**, keeping the UI responsive and providing real-time visual feedback.

---

## 📸 Preview

<img width="854" height="731" alt="image" src="https://github.com/user-attachments/assets/101d064c-ada7-4ad2-9db9-87f5f83c4087" />

---

## ✨ Key Features

* **Modern GUI:** Built with **Flet** (Python), featuring a native Dark Mode interface.
* **Backend Security:** Utilizes native PowerShell commands (`Move-ADObject`) with pre-execution validation (`Get-ADComputer`). If the machine doesn't exist, it won't attempt to move it.
* **Data Sanitization:** Automatic cleanup of extra spaces and invalid characters in hostnames before processing.
* **Zero Credential Storage:** Leverages Windows Integrated Authentication (SSO). It uses the logged-in user's permissions, ensuring 100% compliance with existing AD security policies.

---

## ⚙️ Prerequisites

To run the software (either source code or executable), your environment must meet the following requirements:

1.  **Operating System:** Windows 10/11 or Windows Server.
2.  **Permissions:** The logged-in user must have **write permissions** on the target Active Directory OUs.
3.  **RSAT Installed:** Remote Server Administration Tools (Active Directory PowerShell Module) must be enabled on the machine.

---

## 🚀 Configuration

The system uses a JSON file to map available destinations (OUs). This keeps hardcoded LDAP paths out of the source code.

1.  In the root folder, create or edit the `config.json` file.
2.  Follow the format below (Key = Display Name, Value = LDAP Path):

```json
{
    "Computers - Finance": "OU=Finance,OU=Computers,DC=company,DC=com",
    "Computers - HR": "OU=HR,OU=Computers,DC=company,DC=com",
    "IT Lab": "OU=Lab,OU=IT,DC=company,DC=com",
    "Decommissioned": "OU=Disabled Users,DC=company,DC=com"
}
