# Studio-AI — Environment & Installation Guide

This document describes how to set up and run Studio-AI on Windows or Linux development machines.

## 1. Environment Requirements

- **Python:** 3.10, 3.11, or 3.12 (Python 3.12 recommended)
- **Database:** SQLite3 (uses Python's built-in `sqlite3` module with WAL mode)
- **GUI Framework:** PySide6 (Qt 6 bindings for Python)

---

## 2. Windows Installation (PowerShell)

```powershell
# 1. Create Virtual Environment
py -3.12 -m venv .venv

# 2. Activate Virtual Environment
.\.venv\Scripts\Activate.ps1

# 3. Upgrade Pip & Install Dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3. Linux Installation (Bash)

```bash
# 1. Create Virtual Environment
python3 -m venv .venv

# 2. Activate Virtual Environment
source .venv/bin/activate

# 3. Upgrade Pip & Install Dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Running the Application

### 4.1 Launch Desktop Application
```bash
python -m src.main
```

### 4.2 Run System Doctor Diagnostics
```bash
python -m src.main --doctor
```

---

## 5. Running Automated Tests

```bash
# 1. Check Python compilation across all source and test modules
python -m compileall -q src tests

# 2. Run test suite
python -m pytest -v
```

---

## 6. Default Workspace & Database Paths

- **Default Workspace Directory:** `~/.studio-ai/`
- **SQLite Database Path:** `~/.studio-ai/studio_ai.db`
- **Application Logs:** `~/.studio-ai/logs/app.log`
- **Project Workspaces:** `~/.studio-ai/projects/<project_id>/`
