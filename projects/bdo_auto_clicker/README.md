# BDO Auto Clicker

Auto-clicker for Black Desert Online that detects screen patterns and automatically presses the R key.

## Features

- Screen divided into 3 vertical regions for targeted detection
- Template matching for "Recolectar.png" button detection (searched in center-bottom area)
- Template matching for "Obtener.png" button detection (searched in right region)
- State-based automation workflow:
  - **Collect**: Detects and presses R on Recolectar button
  - **Obtain**: Waits 1 second, then detects and presses R on Obtener button
  - **Timeout**: If Obtener not found within 2 seconds, returns to Collect
- Hotkeys for control:
  - **F6**: Pause/Resume
  - **F7**: Exit

## Installation

1. Dependencies are already in `requirements.txt`
2. Ensure the venv is activated
3. Add template images to `templates/` folder:
   - `Recolectar.png` - Screenshot of the circle/button when collecting with tools
   - `Obtener.png` - Screenshot of the "Obtener" button in inventory list

## Usage

```powershell
python projects\bdo_auto_clicker\main.py
```

The program follows this workflow:
1. **Idle state**: Waits for Recolectar pattern in center-bottom region
2. **Collect**: When Recolectar is detected, presses R and enters collecting state
3. **Wait**: Waits 1 second for the Obtener button to appear
4. **Obtain**: When Obtener is detected in right region, presses R
5. **Timeout**: If Obtener is not found within 2 seconds of collecting, returns to idle and tries again
6. **Repeat**: After obtaining, returns to idle state for next cycle

Control:
- Press F6 to pause/resume the auto-clicker
- Press F7 to exit

## Configuration

Edit `config.py` to adjust:
- `CHECK_INTERVAL`: Check frequency (seconds) - default 0.5
- `TEMPLATE_MATCH_THRESHOLD`: Confidence threshold for template matching (0.0-1.0) - default 0.7
- Hotkeys: `KEY_TOGGLE`, `KEY_EXIT`

State machine timing (in `auto_clicker.py`):
- `collect_wait_time`: Time to wait before searching for Obtener (default 1.0 second)
- `obtain_timeout`: Maximum time to wait for Obtener before restarting cycle (default 2.0 seconds)

## Screen Regions

The screen is divided as follows:
- **Left third**: 0% - 33% width
- **Center (bottom half)**: 33% - 66% width, from 50% height downwards
- **Right third**: 66% - 100% width

## Template Images

Place PNG screenshots in the `templates/` directory:
- `Recolectar.png` - The circle/button that appears when using collection tools (appears in center-bottom)
- `Obtener.png` - The "Obtener" button from the inventory list (appears on right side)

Make sure the images are clear and consistent with the BDO UI.

## Requirements

- Python 3.10+
- Windows (for pynput keyboard listener)
- BDO running in foreground or windowed mode
- Template images in `templates/` directory

## Logging

All logs are stored in two locations:
- **Repository root**: `logs/bdo_auto_clicker.log`
- **Project folder**: `projects/bdo_auto_clicker/logs/bdo_auto_clicker.log`
- Log level: DEBUG (files), INFO (console)
- Rotating logs: 10MB max size, 5 backup files
- Format: `timestamp | logger_name | level | message`

## Logger Module

The project uses the centralized logging module located at `projects/shared.py`:
```python
import sys
from pathlib import Path
from shared import setup_logger

sys.path.insert(0, str(Path(__file__).parent.parent))
log = setup_logger("bdo_auto_clicker")
```
