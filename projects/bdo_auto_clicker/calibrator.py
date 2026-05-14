import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pyautogui

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.logger import setup_logger

log = setup_logger("bdo_auto_clicker")

CONFIG_PATH = Path(__file__).parent / "config.json"


def load_or_create_config() -> dict:
    default_config = {
        "regions": {
            "recolectar": None,
            "obtener": None,
            "espera": None,
        },
        "thresholds": {
            "recolectar": 0.65,
            "obtener": 0.7,
            "espera": 0.3,
        },
    }

    if not CONFIG_PATH.exists():
        return default_config

    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
            return json.load(config_file)
    except Exception as error:
        log.warning("Invalid config.json, using defaults: %s", error)
        return default_config


def calibrate_obtener_region() -> None:
    log.info("Starting Obtener calibration")
    log.info("Open the game and show the Obtener area")
    log.info("Capturing screen now for ROI selection")

    screenshot = pyautogui.screenshot()
    frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    cv2.namedWindow("BDO Obtener Calibrator", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(
        "BDO Obtener Calibrator", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
    )

    roi = cv2.selectROI(
        "BDO Obtener Calibrator", frame, fromCenter=False, showCrosshair=True
    )
    cv2.destroyAllWindows()

    if roi[2] == 0 or roi[3] == 0:
        log.warning("Calibration cancelled or invalid region")
        return

    x, y, w, h = [int(value) for value in roi]

    config = load_or_create_config()
    config.setdefault("regions", {})["obtener"] = {
        "x": x,
        "y": y,
        "w": w,
        "h": h,
    }

    with CONFIG_PATH.open("w", encoding="utf-8") as config_file:
        json.dump(config, config_file, indent=4)

    log.info("Obtener region saved to %s", CONFIG_PATH)
    log.info("Saved region: x=%s y=%s w=%s h=%s", x, y, w, h)


if __name__ == "__main__":
    calibrate_obtener_region()