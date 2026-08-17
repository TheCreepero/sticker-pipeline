import glob
import os
import threading
from datetime import datetime
import customtkinter as ctk
from PIL import Image

from src.grid_builder import build_repeating_sheet, build_mixed_sheet
from src.homography import warp_sticker_to_page
from src.image_ops import build_physical_sheet, add_drop_shadow, create_dot_grid_background
from src.metadata import extract_clean_name, build_seo_metadata, save_csv, generate_unified_html
from main import load_templates, generate_simple_pin, generate_advanced_pin


class BuilderView(ctk.CTkFrame):
    def __init__(self, master, log_callback):
        super().__init__(master)
        self.log = log_callback

        # Options Container
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_controls()

    def setup_controls(self):
        # Left Panel: Parameters
        params_frame = ctk.CTkFrame(self)
        params_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        title_label = ctk.CTkLabel(params_frame, text="Sheet Generation Controls", font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(pady=(15, 10), padx=15, anchor="w")

        # Mode Selection
        ctk.CTkLabel(params_frame, text="Execution Mode:", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 2), padx=15, anchor="w")
        self.mode_var = ctk.StringVar(value="all")
        mode_seg = ctk.CTkSegmentedButton(params_frame, values=["all", "repeating", "mixed"], variable=self.mode_var)
        mode_seg.pack(fill="x", padx=15, pady=(0, 15))

        # Grid Padding Slider
        self.padding_label = ctk.CTkLabel(params_frame, text="Grid Padding: 320 px")
        self.padding_label.pack(padx=15, anchor="w")
        self.padding_slider = ctk.CTkSlider(params_frame, from_=80, to=600, number_of_steps=26, command=self.update_padding_label)
        self.padding_slider.set(320)
        self.padding_slider.pack(fill="x", padx=15, pady=(0, 15))

        # Fill Ratio Slider
        self.fill_label = ctk.CTkLabel(params_frame, text="Cell Fill Ratio: 85%")
        self.fill_label.pack(padx=15, anchor="w")
        self.fill_slider = ctk.CTkSlider(params_frame, from_=50, to=95, number_of_steps=9, command=self.update_fill_label)
        self.fill_slider.set(85)
        self.fill_slider.pack(fill="x", padx=15, pady=(0, 20))

        # Action Buttons
        self.run_btn = ctk.CTkButton(
            params_frame,
            text="▶ Run Generation Pipeline",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#0052cc",
            hover_color="#0747a6",
            height=40,
            command=self.start_processing_thread
        )
        self.run_btn.pack(fill="x", padx=15, pady=10)

        # Right Panel: Live Terminal Status
        terminal_frame = ctk.CTkFrame(self)
        terminal_frame.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")

        term_title = ctk.CTkLabel(terminal_frame, text="Live Output Log", font=ctk.CTkFont(size=16, weight="bold"))
        term_title.pack(pady=(15, 10), padx=15, anchor="w")

        self.textbox = ctk.CTkTextbox(terminal_frame, wrap="word", font=ctk.CTkFont(family="Consolas", size=12))
        self.textbox.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def update_padding_label(self, val):
        self.padding_label.configure(text=f"Grid Padding: {int(val)} px")

    def update_fill_label(self, val):
        self.fill_label.configure(text=f"Cell Fill Ratio: {int(val)}%")

    def append_log(self, message: str):
        self.textbox.insert("end", message + "\n")
        self.textbox.see("end")

    def start_processing_thread(self):
        self.run_btn.configure(state="disabled", text="Processing...")
        threading.Thread(target=self.run_batch_process, daemon=True).start()

    def run_batch_process(self):
        mode = self.mode_var.get()
        padding = int(self.padding_slider.get())
        fill_ratio = self.fill_slider.get() / 100.0

        sheets_dir = os.path.join("exports", "sheets")
        pins_simple_dir = os.path.join("exports", "pins_simple")
        pins_adv_dir = os.path.join("exports", "pins_advanced")

        os.makedirs(sheets_dir, exist_ok=True)
        os.makedirs(pins_simple_dir, exist_ok=True)
        os.makedirs(pins_adv_dir, exist_ok=True)

        templates = load_templates()
        dashboard_items = []
        csv_rows = [[
            "RB_Filename", "RB_Title", "RB_Primary_Tag", "RB_Tags", "RB_Description",
            "Simple_Pin_Filename", "Advanced_Pin_Filename", "Pin_Title", "Pin_Description"
        ]]
        item_id = 1

        self.append_log(f"[{datetime.now().strftime('%H:%M:%S')}] --- Starting pipeline (Mode: {mode}) ---")

        if mode in ["all", "repeating"]:
            asset_files = sorted(glob.glob("assets/*.png"))
            self.append_log(f"Found {len(asset_files)} files in 'assets/'")
            for img_path in asset_files:
                clean_name = extract_clean_name(img_path)
                base_name = os.path.splitext(os.path.basename(img_path))[0]
                sheet_filename = f"{base_name}_sheet.png"
                sheet_path = os.path.join(sheets_dir, sheet_filename)

                sheet = build_repeating_sheet(img_path, padding=padding, cell_fill_ratio=fill_ratio)
                sheet.save(sheet_path, "PNG")

                simple_pin = generate_simple_pin(sheet_path, pins_simple_dir, base_name)
                adv_pin = generate_advanced_pin(sheet_path, pins_adv_dir, base_name, templates)
                meta = build_seo_metadata([clean_name], is_mixed=False)

                csv_rows.append([
                    f"sheets/{sheet_filename}", meta["rb_title"], meta["rb_ptag"], meta["rb_tags"], meta["rb_desc"],
                    f"pins_simple/{simple_pin}", f"pins_advanced/{adv_pin}" if adv_pin else "",
                    meta["pin_title"], meta["pin_desc"]
                ])
                dashboard_items.append({
                    "id": item_id,
                    "rb_filename": sheet_filename,
                    "simple_pin_filename": simple_pin,
                    "adv_pin_filename": adv_pin,
                    **meta
                })
                item_id += 1
                self.append_log(f"  ✓ Processed: {clean_name}")

        if mode in ["all", "mixed"]:
            source_files = sorted(glob.glob("source/*.png"))
            chunks = [source_files[i:i + 6] for i in range(0, len(source_files), 6)]
            self.append_log(f"Found {len(source_files)} files in 'source/' ({len(chunks)} packs)")
            for chunk in chunks:
                names = [extract_clean_name(p) for p in chunk]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                base_name = f"mixed_pack_{timestamp}"
                sheet_filename = f"{base_name}.png"
                sheet_path = os.path.join(sheets_dir, sheet_filename)

                sheet = build_mixed_sheet(chunk, padding=padding, cell_fill_ratio=fill_ratio)
                sheet.save(sheet_path, "PNG")

                simple_pin = generate_simple_pin(sheet_path, pins_simple_dir, base_name)
                adv_pin = generate_advanced_pin(sheet_path, pins_adv_dir, base_name, templates)
                meta = build_seo_metadata(names, is_mixed=True)

                csv_rows.append([
                    f"sheets/{sheet_filename}", meta["rb_title"], meta["rb_ptag"], meta["rb_tags"], meta["rb_desc"],
                    f"pins_simple/{simple_pin}", f"pins_advanced/{adv_pin}" if adv_pin else "",
                    meta["pin_title"], meta["pin_desc"]
                ])
                dashboard_items.append({
                    "id": item_id,
                    "rb_filename": sheet_filename,
                    "simple_pin_filename": simple_pin,
                    "adv_pin_filename": adv_pin,
                    **meta
                })
                item_id += 1
                self.append_log(f"  ✓ Created Mixed Sheet: {meta['rb_title']}")

        if dashboard_items:
            save_csv(csv_rows, "exports/listings.csv")
            generate_unified_html(dashboard_items, "exports/listings.html")
            self.append_log(f"[{datetime.now().strftime('%H:%M:%S')}] Pipeline Complete! Saved to 'exports/'")
        else:
            self.append_log("No PNG images found in 'assets/' or 'source/'.")

        self.run_btn.configure(state="normal", text="▶ Run Generation Pipeline")