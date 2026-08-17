import customtkinter as ctk
from ui.views_builder import BuilderView
from ui.views_catalog import CatalogView

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class StickerStudioApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Sticker Studio Manager")
        self.geometry("980x620")
        self.minsize(850, 520)

        # Layout Configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Navigation Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="✨ Sticker Studio", font=ctk.CTkFont(size=18, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 20))

        self.btn_builder = ctk.CTkButton(self.sidebar_frame, text="Sheet Builder", command=self.show_builder_view)
        self.btn_builder.grid(row=1, column=0, padx=20, pady=10)

        self.btn_catalog = ctk.CTkButton(self.sidebar_frame, text="Listings & Exports", command=self.show_catalog_view)
        self.btn_catalog.grid(row=2, column=0, padx=20, pady=10)

        # Appearance Mode Selector
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Dark", "Light", "System"], command=self.change_appearance_mode)
        self.appearance_mode_menu.grid(row=6, column=0, padx=20, pady=(10, 20))

        # Main View Container
        self.builder_view = BuilderView(self, log_callback=None)
        self.catalog_view = CatalogView(self)

        # Default View
        self.show_builder_view()

    def show_builder_view(self):
        self.catalog_view.grid_forget()
        self.builder_view.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.btn_builder.configure(fg_color=["#3B8ED0", "#1F6AA5"])
        self.btn_catalog.configure(fg_color="transparent")

    def show_catalog_view(self):
        self.builder_view.grid_forget()
        self.catalog_view.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.btn_catalog.configure(fg_color=["#3B8ED0", "#1F6AA5"])
        self.btn_builder.configure(fg_color="transparent")

    def change_appearance_mode(self, new_mode: str):
        ctk.set_appearance_mode(new_mode)