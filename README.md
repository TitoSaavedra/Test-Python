# Python Monorepo with Shared Root Dependencies

This repository uses one shared virtual environment at the root for all projects.

## Structure

- `projects/corsair_profiles_downloader/main.py`
- `requirements.txt` (shared dependencies)
- `setup_env.ps1` (root environment setup)

## 1) Create the root virtual environment

From the repository root (PowerShell):

```powershell
python -m venv .venv
```

## 2) Activate the environment

```powershell
.\.venv\Scripts\Activate.ps1
```

## 3) Install shared dependencies

```powershell
pip install -r requirements.txt
```

## 4) Quick setup script (optional)

```powershell
.\setup_env.ps1
```

## 5) Run a project from the repository root

```powershell
python projects\corsair_profiles_downloader\main.py
```

## 6) Run the web gallery (FastAPI + partial HTML views)

```powershell
uvicorn projects.corsair_profiles_downloader.web_app:app --reload --host 127.0.0.1 --port 8000
```

Then open:

```text
http://127.0.0.1:8000
```
