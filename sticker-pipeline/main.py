import argparse
import glob
import json
import os
import sys
from datetime import datetime
from PIL import Image

from src.grid_builder import build_repeating_sheet, build_mixed_sheet
from src.homography import warp_sticker_to_page
from src.image_ops import build_physical_sheet, add_drop_shadow, create_dot_grid_background
from src.metadata import extract_clean_name, build_seo_metadata, save_csv, generate_unified_html, load_existing_metadata


def load_templates(config_path: str = "config/templates.json") -> dict:
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def generate_simple_pin(
    sheet_path: str,
    output_dir: str,
    base_name: str,
    rotation_angle: float = -3.5
) -> str:
    """Generates a clean dot-grid paper mockup pin."""
    sheet = Image.open(sheet_path)

    target_w = 720
    scale = target_w / sheet.width
    target_h = int(sheet.height * scale)
    sheet_resized = sheet.resize((target_w, target_h), Image.Resampling.LANCZOS)

    card = build_physical_sheet(sheet_resized)
    shadowed = add_drop_shadow(card)
    rotated = shadowed.rotate(rotation_angle, expand=True, resample=Image.BICUBIC)

    pin_bg = create_dot_grid_background(width=1000, height=1500, grid_angle=0)
    pos_x = (1000 - rotated.width) // 2
    pos_y = (1500 - rotated.height) // 2
    pin_bg.paste(rotated, (pos_x, pos_y), mask=rotated)

    pin_filename = f"pin_simple_{base_name}.png"
    pin_path = os.path.join(output_dir, pin_filename)
    pin_bg.convert("RGB").save(pin_path, quality=95)
    return pin_filename


def generate_advanced_pin(
    sheet_path: str,
    output_dir: str,
    base_name: str,
    templates: dict
) -> str:
    """Generates a photographic 3D perspective mockup pin if templates exist."""
    for template_name, template_data in templates.items():
        if os.path.exists(template_data["file"]):
            sheet = Image.open(sheet_path)
            bg = Image.open(template_data["file"])
            corners = template_data["corners"]

            pin_img = warp_sticker_to_page(sheet, bg, corners, apply_multiply=True)
            
            pin_filename = f"pin_adv_{template_name}_{base_name}.jpg"
            pin_path = os.path.join(output_dir, pin_filename)
            pin_img.convert("RGB").save(pin_path, quality=95)
            
            return pin_filename
    return ""


def run_pipeline(mode: str = "all", rows: int = 3, cols: int = 3):
    # Root working paths
    os.makedirs("assets", exist_ok=True)
    os.makedirs("source", exist_ok=True)

    # Subdivided export paths
    sheets_dir = os.path.join("exports", "sheets")
    mixed_sheets_dir = os.path.join("exports", "mixed_sheets")
    pins_simple_dir = os.path.join("exports", "pins_simple")
    pins_adv_dir = os.path.join("exports", "pins_advanced")

    os.makedirs(sheets_dir, exist_ok=True)
    os.makedirs(mixed_sheets_dir, exist_ok=True)
    os.makedirs(pins_simple_dir, exist_ok=True)
    os.makedirs(pins_adv_dir, exist_ok=True)

    csv_path = "exports/listings.csv"
    csv_rows, dashboard_items = load_existing_metadata(csv_path)
    item_id = len(dashboard_items) + 1
    templates = load_templates()

    print(f"--- Starting pipeline (Mode: {mode} | Grid: {rows}x{cols}) ---")

    processed_any = False

    # 1. Process Repeating Single Sheets from assets/
    if mode in ["all", "repeating"]:
        asset_files = sorted(glob.glob("assets/*.png"))
        print(f"--- Processing {len(asset_files)} Single Designs from 'assets/' ---")
        for img_path in asset_files:
            clean_name = extract_clean_name(img_path)
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            sheet_filename = f"{base_name}_sheet.png"
            sheet_path = os.path.join(sheets_dir, sheet_filename)

            sheet = build_repeating_sheet(img_path, rows=rows, cols=cols)
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
                "rb_filepath": f"sheets/{sheet_filename}",
                "simple_pin_filepath": f"pins_simple/{simple_pin}",
                "adv_pin_filepath": f"pins_advanced/{adv_pin}" if adv_pin else "",
                **meta
            })
            item_id += 1
            processed_any = True
            print(f"  ✓ Processed: {clean_name}")

    # 2. Process Mixed Pack Sheets from source/
    if mode in ["all", "mixed"]:
        source_files = sorted(glob.glob("source/*.png"))
        chunks = [source_files[i:i + rows] for i in range(0, len(source_files), rows)]
        print(f"\n--- Processing {len(chunks)} Mixed Pack Sheets from 'source/' ---")
        for chunk in chunks:
            names = [extract_clean_name(p) for p in chunk]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            base_name = f"mixed_pack_{timestamp}"
            sheet_filename = f"{base_name}.png"
            sheet_path = os.path.join(mixed_sheets_dir, sheet_filename)

            sheet = build_mixed_sheet(chunk, cols=cols, max_rows=rows)
            sheet.save(sheet_path, "PNG")

            simple_pin = generate_simple_pin(sheet_path, pins_simple_dir, base_name)
            adv_pin = generate_advanced_pin(sheet_path, pins_adv_dir, base_name, templates)
            meta = build_seo_metadata(names, is_mixed=True)

            csv_rows.append([
                f"mixed_sheets/{sheet_filename}", meta["rb_title"], meta["rb_ptag"], meta["rb_tags"], meta["rb_desc"],
                f"pins_simple/{simple_pin}", f"pins_advanced/{adv_pin}" if adv_pin else "",
                meta["pin_title"], meta["pin_desc"]
            ])
            dashboard_items.append({
                "id": item_id,
                "rb_filepath": f"mixed_sheets/{sheet_filename}",
                "simple_pin_filepath": f"pins_simple/{simple_pin}",
                "adv_pin_filepath": f"pins_advanced/{adv_pin}" if adv_pin else "",
                **meta
            })
            item_id += 1
            processed_any = True
            print(f"  ✓ Created Mixed Sheet: {meta['rb_title']}")

    # Export Catalogs
    if processed_any or dashboard_items:
        save_csv(csv_rows, csv_path)
        generate_unified_html(dashboard_items, "exports/listings.html")
        print("\n==========================================")
        print("Pipeline Complete!")
        print("  • Sheets Output:         'exports/sheets/'")
        print("  • Mixed Sheets Output:   'exports/mixed_sheets/'")
        print("  • Simple Pins Output:    'exports/pins_simple/'")
        print("  • Advanced Pins Output:  'exports/pins_advanced/'")
        print("  • Dashboard:             'exports/listings.html'")
        print("  • Semicolon CSV:         'exports/listings.csv'")
        print("==========================================")
    else:
        print("No image assets found to process in 'assets/' or 'source/'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated Sticker Sheet & Mockup Pipeline")
    parser.add_argument("--mode", choices=["all", "repeating", "mixed"], default="all", help="Execution mode")
    parser.add_argument("--rows", type=int, default=3, help="Number of rows per sheet")
    parser.add_argument("--cols", type=int, default=3, help="Number of columns per sheet")
    args = parser.parse_args()
    
    run_pipeline(mode=args.mode, rows=args.rows, cols=args.cols)