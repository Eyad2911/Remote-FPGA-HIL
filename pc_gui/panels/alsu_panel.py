import customtkinter as ctk


class ALSUPanel(ctk.CTkFrame):
    def __init__(self, parent, on_send, on_operation_change):
        super().__init__(parent, border_width=1)
        self.on_send_callback = on_send
        self.on_operation_change_callback = on_operation_change
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="ALSU Operation", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, columnspan=6, padx=10, pady=(8, 4), sticky="w"
        )

        ctk.CTkLabel(self, text="Operation:").grid(row=1, column=0, padx=(10, 4), pady=8, sticky="e")
        self.operation_menu = ctk.CTkOptionMenu(
            self,
            values=["ADD", "SUB", "MUL", "SHIFT", "BYPASS", "XOR"],
            command=self.on_operation_change,
            width=120,
        )
        self.operation_menu.set("ADD")
        self.operation_menu.grid(row=1, column=1, padx=(0, 14), pady=8)

        ctk.CTkLabel(self, text="Input A (0-255):").grid(row=1, column=2, padx=(0, 4), pady=8, sticky="e")
        self.input_a_entry = ctk.CTkEntry(self, width=80)
        self.input_a_entry.insert(0, "0")
        self.input_a_entry.grid(row=1, column=3, padx=(0, 14), pady=8)

        self.input_b_label = ctk.CTkLabel(self, text="Input B (0-255):")
        self.input_b_label.grid(row=1, column=4, padx=(0, 4), pady=8, sticky="e")
        self.input_b_entry = ctk.CTkEntry(self, width=80)
        self.input_b_entry.insert(0, "0")
        self.input_b_entry.grid(row=1, column=5, padx=(0, 10), pady=8)

        self.send_btn = ctk.CTkButton(self, text="Send", width=100, state="disabled", command=self.on_send)
        self.send_btn.grid(row=2, column=0, columnspan=6, padx=10, pady=(2, 8))

        self.error_label = ctk.CTkLabel(self, text="", text_color="red")
        self.error_label.grid(row=3, column=0, columnspan=6, padx=10, pady=(0, 8))

        self._apply_operation_state("ADD")

    def on_operation_change(self, op: str):
        self._apply_operation_state(op)
        self.on_operation_change_callback(op)

    def on_send(self):
        self.on_send_callback(
            self.operation_menu.get(),
            self.input_a_entry.get(),
            self.input_b_entry.get(),
        )

    def _apply_operation_state(self, op: str):
        self.clear_error()
        if op == "BYPASS":
            self.input_b_label.configure(text="Input B (disabled):")
            self.input_b_entry.configure(state="normal")
            self.input_b_entry.delete(0, "end")
            self.input_b_entry.insert(0, "0")
            self.input_b_entry.configure(state="disabled")
            return

        self.input_b_entry.configure(state="normal")
        if op == "SHIFT":
            self.input_b_label.configure(text="Shift Amount (0-7):")
        else:
            self.input_b_label.configure(text="Input B (0-255):")

    def set_send_enabled(self, enabled: bool):
        self.send_btn.configure(state="normal" if enabled else "disabled")
        if not enabled:
            self.clear_error()

    def show_error(self, message: str):
        self.error_label.configure(text=message)

    def clear_error(self):
        self.error_label.configure(text="")
