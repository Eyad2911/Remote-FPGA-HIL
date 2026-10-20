import threading
from tkinter import filedialog
from typing import Callable, Optional

import customtkinter as ctk


class BitstreamPanel(ctk.CTkFrame):
    def __init__(self, parent, on_file_selected, on_upload):
        super().__init__(parent, border_width=1)
        self.on_file_selected_callback = on_file_selected
        self.on_upload_callback = on_upload
        self.selected_file = ""
        self._after_id = None
        self._upload_thread: Optional[threading.Thread] = None
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Bitstream Upload", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, columnspan=4, padx=10, pady=(8, 4), sticky="w"
        )
        ctk.CTkLabel(self, text="Bitstream File:").grid(
            row=1, column=0, padx=(10, 4), pady=6, sticky="e"
        )
        self.file_path_entry = ctk.CTkEntry(self, state="readonly", width=340)
        self.file_path_entry.grid(row=1, column=1, padx=(0, 6), pady=6)

        self.browse_btn = ctk.CTkButton(self, text="Browse", width=80, command=self.on_browse)
        self.browse_btn.grid(row=1, column=2, padx=(0, 10), pady=6)

        self.upload_btn = ctk.CTkButton(
            self, text="Upload & Program FPGA", state="disabled", command=self.on_upload
        )
        self.upload_btn.grid(row=2, column=0, columnspan=3, padx=10, pady=(4, 4))

        self.progress_bar = ctk.CTkProgressBar(self, width=380)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=3, column=0, columnspan=3, padx=10, pady=(2, 4))

        self.bitstream_status_label = ctk.CTkLabel(self, text="")
        self.bitstream_status_label.grid(
            row=4, column=0, columnspan=3, padx=10, pady=(0, 8), sticky="w"
        )

    # ── Browse ─────────────────────────────────────────────────────────────────

    def on_browse(self):
        selected_path = filedialog.askopenfilename(
            title="Select Bitstream File",
            filetypes=[("Bitstream Files", "*.bit"), ("All Files", "*.*")],
        )
        if not selected_path:
            return
        self.selected_file = selected_path
        self.file_path_entry.configure(state="normal")
        self.file_path_entry.delete(0, "end")
        self.file_path_entry.insert(0, selected_path)
        self.file_path_entry.configure(state="readonly")
        self.set_status("", None)
        self.on_file_selected_callback(selected_path)

    # ── Upload trigger ─────────────────────────────────────────────────────────

    def on_upload(self):
        self.on_upload_callback(self.selected_file)

    # ── Real upload (thread-based) ─────────────────────────────────────────────

    def start_upload(
        self,
        upload_fn: Callable[[Callable[[int], None]], bool],
        on_complete: Callable[[bool], None],
    ) -> None:
        """
        Start a real upload in a background thread.

        Parameters
        ----------
        upload_fn : callable
            Called as ``upload_fn(progress_callback) -> bool`` in a worker thread.
            ``progress_callback(pct: int)`` may be called with values 0-100 to
            update the progress bar. The return value indicates success.
        on_complete : callable
            Called on the main thread as ``on_complete(success: bool)`` when the
            upload finishes or fails.
        """
        self.cancel_animation()
        self.upload_btn.configure(state="disabled")
        self.browse_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self.set_status("Uploading bitstream...", "white")

        def _progress_cb(pct: int) -> None:
            # Called from worker thread — post to the main thread via after()
            self.after(0, lambda: self.progress_bar.set(pct / 100))

        def _run() -> None:
            try:
                success = upload_fn(_progress_cb)
            except Exception:
                success = False
            self.after(0, lambda: _done(success))

        def _done(success: bool) -> None:
            self.browse_btn.configure(state="normal")
            on_complete(success)

        self._upload_thread = threading.Thread(target=_run, daemon=True)
        self._upload_thread.start()

    # ── State helpers ──────────────────────────────────────────────────────────

    def set_upload_enabled(self, enabled: bool):
        # Only re-enable when no upload is running
        if self._upload_thread and self._upload_thread.is_alive():
            return
        self.upload_btn.configure(state="normal" if enabled else "disabled")

    def has_selected_file(self) -> bool:
        return bool(self.selected_file)

    def set_status(self, message: str, color: Optional[str]):
        if color is None:
            self.bitstream_status_label.configure(text=message)
        else:
            self.bitstream_status_label.configure(text=message, text_color=color)

    def set_progress(self, pct: int) -> None:
        self.progress_bar.set(pct / 100)

    def reset_progress(self):
        self.progress_bar.set(0)

    def cancel_animation(self):
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
