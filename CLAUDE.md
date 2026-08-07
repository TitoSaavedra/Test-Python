# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Role and Language

- Act as a reactive Python Software Engineer focused on implementing user requests precisely.
- All code, comments, documentation, and communication must be in English.
- For routine implementation tasks: output only code, no explanations or summaries.
- For non-obvious solutions or design choices: propose alternatives briefly with rationale, then wait for user confirmation ("OK") before proceeding. This is the only exception to the "code only" rule.
- Implement exactly what is requested, nothing more. If a request is ambiguous or incomplete, ask for clarification instead of guessing.

## Coding Restrictions

- No tests: do not execute, suggest, or mention tests.
- No refactoring unless specifically asked.
- No extra error handling beyond what was requested.
- No formatting changes unrelated to the task.
- Do not over-document: no docstrings/comments unless requested, or unless logic involves non-obvious algorithms, domain-specific decisions, or complex control flow.

## Repository Structure

This is a monorepo of independent, unrelated Python desktop/scripting utilities that share one root virtual environment and dependency file — there is no shared application logic between projects beyond the `projects/shared/` package.

```
requirements.txt        # single shared dependency file for ALL Python projects
setup_env.ps1            # creates .venv and installs requirements.txt
logs/                     # centralized log output (one file per project)
projects/
  shared/                 # cross-project Python utilities (logger, toast overlay)
  bdo_auto_clicker/       # OpenCV template-matching auto-clicker for a game
  corsair_profiles_downloader/  # scraper + FastAPI gallery for downloaded profiles
  notification_overlay_tester/  # standalone demo of the toast overlay
  tauri-front-ends/       # unrelated desktop apps: Tauri + React, one independent app per subfolder
```

Each Python project directory is self-contained (its own `main.py`, `README.md`, `run.ps1`) but there is **no per-project virtual environment or requirements file** — everything installs from the root `requirements.txt` into the root `.venv`. `projects/tauri-front-ends/` is a separate ecosystem (Node/Rust, not Python) with its own per-app dependencies — see below.

## Environment Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# or, equivalently:
.\setup_env.ps1
```

There are no test or lint commands configured in this repo.

## Running Projects

Always run from the repository root using relative paths (PowerShell execution format):

```powershell
python projects\bdo_auto_clicker\main.py
python projects\corsair_profiles_downloader\main.py
python projects\notification_overlay_tester\main.py

# FastAPI gallery for corsair_profiles_downloader
uvicorn projects.corsair_profiles_downloader.web_app:app --reload --host 127.0.0.1 --port 8000
```

Each project also has a `run.ps1` that activates the root venv and runs its `main.py` (some, like `bdo_auto_clicker/run.ps1`, require `#Requires -RunAsAdministrator` for hotkey/keyboard access). `corsair_profiles_downloader/web.ps1` launches the uvicorn gallery directly.

## Cross-Project Conventions

### sys.path pattern

