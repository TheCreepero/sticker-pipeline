import os
import glob
import csv
import re
from datetime import datetime
from PIL import Image, ImageDraw, ImageFilter

# ---------------------------------------------------------
# IMAGE PROCESSING FUNCTIONS
# ---------------------------------------------------------

def clean_alpha_channel(img, threshold=35):
    """Strips invisible anti-aliasing ghosts to prevent cutlines from merging."""
    img = img.convert("RGBA")
    r, g, b, a = img.split()
    a = a.point(lambda p: p if p > threshold else 0)
    img.putalpha(a)
    return img

def create_dot_grid_background(
    width=1000, 
    height=1500, 
    dot_spacing=40, 
    dot_radius=2, 
    bg_color="#f8f6f0", 
    dot_color="#ded9cf",
    grid_angle=0
):
    """Generates an aesthetic dot-grid paper background with optional tilt."""
    if grid_angle == 0:
        bg = Image.new("RGBA", (width, height), bg_color)
        draw = ImageDraw.Draw(bg)
        for x in range(dot_spacing // 2, width, dot_spacing):
            for y in range(dot_spacing // 2, height, dot_spacing):
                draw.ellipse([x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius], fill=dot_color)
        return bg
    
    # Oversize canvas to rotate without clipping corners
    diag = int((width**2 + height**2) ** 0.5) + 200
    big_bg = Image.new("RGBA", (diag, diag), bg_color)
    draw = ImageDraw.Draw(big_bg)
    for x in range(0, diag, dot_spacing):
        for y in range(0, diag, dot_spacing):
            draw.ellipse([x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius], fill=dot_color)
    
    rotated = big_bg.rotate(grid_angle, resample=Image.BICUBIC)
    crop_x = (diag - width) // 2
    crop_y = (diag - height) // 2
    return rotated.crop((crop_x, crop_y, crop_x + width, crop_y + height))

def build_physical_sheet(sticker_img, margin=24, corner_radius=18, card_color=(255, 255, 255, 255)):
    """Wraps transparent icons in a rounded matte sticker-sheet card backing."""
    w = sticker_img.width + margin * 2
    h = sticker_img.height + margin * 2
    sheet_card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(sheet_card)
    draw.rounded_rectangle([0, 0, w, h], radius=corner_radius, fill=card_color)
    sheet_card.paste(sticker_img, (margin, margin), mask=sticker_img)
    return sheet_card

def add_drop_shadow(image, offset=(10, 18), blur_radius=20, shadow_alpha=75):
    """Adds a soft Gaussian shadow around the sticker card."""
    shadow_w = image.width + blur_radius * 4
    shadow_h = image.height + blur_radius * 4
    shadow = Image.new("RGBA", (shadow_w, shadow_h), (0, 0, 0, 0))

    mask = image.split()[3]
    shadow_base = Image.new("RGBA", image.size, (20, 20, 20, shadow_alpha))
    shadow.paste(shadow_base, (blur_radius * 2 + offset[0], blur_radius * 2 + offset[1]), mask=mask)
    
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))
    shadow.paste(image, (blur_radius * 2, blur_radius * 2), mask=image)
    return shadow

# ---------------------------------------------------------
# HTML DASHBOARD GENERATOR
# ---------------------------------------------------------

