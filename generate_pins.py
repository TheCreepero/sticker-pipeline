import csv
import glob
import os
import re
from PIL import Image, ImageDraw, ImageFilter

def create_dot_grid_background(
    width=1000, 
    height=1500, 
    dot_spacing=40, 
    dot_radius=2, 
    bg_color="#f8f6f0", 
    dot_color="#ded9cf",
    grid_angle=0
):
    """Generates an aesthetic dot-grid paper background."""
    if grid_angle == 0:
        bg = Image.new("RGBA", (width, height), bg_color)
        draw = ImageDraw.Draw(bg)
        for x in range(dot_spacing // 2, width, dot_spacing):
            for y in range(dot_spacing // 2, height, dot_spacing):
                draw.ellipse([x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius], fill=dot_color)
        return bg
    
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

def generate_pinterest_dashboard(items, output_html="pinterest_dashboard.html"):
    """Generates an HTML dashboard for rapid Pinterest uploading and copying."""
    html_cards = ""
    for item in items:
        html_cards += f"""
        <div class="card">
            <div class="preview">
                <img src="{item['pin_path']}" alt="{item['title']}">
                <span>{item['pin_filename']}</span>
            </div>
            <div class="fields">
                <div class="field-group">
                    <label>Suggested Board</label>
                    <div class="input-row">
                        <input type="text" readonly value="{item['board']}" id="board-{item['id']}">
                        <button onclick="copyToClipboard('board-{item['id']}', this)">Copy</button>
                    </div>
                </div>

                <div class="field-group">
                    <label>Pin Title</label>
                    <div class="input-row">
                        <input type="text" readonly value="{item['title']}" id="title-{item['id']}">
                        <button onclick="copyToClipboard('title-{item['id']}', this)">Copy</button>
                    </div>
                </div>

                <div class="field-group">
                    <label>Pin Description & Tags</label>
                    <div class="input-row">
                        <textarea readonly rows="4" id="desc-{item['id']}">{item['desc']}</textarea>
                        <button onclick="copyToClipboard('desc-{item['id']}', this)">Copy</button>
                    </div>
                </div>
            </div>
        </div>
        """

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Pinterest Upload Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #faf6f0; margin: 0; padding: 24px; color: #222; }}
        h1 {{ margin-bottom: 24px; font-size: 24px; color: #bd081c; }}
        .card {{ background: #fff; border-radius: 10px; padding: 20px; margin-bottom: 20px; display: flex; gap: 24px; box-shadow: 0 2px 5px rgba(0,0,0,0.06); }}
        .preview {{ width: 140px; text-align: center; flex-shrink: 0; }}
        .preview img {{ width: 140px; height: 210px; object-fit: cover; border-radius: 8px; border: 1px solid #e0dbd3; }}
        .preview span {{ display: block; font-size: 11px; color: #777; margin-top: 6px; word-break: break-all; }}
        .fields {{ flex-grow: 1; display: flex; flex-direction: column; gap: 12px; }}
        .field-group {{ display: flex; flex-direction: column; gap: 4px; }}
        label {{ font-size: 12px; font-weight: 700; text-transform: uppercase; color: #555; }}
        .input-row {{ display: flex; gap: 8px; }}
        input, textarea {{ flex-grow: 1; border: 1px solid #ddd; border-radius: 6px; padding: 8px 12px; font-size: 14px; background: #fafafa; color: #111; font-family: inherit; }}
        textarea {{ resize: none; }}
        button {{ background: #bd081c; color: white; border: none; border-radius: 6px; padding: 0 16px; font-weight: 600; cursor: pointer; transition: background 0.2s; white-space: nowrap; }}
        button:hover {{ background: #960616; }}
        button.copied {{ background: #2e7d32; }}
    </style>
</head>
<body>
    <h1>Pinterest Mockups & Metadata Dashboard</h1>
    {html_cards}
    <script>
        function copyToClipboard(elementId, btn) {{
            const el = document.getElementById(elementId);
            navigator.clipboard.writeText(el.value).then(() => {{
                const originalText = btn.innerText;
                btn.innerText = 'Copied!';
                btn.classList.add('copied');
                setTimeout(() => {{
                    btn.innerText = originalText;
                    btn.classList.remove('copied');
                }}, 1500);
            }});
        }}
    </script>
</body>
</html>"""

    with open(output_html, "w", encoding="utf-8") as f:
        f.write(full_html)

def generate_pinterest_pipeline(
    input_dir="exports",
    output_dir="pinterest_pins",
    output_csv="pinterest_listings.csv",
    output_html="pinterest_dashboard.html",
    pin_size=(1000, 1500),
    rotation_angle=-3.5
):
    os.makedirs(output_dir, exist_ok=True)
    sheet_files = sorted(glob.glob(os.path.join(input_dir, "*_sheet.png")))

    if not sheet_files:
        print(f"No sticker sheets found in '{input_dir}'.")
        return

    print(f"Generating Pinterest pins and metadata for {len(sheet_files)} designs...\n")

    csv_rows = [["Pin_Image", "Board", "Pin_Title", "Pin_Description", "Destination_Link_Note"]]
    dashboard_items = []

    for idx, sheet_path in enumerate(sheet_files, start=1):
        filename = os.path.basename(sheet_path)
        base_name = filename.replace("_sheet.png", "")

        # 1. Clean metadata string (strips digits and underscores)
        clean_name = re.sub(r"\d+", "", base_name)
        display_name = clean_name.replace("_", " ").replace("-", " ").strip()
        display_name = re.sub(r"\s+", " ", display_name).title()
        if not display_name:
            display_name = base_name.replace("_", " ").replace("-", " ").strip().title()

        # 2. Build Pinterest SEO Metadata
        pin_title = f"Minimalist {display_name} Bullet Journal Sticker Sheet | Aesthetic Bujo Deco"
        board_name = "Minimalist Planner Aesthetic"
        hashtag_tag = display_name.lower().replace(' ', '')
        pin_desc = (
            f"Keep your weekly spreads, reading logs, and habit trackers organized with this minimalist "
            f"black and white {display_name.lower()} sticker pack. Designed specifically for bullet journals, "
            f"student planners, and studygram spreads. Printed on clean matte paper. "
            f"#bulletjournal #bujoinspo #plannerstickers #studygram #functionalplanning #{hashtag_tag}sticker"
        )
        link_note = "Paste your exact Redbubble product URL here when uploading."

        # 3. Create Graphic Mockup
        raw_sheet = Image.open(sheet_path).convert("RGBA")
        target_w = 720
        scale = target_w / raw_sheet.width
        target_h = int(raw_sheet.height * scale)
        sheet_resized = raw_sheet.resize((target_w, target_h), Image.Resampling.LANCZOS)

        composite_item = build_physical_sheet(sheet_resized, margin=24, corner_radius=18)
        with_shadow = add_drop_shadow(composite_item, offset=(10, 18), blur_radius=20, shadow_alpha=75)
        rotated_item = with_shadow.rotate(rotation_angle, expand=True, resample=Image.BICUBIC)

        pin_bg = create_dot_grid_background(width=pin_size[0], height=pin_size[1], grid_angle=0)
        pos_x = (pin_size[0] - rotated_item.width) // 2
        pos_y = (pin_size[1] - rotated_item.height) // 2
        pin_bg.paste(rotated_item, (pos_x, pos_y), mask=rotated_item)

        pin_filename = f"{base_name}_pin.png"
        out_pin_path = os.path.join(output_dir, pin_filename)
        pin_bg.convert("RGB").save(out_pin_path, "PNG", quality=95)

        # 4. Save metadata records
        csv_rows.append([pin_filename, board_name, pin_title, pin_desc, link_note])
        dashboard_items.append({
            "id": idx,
            "pin_filename": pin_filename,
            "pin_path": f"{output_dir}/{pin_filename}",
            "board": board_name,
            "title": pin_title,
            "desc": pin_desc
        })

        print(f"[{idx}/{len(sheet_files)}] Generated: {pin_filename}")

    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(csv_rows)

    generate_pinterest_dashboard(dashboard_items, output_html)

    print(f"\nDone! Pinterest assets ready:")
    print(f"• Mockups saved in: '{output_dir}/'")
    print(f"• Visual Dashboard: '{output_html}'")
    print(f"• CSV Catalog:      '{output_csv}'")

if __name__ == "__main__":
    generate_pinterest_pipeline()