Modules that need `projects/shared` insert the `projects/` directory into `sys.path` before importing it, since scripts are invoked directly (not as an installed package):

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.logger import setup_logger
```

`main.py` in each project is the entry point and typically does this `sys.path` insert; sibling modules in the same project directory (e.g. `auto_clicker.py` next to `bdo_auto_clicker/main.py`) can import `shared.*` directly because Python adds the invoked script's own directory to `sys.path[0]`.

### Centralized logging (`projects/shared/logger.py`)

All projects must use `setup_logger()` instead of `print()`:

```python
from shared.logger import setup_logger
log = setup_logger("project_name")   # use the project directory name
```

- Writes to **both** `{repo_root}/logs/{name}.log` and (unless disabled) the project's local `logs/` dir.
- Rotating file handler: 10MB max, 5 backups. File level DEBUG, console level INFO.
- Format: `timestamp | logger_name | level | message`.
- Replace all `print()` calls with `log.info()` / `log.warning()` / `log.error()` / `log.debug()`.

### Toast overlay (`projects/shared/toast_overlay.py`)

`ToastNotifier` (built on `customtkinter`) shows stacked, fading, click-through pastel toast notifications (`success`/`error`/`info`/`warning`) top-center on screen. `notification_overlay_tester` is a minimal standalone demo of this component; other projects can reuse `ToastNotifier` for UI feedback.

## Project Notes

### `bdo_auto_clicker`

OpenCV (`cv2.matchTemplate`) based state machine that watches the screen for two UI patterns (`Recolectar.png`, `Obtener.png`) and simulates the `R` key via `keybd_event`. Key pieces:

- `auto_clicker.py` — `BDOAutoClicker` class: screen-region detection, state machine (`idle` → `waiting_obtener` → `idle`), two background worker threads (`recolectar_worker_loop`, `obtener_worker_loop`) coordinated via a `state_lock` and `stop_event`, plus an `F6`/`F7` `pynput` hotkey listener for pause/resume/exit.
- `config.json` — runtime-tunable detection regions (`recolectar`/`obtener`/`espera`) and match thresholds; auto-created with defaults on first run if missing.
- `calibrator.py` — helper for calibrating screen regions/templates.
- Template images (`Recolectar.png`, `Obtener.png`, `Espera.png`) live at the project root and must match the current game UI.

### `corsair_profiles_downloader`

Two independent entry points sharing scraped data in `Corsair_Profiles_Collection/` (gitignored):

- `main.py` — scrapes `lewisgerschwitz.com/corsair.html` with `requests` + `BeautifulSoup` (session configured with retry/backoff via `urllib3.util.retry.Retry`), downloads profile archives/images, and writes a generated `README.md` per profile, organized by category and iCUE version.
- `web_app.py` — FastAPI app that reads the downloaded collection directly off disk (no database) and renders it via Jinja2 templates (`templates/`) and static assets (`static/`); serves the downloaded files themselves at `/profiles` via `StaticFiles`. Parses each profile's generated `README.md` (YouTube link, bullet list of included profiles) to build the `Profile` dataclass used by the templates.

### `notification_overlay_tester`

Minimal script demonstrating `shared.toast_overlay.ToastNotifier` with a hidden root `customtkinter` window (`app.withdraw()`) and scheduled `app.after(...)` calls firing different toast types.

### `tauri-front-ends`

Not part of the Python monorepo — each subfolder is a **fully independent Tauri desktop app** (own `package.json`, own `src-tauri` Rust crate, own React frontend). No shared Cargo workspace, no shared `node_modules`, no shared crate between apps; each app's `src-tauri` acts as that app's BFF via `#[tauri::command]` IPC handlers called from the frontend with `invoke()`.

- `icue/` — Material UI (MUI v6) gallery for the Corsair iCUE profiles, styled after a "Lumina Spectrum" design system (Inter font, cyan/magenta/lime accents on near-black glass surfaces — see `src/theme.ts`). Ships a standalone copy of the profile data instead of depending on `corsair_profiles_downloader` at runtime: `scripts/generate_data.py` (Python, run manually) copies `corsair_profiles_downloader/Corsair_Profiles_Collection/` into `icue/data/` and builds `data/profiles.json`, re-implementing the same README/image/zip parsing as `corsair_profiles_downloader/web_app.py`. The Rust backend (`src-tauri/src/main.rs`) loads that JSON on startup, rewrites relative asset paths to absolute ones, and exposes it via `get_profiles`/`get_filters`/`open_path` commands, plus `get_favorites`/`toggle_favorite` which persist a favorited-profile-ID set to `favorites.json` in the OS app data dir; the React side reads local images through `convertFileSrc`. The UI has no router — `App.tsx` holds a `view` state (`explore`/`favorites`/`settings`) rendered alongside a fixed `Sidebar`; `SettingsView` exposes a dark/light toggle and an accent-color picker that feed back into `buildTheme(mode, accent)`. See `icue/README.md` for the install/run steps (`generate_data.py` → `npm install` → `npm run tauri dev`).
