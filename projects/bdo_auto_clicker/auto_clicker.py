import ctypes
import json
import threading
import time
from pathlib import Path

import cv2
import numpy as np
import pyautogui
from pynput import keyboard

from shared.logger import setup_logger

log = setup_logger("bdo_auto_clicker")


class BDOAutoClicker:
    def __init__(self, check_interval: float = 0.5):
        self.check_interval = check_interval
        self.is_running = False
        self.listener = None
        self.templates_dir = Path(__file__).parent / "templates"
        self.config_path = Path(__file__).parent / "config.json"
        self.config = self.load_runtime_config()
        self.load_templates()

        self.state = "idle"
        self.last_action_time = 0
        self.obtener_fast_checks = 8
        self.obtener_fast_interval = 0.03
        self.stop_event = threading.Event()
        self.obtener_thread = None

    def load_runtime_config(self) -> dict:
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

        if not self.config_path.exists():
            with self.config_path.open("w", encoding="utf-8") as config_file:
                json.dump(default_config, config_file, indent=4)
            log.info("Created default config at %s", self.config_path)
            return default_config

        try:
            with self.config_path.open("r", encoding="utf-8") as config_file:
                loaded_config = json.load(config_file)
            log.info("Loaded config from %s", self.config_path)
            return loaded_config
        except Exception as error:
            log.error("Failed to load config.json, using defaults: %s", error)
            return default_config

    def resolve_search_region(
        self,
        frame_height: int,
        frame_width: int,
        region_name: str,
        default_region: tuple,
    ) -> tuple:
        region_config = self.config.get("regions", {}).get(region_name)

        if not region_config:
            return default_region

        try:
            x = max(0, int(region_config["x"]))
            y = max(0, int(region_config["y"]))
            w = max(1, int(region_config["w"]))
            h = max(1, int(region_config["h"]))
            x2 = min(frame_width, x + w)
            y2 = min(frame_height, y + h)

            if x >= x2 or y >= y2:
                return default_region

            return (x, y, x2, y2)
        except Exception:
            return default_region

    def get_screen_regions(self, frame_height: int, frame_width: int) -> dict:
        # Divide verticalmente: izquierda 20%, centro 60%, derecha 20%
        left_width = int(frame_width * 0.2)
        center_width = int(frame_width * 0.6)
        center_start = left_width
        center_end = center_start + center_width
        third_height = frame_height // 3
        # Recolectar: centro completo
        # Obtener: derecha completa
        return {
            "left": (0, 0, center_start, frame_height),
            "center": (center_start, 0, center_end, frame_height),
            "center_top": (center_start, 0, center_end, third_height),
            "center_middle": (
                center_start,
                third_height,
                center_end,
                2 * third_height,
            ),
            "center_bottom": (
                center_start,
                2 * third_height,
                center_end,
                frame_height,
            ),
            "right": (center_end, 0, frame_width, frame_height),
        }

    def extract_region(self, frame: np.ndarray, region: tuple) -> np.ndarray:
        x1, y1, x2, y2 = region
        return frame[y1:y2, x1:x2]

    def load_templates(self) -> None:
        # Always load from project root
        recolector_path = Path(__file__).parent / "Recolectar.png"
        obtener_path = Path(__file__).parent / "Obtener.png"
        self.recolector_template = cv2.imread(str(recolector_path))
        self.obtener_template = cv2.imread(str(obtener_path))
        log.info("Loaded Recolectar.png from %s", recolector_path)
        log.info("Loaded Obtener.png from %s", obtener_path)
        log.debug("Templates loaded: recolector=OK, obtener=OK")

    def on_hotkey_toggle(self, key: keyboard.Key | None) -> None:
        if key == keyboard.Key.f6:
            self.is_running = not self.is_running
            status = "STARTED" if self.is_running else "PAUSED"
            log.info("%s - Press F6 to toggle", status)

    def on_hotkey_exit(self, key: keyboard.Key | None) -> None:
        if key == keyboard.Key.f7:
            log.info("Exiting...")
            return False

    def start_hotkey_listener(self) -> None:
        with keyboard.Listener(
            on_release=lambda key: (
                self.on_hotkey_toggle(key), self.on_hotkey_exit(key)
            )[1]
        ) as self.listener:
            self.listener.join()

    def detect_r_button_pattern(self) -> bool:
        screenshot = pyautogui.screenshot()
        frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        regions = self.get_screen_regions(frame.shape[0], frame.shape[1])
        center_region = self.resolve_search_region(
            frame.shape[0],
            frame.shape[1],
            "recolectar",
            regions["center"],
        )
        search_frame = self.extract_region(frame, center_region)

        result = cv2.matchTemplate(search_frame, self.recolector_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        threshold = float(self.config.get("thresholds", {}).get("recolectar", 0.65))
        log.debug(f"Recolectar match value: {max_val:.3f} (threshold: {threshold})")
        if max_val >= threshold:
            log.info("Recolectar pattern detected (match=%.3f) en posición %s", max_val, max_loc)
            log.debug(f"Recolectar: min_val={min_val:.3f}, max_val={max_val:.3f}, min_loc={min_loc}, max_loc={max_loc}")
            return True
        log.debug("Recolectar pattern not detected")
        return False

    def detect_inventory_list(self) -> bool:
        screenshot = pyautogui.screenshot()
        frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        regions = self.get_screen_regions(frame.shape[0], frame.shape[1])
        right_region = self.resolve_search_region(
            frame.shape[0],
            frame.shape[1],
            "obtener",
            regions["right"],
        )
        search_frame = self.extract_region(frame, right_region)

        result = cv2.matchTemplate(search_frame, self.obtener_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        threshold = float(self.config.get("thresholds", {}).get("obtener", 0.7))
        log.debug(f"Obtener match value: {max_val:.3f} (threshold: {threshold})")
        if max_val >= threshold:
            log.info("Obtener pattern detected (match=%.3f) en posición %s", max_val, max_loc)
            log.debug(f"Obtener: min_val={min_val:.3f}, max_val={max_val:.3f}, min_loc={min_loc}, max_loc={max_loc}")
            return True
        log.debug("Obtener pattern not detected")
        return False

    def detect_inventory_list_aggressive(self) -> bool:
        for attempt in range(self.obtener_fast_checks):
            if self.detect_inventory_list():
                log.info("Obtener detected in aggressive loop (attempt %s)", attempt + 1)
                return True
            if attempt < self.obtener_fast_checks - 1:
                time.sleep(self.obtener_fast_interval)
        return False

    def obtener_worker_loop(self) -> None:
        log.info("Obtener worker thread started")
        while not self.stop_event.is_set():
            if self.is_running and self.state == "waiting_obtener":
                if self.detect_inventory_list_aggressive():
                    log.info("Obtener detectado, ejecutando acción de obtención.")
                    self.press_r_key()
                    self.state = "idle"
                    log.info("State changed: idle")
            time.sleep(0.05)
        log.info("Obtener worker thread stopped")

    def press_r_key_keybd_event(self) -> bool:
        try:
            keybd_event = ctypes.windll.user32.keybd_event
            keybd_event(0x52, 0x13, 0, 0)
            time.sleep(0.08)
            keybd_event(0x52, 0x13, 0x0002, 0)
            return True
        except Exception:
            return False

    def press_r_key(self) -> None:
        log.info("Pressing R key (method=keybd_event)")
        if self.press_r_key_keybd_event():
            log.info("R key sent via keybd_event")
        else:
            log.warning("keybd_event failed")

        time.sleep(0.3)

    def run(self) -> None:
        log.info("Starting monitor... (detección activa)")
        log.info("Press F6 to pause/resume")
        log.info("Press F7 to exit")

        listener_thread = threading.Thread(
            target=self.start_hotkey_listener, daemon=True
        )
        listener_thread.start()

        self.obtener_thread = threading.Thread(
            target=self.obtener_worker_loop, daemon=True
        )
        self.obtener_thread.start()

        # Iniciar en modo detección
        self.is_running = True
        log.info("Modo detección: ON (presiona F6 para pausar)")

        try:
            while True:
                if self.is_running:
                    current_time = time.time()

                    log.debug(f"Current state: {self.state}")

                    if self.state == "idle":
                        log.debug("State: idle. Checking for Recolectar pattern...")
                        if self.detect_r_button_pattern():
                            log.info("Recolectar detectado, ejecutando acción de recolección.")
                            self.press_r_key()
                            self.state = "waiting_obtener"
                            self.last_action_time = current_time
                            log.info("State changed: waiting_obtener")
                    elif self.state == "waiting_obtener":
                        log.debug("State: waiting_obtener. Worker thread is scanning Obtener...")

                else:
                    log.debug("Paused. Waiting for F6 to resume...")

                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            log.info("Interrupted by user")
        finally:
            self.stop_event.set()
