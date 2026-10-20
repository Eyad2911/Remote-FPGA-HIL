import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import customtkinter as ctk
from pc_gui.app import App

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
