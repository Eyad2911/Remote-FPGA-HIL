from datetime import datetime

import customtkinter as ctk


class ResultPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, border_width=1)
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Result", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, columnspan=3, padx=10, pady=(8, 4), sticky="w"
        )

        self.result_dec = ctk.CTkLabel(self, text="-", font=ctk.CTkFont(size=20))
        self.result_dec.grid(row=1, column=0, padx=(20, 20), pady=4)

        self.result_hex = ctk.CTkLabel(self, text="-")
        self.result_hex.grid(row=1, column=1, padx=(0, 20), pady=4)

        self.result_bin = ctk.CTkLabel(self, text="-")
        self.result_bin.grid(row=1, column=2, padx=(0, 10), pady=4)

        self.log_box = ctk.CTkTextbox(self, height=160, state="disabled", font=("Courier New", 11))
        self.log_box.grid(row=2, column=0, columnspan=3, padx=10, pady=(4, 10), sticky="ew")
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)

    def update_result(self, value: int):
        bit_width = 8 if value <= 0xFF else 16
        self.result_dec.configure(text=str(value))
        self.result_hex.configure(text=f"Hex: 0x{value:04X}")
        self.result_bin.configure(text=f"Binary: 0b{value:0{bit_width}b}")

    def add_log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{timestamp}] {message}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