def generate_unified_dashboard(items, output_html="output/mixed_dashboard.html"):
    """Generates a side-by-side HTML dashboard for Redbubble and Pinterest."""
    html_cards = ""
    for item in items:
        html_cards += f"""
        <div class="card">
            <div class="preview-section">
                <div class="preview">
                    <strong>Redbubble Export</strong>
                    <img src="{item['rb_filename']}" alt="{item['rb_title']}" style="object-fit: contain;">
                </div>
                <div class="preview">
                    <strong>Pinterest Pin</strong>
                    <img src="{item['pin_filename']}" alt="{item['pin_title']}" style="object-fit: cover;">
                </div>
            </div>
            
            <div class="metadata-section">
                <div class="column">
                    <h3>🔴 Redbubble SEO</h3>
                    <div class="field-group">
                        <label>Title</label>
                        <div class="input-row">
                            <input type="text" readonly value="{item['rb_title']}" id="rb-title-{item['id']}">
                            <button onclick="copyToClipboard('rb-title-{item['id']}', this)">Copy</button>
                        </div>
                    </div>
                    <div class="field-group">
                        <label>Primary Tag</label>
                        <div class="input-row">
                            <input type="text" readonly value="{item['rb_ptag']}" id="rb-ptag-{item['id']}">
                            <button onclick="copyToClipboard('rb-ptag-{item['id']}', this)">Copy</button>
                        </div>
                    </div>
                    <div class="field-group">
                        <label>Tags (Comma-Separated)</label>
                        <div class="input-row">
                            <textarea readonly rows="3" id="rb-tags-{item['id']}">{item['rb_tags']}</textarea>
                            <button onclick="copyToClipboard('rb-tags-{item['id']}', this)">Copy</button>
                        </div>
                    </div>
                    <div class="field-group">
                        <label>Description</label>
                        <div class="input-row">
                            <textarea readonly rows="4" id="rb-desc-{item['id']}">{item['rb_desc']}</textarea>
                            <button onclick="copyToClipboard('rb-desc-{item['id']}', this)">Copy</button>
                        </div>
                    </div>
                </div>

                <div class="column">
                    <h3>📌 Pinterest SEO</h3>
                    <div class="field-group">
                        <label>Pin Title</label>
                        <div class="input-row">
                            <input type="text" readonly value="{item['pin_title']}" id="pin-title-{item['id']}">
                            <button onclick="copyToClipboard('pin-title-{item['id']}', this)">Copy</button>
                        </div>
                    </div>
                    <div class="field-group">
                        <label>Pin Description & Hashtags</label>
                        <div class="input-row">
                            <textarea readonly rows="6" id="pin-desc-{item['id']}">{item['pin_desc']}</textarea>
                            <button onclick="copyToClipboard('pin-desc-{item['id']}', this)">Copy</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Mixed Pack Metadata Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f4f5f7; margin: 0; padding: 24px; color: #172b4d; }}
        h1 {{ margin-bottom: 24px; font-size: 24px; }}
        .card {{ background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 30px; display: flex; flex-direction: column; gap: 24px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }}
        .preview-section {{ display: flex; gap: 20px; padding-bottom: 20px; border-bottom: 1px solid #ebecf0; }}
        .preview {{ display: flex; flex-direction: column; align-items: center; gap: 8px; font-size: 13px; color: #5e6c84; }}
        .preview img {{ width: 180px; height: 180px; border: 1px dashed #ccc; border-radius: 6px; background: #fafafa; }}
        .metadata-section {{ display: flex; gap: 30px; }}
        .column {{ flex: 1; display: flex; flex-direction: column; gap: 12px; }}
        h3 {{ margin: 0 0 8px 0; font-size: 16px; color: #172b4d; }}
        .field-group {{ display: flex; flex-direction: column; gap: 4px; }}
        label {{ font-size: 12px; font-weight: 600; text-transform: uppercase; color: #5e6c84; }}
        .input-row {{ display: flex; gap: 8px; }}
        input, textarea {{ flex-grow: 1; border: 1px solid #dfe1e6; border-radius: 4px; padding: 8px; font-size: 13px; background: #fafbfc; color: #091e42; font-family: inherit; resize: none; }}
        button {{ background: #0052cc; color: white; border: none; border-radius: 4px; padding: 0 16px; font-weight: 600; cursor: pointer; transition: background 0.2s; white-space: nowrap; }}
        button:hover {{ background: #0747a6; }}
        button.copied {{ background: #36b37e; }}
    </style>
</head>
<body>
    <h1>Mixed Pack & Pinterest Dashboard</h1>
    {html_cards}
    <script>
        function copyToClipboard(elementId, btn) {{
            const el = document.getElementById(elementId);
            navigator.clipboard.writeText(el.value).then(() => {{
                const originalText = btn.innerText;
                btn.innerText = 'Copied!';
                btn.classList.add('copied');
                setTimeout(() => {{ btn.innerText = originalText; btn.classList.remove('copied'); }}, 1500);
            }});
        }}
    </script>
</body>
</html>"""

    with open(output_html, "w", encoding="utf-8") as f:
        f.write(full_html)

# ---------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------

