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
from src.metadata import extract_clean_name, build_seo_metadata, save_csv, generate_unified_html


def load_templates(config_path: str = "config/templates.json") -> dict:
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def process_pins(
    sheet_path: str,
    output_dir: str,
    base_name: str,
    templates: dict,
    rotation_angle: float = -3.5
) -> str:
    """Generates standard dot-grid or photographic mockup pins."""
    sheet = Image.open(sheet_path)

    # Use photographic mockup template if available
    if "desk_mockup" in templates and os.path.exists(templates["desk_mockup"]["file"]):
        bg = Image.open(templates["desk_mockup"]["file"])
        corners = templates["desk_mockup"]["corners"]
        pin_img = warp_sticker_to_page(sheet, bg, corners, apply_multiply=True)
        pin_filename = f"pin_{base_name}.jpg"
        pin_path = os.path.join(output_dir, pin_filename)
        pin_img.convert("RGB").save(pin_path, quality=95)
        return pin_filename

    # Fallback to rotated dot-grid background
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

    pin_filename = f"pin_{base_name}.png"
    pin_path = os.path.join(output_dir, pin_filename)
    pin_bg.convert("RGB").save(pin_path, quality=95)
    return pin_filename


def run_pipeline(mode: str = "all"):
    os.makedirs("assets", exist_ok=True)
    os.makedirs("source", exist_ok=True)
    os.makedirs("exports", exist_ok=True)

    templates = load_templates()
    dashboard_items = []
    csv_rows = [["RB_Filename", "RB_Title", "RB_Primary_Tag", "RB_Tags", "RB_Description", "Pin_Filename", "Pin_Title", "Pin_Description"]]
    item_id = 1

    # 1. Process Repeating Single Sheets from assets/
    if mode in ["all", "repeating"]:
        asset_files = sorted(glob.glob("assets/*.png"))
        print(f"--- Processing {len(asset_files)} Single Designs from 'assets/' ---")
        for img_path in asset_files:
            clean_name = extract_clean_name(img_path)
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            sheet_filename = f"{base_name}_sheet.png"
            sheet_path = os.path.join("exports", sheet_filename)

            sheet = build_repeating_sheet(img_path)
            sheet.save(sheet_path, "PNG")

            pin_filename = process_pins(sheet_path, "exports", base_name, templates)
            meta = build_seo_metadata([clean_name], is_mixed=False)

            csv_rows.append([sheet_filename, meta["rb_title"], meta["rb_ptag"], meta["rb_tags"], meta["rb_desc"], pin_filename, meta["pin_title"], meta["pin_desc"]])
            dashboard_items.append({
                "id": item_id,
                "rb_filename": sheet_filename,
                "pin_filename": pin_filename,
                **meta
            })
            item_id += 1
            print(f"  ✓ Processed: {clean_name}")

    # 2. Process Mixed Pack Sheets from source/
    if mode in ["all", "mixed"]:
        source_files = sorted(glob.glob("source/*.png"))
        chunks = [source_files[i:i + 6] for i in range(0, len(source_files), 6)]
        print(f"\n--- Processing {len(chunks)} Mixed Pack Sheets from 'source/' ---")
        for chunk in chunks:
            names = [extract_clean_name(p) for p in chunk]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            sheet_filename = f"mixed_pack_{timestamp}.png"
            sheet_path = os.path.join("exports", sheet_filename)

            sheet = build_mixed_sheet(chunk)
            sheet.save(sheet_path, "PNG")

            pin_filename = process_pins(sheet_path, "exports", f"mixed_{timestamp}", templates)
            meta = build_seo_metadata(names, is_mixed=True)

            csv_rows.append([sheet_filename, meta["rb_title"], meta["rb_ptag"], meta["rb_tags"], meta["rb_desc"], pin_filename, meta["pin_title"], meta["pin_desc"]])
            dashboard_items.append({
                "id": item_id,
                "rb_filename": sheet_filename,
                "pin_filename": pin_filename,
                **meta
            })
            item_id += 1
            print(f"  ✓ Created Mixed Sheet: {meta['rb_title']}")

    # Export Catalogs
    if dashboard_items:
        save_csv(csv_rows, "exports/listings.csv")
        generate_unified_html(dashboard_items, "exports/listings.html")
        print("\n==========================================")
        print("Pipeline Complete!")
        print("  • Exports Folder: 'exports/'")
        print("  • Visual Dashboard: 'exports/listings.html'")
        print("  • Semicolon CSV: 'exports/listings.csv'")
        print("==========================================")
    else:
        print("No image assets found to process in 'assets/' or 'source/'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated Sticker Sheet & Mockup Pipeline")
    parser.add_argument("--mode", choices=["all", "repeating", "mixed"], default="all", help="Execution mode")
    args = parser.parse_args()
    run_pipeline(args.mode)