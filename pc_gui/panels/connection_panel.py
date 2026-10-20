import customtkinter as ctk


class ConnectionPanel(ctk.CTkFrame):
    def __init__(self, parent, on_connect, on_disconnect):
        super().__init__(parent, border_width=1)
        self.on_connect_callback = on_connect
        self.on_disconnect_callback = on_disconnect
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Connection", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, columnspan=6, padx=10, pady=(8, 4), sticky="w"
        )

        ctk.CTkLabel(self, text="IP Address:").grid(row=1, column=0, padx=(10, 4), pady=8, sticky="e")
        self.ip_entry = ctk.CTkEntry(self, placeholder_text="192.168.1.100", width=180)
        self.ip_entry.insert(0, "192.168.1.100")
        self.ip_entry.grid(row=1, column=1, padx=(0, 10), pady=8)

        ctk.CTkLabel(self, text="Port:").grid(row=1, column=2, padx=(0, 4), pady=8, sticky="e")
        self.port_entry = ctk.CTkEntry(self, placeholder_text="5000", width=70)
        self.port_entry.insert(0, "5000")
        self.port_entry.grid(row=1, column=3, padx=(0, 10), pady=8)

        self.connect_btn = ctk.CTkButton(self, text="Connect", width=100, command=self.on_connect)
        self.connect_btn.grid(row=1, column=4, padx=(0, 6), pady=8)

        self.disconnect_btn = ctk.CTkButton(
            self, text="Disconnect", width=100, state="disabled", command=self.on_disconnect
        )
        self.disconnect_btn.grid(row=1, column=5, padx=(0, 10), pady=8)

        self.status_label = ctk.CTkLabel(self, text="● Disconnected", text_color="red")
        self.status_label.grid(row=2, column=0, columnspan=6, padx=10, pady=(0, 8), sticky="w")

    def on_connect(self):
        self.on_connect_callback(self.ip_entry.get(), self.port_entry.get())

    def on_disconnect(self):
        self.on_disconnect_callback()

    def set_connected(self, connected: bool, message: str | None = None, is_error: bool = False):
        if is_error:
            self.status_label.configure(text=message or "Connection failed", text_color="red")
            return

        if connected:
            self.status_label.configure(text=message or "● Connected", text_color="green")
            self.connect_btn.configure(state="disabled")
            self.disconnect_btn.configure(state="normal")
        else:
            self.status_label.configure(text=message or "● Disconnected", text_color="red")
            self.connect_btn.configure(state="normal")
            self.disconnect_btn.configure(state="disabled")