def generate_mixed_packs(
    input_dir="source", 
    output_dir="output", 
    output_csv="mixed_listings.csv",
    padding=320, 
    canvas_size=(3200, 3200),
    pin_size=(1000, 1500),
    rotation_angle=-3.5
):
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    png_files = sorted(glob.glob(os.path.join(input_dir, "*.png")))
    total_files = len(png_files)
    
    if total_files == 0:
        print(f"No PNG files found. Drop your sticker designs into the '{input_dir}/' folder.")
        return

    max_rows = 6
    cols = 3
    chunks = [png_files[i:i + max_rows] for i in range(0, total_files, max_rows)]
    
    print(f"Found {total_files} designs. Generating {len(chunks)} mixed sticker sheets and Pinterest pins...\n")

    cell_w = (canvas_size[0] - (cols + 1) * padding) // cols
    cell_h = (canvas_size[1] - (max_rows + 1) * padding) // max_rows

    max_target_w = int(cell_w * 0.85)
    max_target_h = int(cell_h * 0.85)

    # Note the delimiter change here for EU Excel compatibility
    csv_rows = [["RB_Filename", "RB_Title", "RB_Primary_Tag", "RB_Tags", "RB_Description", "Pin_Filename", "Pin_Title", "Pin_Description"]]
    dashboard_items = []

    for chunk_idx, chunk in enumerate(chunks, start=1):
        sheet = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        clean_names = []

        # 1. Build the Redbubble Sheet
        for r, img_path in enumerate(chunk):
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            c_name = re.sub(r"\d+", "", base_name).replace("_", " ").replace("-", " ").strip().title()
            if not c_name: c_name = "Planner"
            clean_names.append(c_name)

            raw_img = Image.open(img_path)
            sticker = clean_alpha_channel(raw_img, threshold=35)
            bbox = sticker.getbbox()
            if bbox:
                sticker = sticker.crop(bbox)

            scale = min(max_target_w / sticker.width, max_target_h / sticker.height)
            new_w = max(1, int(sticker.width * scale))
            new_h = max(1, int(sticker.height * scale))
            sticker = sticker.resize((new_w, new_h), Image.Resampling.LANCZOS)

            for c in range(cols):
                x = padding + c * (cell_w + padding) + (cell_w - sticker.width) // 2
                y = padding + r * (cell_h + padding) + (cell_h - sticker.height) // 2
                sheet.paste(sticker, (x, y), sticker)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        rb_filename = f"mixed_pack_{timestamp}.png"
        sheet.save(os.path.join(output_dir, rb_filename), "PNG")

        # 2. Build the Pinterest Pin
        target_w = 720
        scale = target_w / sheet.width
        target_h = int(sheet.height * scale)
        sheet_resized = sheet.resize((target_w, target_h), Image.Resampling.LANCZOS)

        composite_item = build_physical_sheet(sheet_resized, margin=24, corner_radius=18)
        with_shadow = add_drop_shadow(composite_item, offset=(10, 18), blur_radius=20, shadow_alpha=75)
        rotated_item = with_shadow.rotate(rotation_angle, expand=True, resample=Image.BICUBIC)

        pin_bg = create_dot_grid_background(width=pin_size[0], height=pin_size[1], grid_angle=0)
        pos_x = (pin_size[0] - rotated_item.width) // 2
        pos_y = (pin_size[1] - rotated_item.height) // 2
        pin_bg.paste(rotated_item, (pos_x, pos_y), mask=rotated_item)

        pin_filename = f"pin_mixed_pack_{timestamp}.png"
        pin_bg.convert("RGB").save(os.path.join(output_dir, pin_filename), "PNG", quality=95)

        # 3. Generate Redbubble Metadata
        display_title = ", ".join(clean_names[:2])
        if len(clean_names) > 2:
            display_title += f" & {clean_names[2]}"
            
        rb_title = f"Minimalist {display_title} Bullet Journal Sticker Pack"
        rb_ptag = f"{clean_names[0].lower()} planner sticker"
        
        specific_tags = [f"{name.lower()} sticker" for name in clean_names[:4]]
        core_tags = [
            "bujo typography", "functional planner sticker", "bullet journal aesthetic", 
            "habit tracker sticker", "minimalist aesthetic sticker", "black and white sticker", 
            "stationery addict"
        ]
        rb_tags = ", ".join(specific_tags + core_tags)
        
        rb_desc = (
            f"Organize your routines with this minimalist functional sticker pack featuring "
            f"{', '.join(name.lower() for name in clean_names[:4])} and more. Perfect for habit trackers, "
            f"weekly spreads, and bullet journal layouts. Choose the matte finish for a seamless look."
        )

        # 4. Generate Pinterest Metadata
        pin_title = f"Minimalist {display_title} Bullet Journal Sticker Pack | Aesthetic Bujo Deco"
        hashtag_tag = clean_names[0].lower().replace(' ', '')
        pin_desc = (
            f"Keep your weekly spreads, reading logs, and habit trackers organized with this minimalist "
            f"black and white {display_title} sticker pack. Designed specifically for bullet journals, "
            f"student planners, and studygram spreads. Printed on clean matte paper. "
            f"#bulletjournal #bujoinspo #plannerstickers #studygram #functionalplanning #{hashtag_tag}sticker"
        )

        # Append to CSV and Dashboard
        csv_rows.append([rb_filename, rb_title, rb_ptag, rb_tags, rb_desc, pin_filename, pin_title, pin_desc])
        dashboard_items.append({
            "id": chunk_idx,
            "rb_filename": rb_filename,
            "rb_title": rb_title,
            "rb_ptag": rb_ptag,
            "rb_tags": rb_tags,
            "rb_desc": rb_desc,
            "pin_filename": pin_filename,
            "pin_title": pin_title,
            "pin_desc": pin_desc
        })

        print(f"[{chunk_idx}/{len(chunks)}] Generated Sheet & Pin for: {display_title}")

    # Save CSV with Semicolon Delimiter for European Excel compatibility
    with open(os.path.join(output_dir, output_csv), mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerows(csv_rows)

    # Save HTML Dashboard
    generate_unified_dashboard(dashboard_items, os.path.join(output_dir, "mixed_dashboard.html"))

    print(f"\nSuccess! All files saved to the '{output_dir}/' folder.")
    print("Double-click 'mixed_dashboard.html' inside the output folder to copy your metadata.")

if __name__ == "__main__":
    generate_mixed_packs()