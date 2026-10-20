import threading

import customtkinter as ctk

from pc_gui.networking.client import NetworkClient
from pc_gui.panels.alsu_panel import ALSUPanel
from pc_gui.panels.bitstream_panel import BitstreamPanel
from pc_gui.panels.connection_panel import ConnectionPanel
from pc_gui.panels.result_panel import ResultPanel
from pc_gui.validation import validate_alsu_form, validate_ip, validate_port


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.connected = False
        self._client = None

        self.title("FPGA ALSU Controller")
        self.geometry("780x680")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.connection_panel = ConnectionPanel(self, self.handle_connect, self.handle_disconnect)
        self.connection_panel.pack(fill="x", padx=10, pady=(10, 5))

        self.bitstream_panel = BitstreamPanel(self, self.handle_file_selected, self.handle_upload)
        self.bitstream_panel.pack(fill="x", padx=10, pady=5)

        self.alsu_panel = ALSUPanel(self, self.handle_send, self.handle_operation_changed)
        self.alsu_panel.pack(fill="x", padx=10, pady=5)

        self.result_panel = ResultPanel(self)
        self.result_panel.pack(fill="x", padx=10, pady=(5, 10))

        self._client = NetworkClient(
            result_callback=lambda result: None,
            log_callback=self.result_panel.add_log,
            connection_lost_callback=lambda: self.after(0, self._on_connection_lost),
        )
        self._sync_controls()

    # ── Connection ──────────────────────────────────────────────────────────────

    def handle_connect(self, ip, port):
        is_valid_ip, ip_error = validate_ip(ip)
        if not is_valid_ip:
            self.connection_panel.set_connected(False, ip_error, is_error=True)
            return

        is_valid_port, port_error = validate_port(port)
        if not is_valid_port:
            self.connection_panel.set_connected(False, port_error, is_error=True)
            return

        self.result_panel.add_log(f"Connecting to {ip.strip()}:{port.strip()} ...")
        ok = self._client.connect(ip.strip(), int(port.strip()))

        if ok:
            self.connected = True
            self.connection_panel.set_connected(True, "Connected")
        else:
            self.connection_panel.set_connected(False, "Connection failed", is_error=True)

        self._sync_controls()

    def handle_disconnect(self):
        if self._client is not None:
            self._client.disconnect()
        self.connected = False
        self.connection_panel.set_connected(False, "Disconnected")
        self.bitstream_panel.cancel_animation()
        self.bitstream_panel.reset_progress()
        self.bitstream_panel.set_status("", None)
        self._sync_controls()
        self.result_panel.add_log("Disconnected")

    # ── ALSU ────────────────────────────────────────────────────────────────────

    def handle_operation_changed(self, _operation):
        self._sync_controls()

    def handle_send(self, operation, a_str, b_str):
        is_valid, errors = validate_alsu_form(operation, a_str, b_str)
        if not is_valid:
            self.alsu_panel.show_error(errors[0])
            return

        self.alsu_panel.clear_error()
        a_value = int(a_str.strip())
        b_value = 0 if operation == "BYPASS" else int(b_str.strip())

        result = self._client.send_alsu_request(operation, a_value, b_value)
        if result is None:
            return

        self.result_panel.update_result(result)
        self.result_panel.add_log(f"{operation} A={a_value} B={b_value} -> {result}")

    # ── Bitstream upload ────────────────────────────────────────────────────────

    def handle_file_selected(self, selected_file):
        self.result_panel.add_log(f"Selected bitstream file: {selected_file}")
        self._sync_controls()

    def handle_upload(self, selected_file):
        if not self.connected or not selected_file:
            return

        def upload_fn(progress_cb):
            return self._client.send_bitstream(selected_file, progress_cb)

        self.result_panel.add_log(f"Uploading: {selected_file}")
        self.bitstream_panel.start_upload(upload_fn, self._finish_upload_result)

    def _finish_upload_result(self, success: bool):
        if success:
            self.bitstream_panel.set_status("FPGA programmed successfully", "green")
            self.result_panel.add_log("Upload complete — FPGA programmed successfully")
        else:
            self.bitstream_panel.set_status("Upload failed", "red")
            self.result_panel.add_log("Upload failed — check connection and server log")
        self._sync_controls()

    def _on_connection_lost(self):
        if not self.connected:
            return
        self.connected = False
        self.connection_panel.set_connected(False, "Connection lost — reconnect to continue")
        self.bitstream_panel.set_status("", None)
        self._sync_controls()
        self.result_panel.add_log("Connection to Pi server lost.")

    # ── Internal helpers ────────────────────────────────────────────────────────

    def _sync_controls(self):
        self.alsu_panel.set_send_enabled(self.connected)
        self.bitstream_panel.set_upload_enabled(
            self.connected and self.bitstream_panel.has_selected_file()
        )

    def on_close(self):
        self.bitstream_panel.cancel_animation()
        if self._client is not None:
            self._client.disconnect()
        self.destroy()
