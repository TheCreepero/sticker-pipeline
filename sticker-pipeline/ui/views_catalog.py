import os
import subprocess
import webbrowser
import pathlib
import customtkinter as ctk


class CatalogView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        title = ctk.CTkLabel(self, text="Exports & Listings Hub", font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=20, padx=20, anchor="w")

        info_label = ctk.CTkLabel(
            self,
            text="Access your generated sticker sheets, Pinterest mockups, and the one-click copy dashboard below:",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        info_label.pack(padx=20, anchor="w", pady=(0, 20))

        btn_container = ctk.CTkFrame(self)
        btn_container.pack(fill="x", padx=20, pady=10)

        # Action Buttons
        dash_btn = ctk.CTkButton(
            btn_container,
            text="🌐 Open HTML Dashboard in Browser",
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#0052cc",
            hover_color="#0747a6",
            command=self.open_html_dashboard
        )
        dash_btn.pack(fill="x", padx=15, pady=10)

        sheets_btn = ctk.CTkButton(
            btn_container,
            text="📁 Open Single Sticker Sheets Folder",
            height=36,
            command=lambda: self.open_folder("exports/sheets")
        )
        sheets_btn.pack(fill="x", padx=15, pady=6)

        mixed_sheets_btn = ctk.CTkButton(
            btn_container,
            text="📁 Open Mixed Sticker Sheets Folder",
            height=36,
            command=lambda: self.open_folder("exports/mixed_sheets")
        )
        mixed_sheets_btn.pack(fill="x", padx=15, pady=6)

        pins_simple_btn = ctk.CTkButton(
            btn_container,
            text="📁 Open Dot-Grid Pins Folder",
            height=36,
            command=lambda: self.open_folder("exports/pins_simple")
        )
        pins_simple_btn.pack(fill="x", padx=15, pady=6)

        pins_adv_btn = ctk.CTkButton(
            btn_container,
            text="📁 Open Advanced Mockups Folder",
            height=36,
            command=lambda: self.open_folder("exports/pins_advanced")
        )
        pins_adv_btn.pack(fill="x", padx=15, pady=6)

    def open_html_dashboard(self):
        path = os.path.abspath("exports/listings.html")
        if os.path.exists(path):
            # Formats the Windows path into a strict file:/// URI
            file_uri = pathlib.Path(path).as_uri()
            webbrowser.open(file_uri)

    def open_folder(self, folder_path):
        abs_path = os.path.abspath(folder_path)
        os.makedirs(abs_path, exist_ok=True)
        if os.name == "nt":
            os.startfile(abs_path)
        else:
            subprocess.run(["open" if os.uname().sysname == "Darwin" else "xdg-open", abs_path])