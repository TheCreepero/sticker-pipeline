import threading
import customtkinter as ctk
from main import run_pipeline
from src.metadata import load_seo_profiles


class BuilderView(ctk.CTkFrame):
    def __init__(self, master, log_callback):
        super().__init__(master)
        self.log = log_callback

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.setup_controls()

    def setup_controls(self):
        params_frame = ctk.CTkFrame(self)
        params_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        title_label = ctk.CTkLabel(params_frame, text="Sheet Generation Controls", font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(pady=(15, 5), padx=15, anchor="w")

        # 1. SEO Profile Dropdown
        seo_frame = ctk.CTkFrame(params_frame, fg_color="transparent")
        seo_frame.pack(fill="x", padx=15, pady=(5, 10))

        ctk.CTkLabel(seo_frame, text="SEO Profile:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        
        profiles = load_seo_profiles()
        profile_options = list(profiles.keys()) if profiles else ["Minimalist Bujo"]
        self.profile_dropdown = ctk.CTkOptionMenu(seo_frame, values=profile_options)
        self.profile_dropdown.pack(fill="x")
        self.profile_dropdown.set(profile_options[0])

        # 2. Toggles Container
        toggles_frame = ctk.CTkFrame(params_frame, fg_color="transparent")
        toggles_frame.pack(fill="x", padx=15, pady=5)
        toggles_frame.grid_columnconfigure((0, 1), weight=1)

        # Input Toggles
        ctk.CTkLabel(toggles_frame, text="Inputs:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.chk_repeating = ctk.CTkCheckBox(toggles_frame, text="Repeating ('assets/')")
        self.chk_repeating.grid(row=1, column=0, sticky="w", pady=2)
        self.chk_repeating.select()
        
        self.chk_mixed = ctk.CTkCheckBox(toggles_frame, text="Mixed Packs ('source/')")
        self.chk_mixed.grid(row=2, column=0, sticky="w", pady=2)
        self.chk_mixed.select()

        # Output Toggles
        ctk.CTkLabel(toggles_frame, text="Outputs:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, sticky="w", pady=(0, 5))
        self.chk_out_sheets = ctk.CTkCheckBox(toggles_frame, text="Sticker Sheets")
        self.chk_out_sheets.grid(row=1, column=1, sticky="w", pady=2)
        self.chk_out_sheets.select()
        
        self.chk_out_simple = ctk.CTkCheckBox(toggles_frame, text="Dot-Grid Pins")
        self.chk_out_simple.grid(row=2, column=1, sticky="w", pady=2)
        self.chk_out_simple.select()
        
        self.chk_out_adv = ctk.CTkCheckBox(toggles_frame, text="Photographic Pins")
        self.chk_out_adv.grid(row=3, column=1, sticky="w", pady=2)
        self.chk_out_adv.select()

        # 3. Grid Sliders
        self.rows_label = ctk.CTkLabel(params_frame, text="Rows: 3")
        self.rows_label.pack(padx=15, anchor="w", pady=(10, 0))
        self.rows_slider = ctk.CTkSlider(params_frame, from_=1, to=10, number_of_steps=9, command=self.update_rows_label)
        self.rows_slider.set(3)
        self.rows_slider.pack(fill="x", padx=15, pady=(0, 10))

        self.cols_label = ctk.CTkLabel(params_frame, text="Columns: 3")
        self.cols_label.pack(padx=15, anchor="w")
        self.cols_slider = ctk.CTkSlider(params_frame, from_=1, to=10, number_of_steps=9, command=self.update_cols_label)
        self.cols_slider.set(3)
        self.cols_slider.pack(fill="x", padx=15, pady=(0, 10))

        self.padding_label = ctk.CTkLabel(params_frame, text="Grid Padding: 320 px")
        self.padding_label.pack(padx=15, anchor="w")
        self.padding_slider = ctk.CTkSlider(params_frame, from_=80, to=600, number_of_steps=26, command=self.update_padding_label)
        self.padding_slider.set(320)
        self.padding_slider.pack(fill="x", padx=15, pady=(0, 10))

        self.fill_label = ctk.CTkLabel(params_frame, text="Cell Fill Ratio: 85%")
        self.fill_label.pack(padx=15, anchor="w")
        self.fill_slider = ctk.CTkSlider(params_frame, from_=50, to=95, number_of_steps=9, command=self.update_fill_label)
        self.fill_slider.set(85)
        self.fill_slider.pack(fill="x", padx=15, pady=(0, 15))

        # 4. Action Buttons
        self.run_btn = ctk.CTkButton(
            params_frame, text="▶ Run Generation Pipeline", font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#0052cc", hover_color="#0747a6", height=40, command=self.start_processing_thread
        )
        self.run_btn.pack(fill="x", padx=15, pady=10)

        # Right Panel: Terminal
        terminal_frame = ctk.CTkFrame(self)
        terminal_frame.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")

        ctk.CTkLabel(terminal_frame, text="Live Output Log", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10), padx=15, anchor="w")
        self.textbox = ctk.CTkTextbox(terminal_frame, wrap="word", font=ctk.CTkFont(family="Consolas", size=12))
        self.textbox.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def update_rows_label(self, val): self.rows_label.configure(text=f"Rows: {int(val)}")
    def update_cols_label(self, val): self.cols_label.configure(text=f"Columns: {int(val)}")
    def update_padding_label(self, val): self.padding_label.configure(text=f"Grid Padding: {int(val)} px")
    def update_fill_label(self, val): self.fill_label.configure(text=f"Cell Fill Ratio: {int(val)}%")

    def append_log(self, message: str):
        self.textbox.insert("end", message + "\n")
        self.textbox.see("end")

    def start_processing_thread(self):
        self.run_btn.configure(state="disabled", text="Processing...")
        threading.Thread(target=self.execute_pipeline, daemon=True).start()

    def execute_pipeline(self):
        run_pipeline(
            gen_repeating=bool(self.chk_repeating.get()),
            gen_mixed=bool(self.chk_mixed.get()),
            out_sheets=bool(self.chk_out_sheets.get()),
            out_simple=bool(self.chk_out_simple.get()),
            out_advanced=bool(self.chk_out_adv.get()),
            rows=int(self.rows_slider.get()),
            cols=int(self.cols_slider.get()),
            padding=int(self.padding_slider.get()),
            fill_ratio=self.fill_slider.get() / 100.0,
            seo_profile=self.profile_dropdown.get(),
            log_callback=self.append_log
        )
        self.run_btn.configure(state="normal", text="▶ Run Generation Pipeline")