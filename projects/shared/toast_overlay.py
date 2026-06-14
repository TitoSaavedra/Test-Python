import platform
from typing import Callable

import customtkinter as ctk

ctk.set_appearance_mode("light")


class PastelToast(ctk.CTkToplevel):
    TYPES = {
        "success": {"bg": "#E8F5E9", "accent": "#2E7D32", "text": "#1B4332"},
        "error": {"bg": "#FFEBEE", "accent": "#C62828", "text": "#7A1F1F"},
        "info": {"bg": "#E3F2FD", "accent": "#1565C0", "text": "#123A63"},
        "warning": {"bg": "#FFF3E0", "accent": "#EF6C00", "text": "#6E3B00"},
    }

    def __init__(
        self,
        message: str,
        toast_type: str = "info",
        duration: int = 2000,
        y_offset: int = 40,
        animation_interval_ms: int = 15,
        animation_step: float = 0.1,
        on_close: Callable[["PastelToast"], None] | None = None,
    ):
        super().__init__()
        self._on_close = on_close
        self._animation_interval_ms = animation_interval_ms
        self._animation_step = animation_step
        self._is_closing = False

        style = self.TYPES.get(toast_type, self.TYPES["info"])

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.0)

        if platform.system() == "Windows":
            self.attributes("-disabled", True)
            self.attributes("-toolwindow", True)

        self.configure(fg_color=style["bg"])

        self.container = ctk.CTkFrame(
            self,
            fg_color=style["bg"],
            corner_radius=0,
            border_width=0,
        )
        self.container.pack(fill="both", expand=True)

        self.message_label = ctk.CTkLabel(
            self.container,
            text=message,
            text_color=style["text"],
            font=("Segoe UI Semibold", 17),
            padx=24,
            pady=16,
        )
        self.message_label.pack()

        self.update_idletasks()
        self._width = self.container.winfo_reqwidth()
        self._height = self.container.winfo_reqheight()
        self._x = (self.winfo_screenwidth() // 2) - (self._width // 2)

        self.reposition(y_offset)

        self.fade_in()
        self.after(duration, self.fade_out)

    def reposition(self, y_offset: int) -> None:
        self.geometry(f"{self._width}x{self._height}+{self._x}+{y_offset}")

    def fade_in(self) -> None:
        alpha = self.attributes("-alpha")
        if alpha < 1.0:
            self.attributes("-alpha", alpha + self._animation_step)
            self.after(self._animation_interval_ms, self.fade_in)

    def fade_out(self, callback=None) -> None:
        if self._is_closing:
            return

        self._is_closing = True

        def step() -> None:
            alpha = self.attributes("-alpha")
            if alpha > 0.0:
                self.attributes("-alpha", alpha - self._animation_step)
                self.after(self._animation_interval_ms, step)
            else:
                if callback:
                    callback()
                if self._on_close:
                    self._on_close(self)
                self.destroy()

        step()


class ToastNotifier:
    def __init__(
        self,
        max_visible: int = 1,
        stack_gap: int = 8,
        top_offset: int = 40,
        default_duration: int = 1400,
        animation_interval_ms: int = 15,
        animation_step: float = 0.1,
    ) -> None:
        self._max_visible = max_visible
        self._stack_gap = stack_gap
        self._top_offset = top_offset
        self._default_duration = default_duration
        self._animation_interval_ms = animation_interval_ms
        self._animation_step = animation_step
        self._active_notifications: list[PastelToast] = []

    def _on_toast_close(self, toast: PastelToast) -> None:
        self._active_notifications = [item for item in self._active_notifications if item != toast]
        self._reposition_stack()

    def _reposition_stack(self) -> None:
        current_y = self._top_offset
        for toast in self._active_notifications:
            if toast.winfo_exists():
                toast.reposition(current_y)
                current_y += toast.winfo_height() + self._stack_gap

    def notify(self, message: str, toast_type: str = "info", duration: int | None = None) -> None:
        toast = PastelToast(
            message=message,
            toast_type=toast_type,
            duration=duration if duration is not None else self._default_duration,
            y_offset=self._top_offset,
            animation_interval_ms=self._animation_interval_ms,
            animation_step=self._animation_step,
            on_close=self._on_toast_close,
        )
        self._active_notifications.append(toast)

        while len(self._active_notifications) > self._max_visible:
            oldest = self._active_notifications.pop(0)
            if oldest.winfo_exists():
                oldest.fade_out()

        self._reposition_stack()
