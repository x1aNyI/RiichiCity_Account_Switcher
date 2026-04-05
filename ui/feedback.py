from __future__ import annotations

import tkinter as tk
from tkinter import messagebox


class FeedbackManager:
    def __init__(self, root: tk.Tk, *, success_duration_ms: int = 3000) -> None:
        self.root = root
        self.success_duration_ms = success_duration_ms
        self._toast_window: tk.Toplevel | None = None
        self._toast_after_id: str | None = None
        self._toast_parent: tk.Misc | None = None

    def show_success(self, message: str, *, parent: tk.Misc | None = None, duration_ms: int | None = None) -> None:
        host = self._resolve_parent(parent)
        if host is None:
            return

        self._destroy_toast()

        toast = tk.Toplevel(host)
        toast.withdraw()
        toast.overrideredirect(True)
        toast.transient(host)
        toast.configure(bg="#2f855a")
        toast.attributes("-topmost", True)

        label = tk.Label(
            toast,
            text=message,
            justify="left",
            anchor="w",
            bg="#2f855a",
            fg="white",
            padx=14,
            pady=10,
            font=("Microsoft YaHei UI", 10),
        )
        label.pack()

        self._toast_window = toast
        self._toast_parent = host

        host.bind("<Configure>", self._on_parent_configure, add="+")
        host.bind("<Destroy>", self._on_parent_destroy, add="+")

        toast.update_idletasks()
        self._position_toast(host)
        toast.deiconify()

        duration = duration_ms or self.success_duration_ms
        self._toast_after_id = toast.after(duration, self._destroy_toast)

    def show_warning(self, title: str, message: str, *, parent: tk.Misc | None = None) -> None:
        host = self._resolve_parent(parent)
        messagebox.showwarning(title, message, parent=host)

    def show_error(self, title: str, message: str, *, parent: tk.Misc | None = None) -> None:
        host = self._resolve_parent(parent)
        messagebox.showerror(title, message, parent=host)

    def ask_confirm(self, title: str, message: str, *, parent: tk.Misc | None = None) -> bool:
        host = self._resolve_parent(parent)
        return bool(messagebox.askyesno(title, message, parent=host))

    def _resolve_parent(self, parent: tk.Misc | None) -> tk.Misc | None:
        if parent is not None and bool(parent.winfo_exists()):
            return parent
        if bool(self.root.winfo_exists()):
            return self.root
        return None

    def _position_toast(self, parent: tk.Misc) -> None:
        if self._toast_window is None or not bool(self._toast_window.winfo_exists()):
            return

        parent.update_idletasks()
        self._toast_window.update_idletasks()

        x = parent.winfo_rootx() + parent.winfo_width() - self._toast_window.winfo_width() - 20
        y = parent.winfo_rooty() + 20
        self._toast_window.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _on_parent_configure(self, event: tk.Event) -> None:
        if self._toast_parent is None or event.widget != self._toast_parent:
            return
        self._position_toast(self._toast_parent)

    def _on_parent_destroy(self, event: tk.Event) -> None:
        if self._toast_parent is None or event.widget != self._toast_parent:
            return
        self._destroy_toast()

    def _destroy_toast(self) -> None:
        if self._toast_window is not None and bool(self._toast_window.winfo_exists()):
            if self._toast_after_id is not None:
                try:
                    self._toast_window.after_cancel(self._toast_after_id)
                except tk.TclError:
                    pass
            self._toast_window.destroy()

        self._toast_window = None
        self._toast_after_id = None
        self._toast_parent = None


def show_error(title: str, message: str) -> None:
    root = tk.Tk()
    root.withdraw()
    try:
        messagebox.showerror(title, message, parent=root)
    finally:
        root.destroy()
