import sys
from pathlib import Path

import customtkinter as ctk

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.toast_overlay import ToastNotifier


if __name__ == "__main__":
    app = ctk.CTk()
    app.withdraw()

    notifier = ToastNotifier()

    app.after(500, lambda: notifier.notify("Tarea completada", "success"))
    app.after(2000, lambda: notifier.notify("Ocurrió un error", "error"))
    app.after(3500, lambda: notifier.notify("Actualización disponible", "info"))
    app.after(5000, lambda: notifier.notify("Espacio de almacenamiento bajo", "warning"))
    app.after(6500, lambda: notifier.notify("Actualizando el sistema...", "info"))

    app.mainloop()