import csv
import glob
import os
import re
import sys
from PIL import Image

def print_progress(current, total, filename="", bar_length=25):
    """Renders a dynamic command-line progress bar."""
    fraction = current / total if total > 0 else 1
    filled = int(bar_length * fraction)
    bar = "█" * filled + "░" * (bar_length - filled)
    percent = int(fraction * 100)
    sys.stdout.write(f"\r[{bar}] {current}/{total} ({percent}%)  Processing: {filename[:25]:<25}")
    sys.stdout.flush()

def clean_alpha_channel(img, threshold=35):
    """
    Strips invisible anti-aliasing ghosts and compression noise 
    that cause Redbubble cutlines to bridge across gaps.
    """
    img = img.convert("RGBA")
    r, g, b, a = img.split()
    # Zero out any pixel with alpha below the threshold
    a = a.point(lambda p: p if p > threshold else 0)
    img.putalpha(a)
    return img

def generate_html_dashboard(items, output_html="listings.html"):
    """Generates an HTML dashboard with one-click copy buttons."""
    html_cards = ""
    for item in items:
        html_cards += f"""
        <div class="card">
            <div class="preview">
                <img src="exports/{item['filename']}" alt="{item['title']}">
                <span>{item['filename']}</span>
            </div>
            <div class="fields">
                <div class="field-group">
                    <label>Title</label>
                    <div class="input-row">
                        <input type="text" readonly value="{item['title']}" id="title-{item['id']}">
                        <button onclick="copyToClipboard('title-{item['id']}', this)">Copy</button>
                    </div>
                </div>

                <div class="field-group">
                    <label>Primary Tag</label>
                    <div class="input-row">
                        <input type="text" readonly value="{item['primary_tag']}" id="ptag-{item['id']}">
                        <button onclick="copyToClipboard('ptag-{item['id']}', this)">Copy</button>
                    </div>
                </div>

                <div class="field-group">
                    <label>Tags (Comma-Separated)</label>
                    <div class="input-row">
                        <textarea readonly rows="2" id="tags-{item['id']}">{item['tags']}</textarea>
                        <button onclick="copyToClipboard('tags-{item['id']}', this)">Copy</button>
                    </div>
                </div>

                <div class="field-group">
                    <label>Description</label>
                    <div class="input-row">
                        <textarea readonly rows="3" id="desc-{item['id']}">{item['desc']}</textarea>
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
    <title>Sticker Upload Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f4f5f7; margin: 0; padding: 24px; color: #172b4d; }}
        h1 {{ margin-bottom: 24px; font-size: 24px; }}
        .card {{ background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 20px; display: flex; gap: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .preview {{ width: 180px; text-align: center; flex-shrink: 0; }}
        .preview img {{ width: 160px; height: 160px; object-fit: contain; border: 1px dashed #ccc; border-radius: 6px; background: #fafafa; }}
        .preview span {{ display: block; font-size: 12px; color: #6b778c; margin-top: 6px; word-break: break-all; }}
        .fields {{ flex-grow: 1; display: flex; flex-direction: column; gap: 12px; }}
        .field-group {{ display: flex; flex-direction: column; gap: 4px; }}
        label {{ font-size: 12px; font-weight: 600; text-transform: uppercase; color: #5e6c84; }}
        .input-row {{ display: flex; gap: 8px; }}
        input, textarea {{ flex-grow: 1; border: 1px solid #dfe1e6; border-radius: 4px; padding: 8px; font-size: 14px; background: #fafbfc; color: #091e42; font-family: inherit; }}
        textarea {{ resize: none; }}
        button {{ background: #0052cc; color: white; border: none; border-radius: 4px; padding: 0 16px; font-weight: 600; cursor: pointer; transition: background 0.2s; white-space: nowrap; }}
        button:hover {{ background: #0747a6; }}
        button.copied {{ background: #36b37e; }}
    </style>
</head>
<body>
    <h1>Sticker Metadata & Copy Dashboard</h1>
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

def run_full_pipeline(
    input_dir="assets",
    output_dir="exports",
    output_csv="listings.csv",
    output_txt="listings.txt",
    output_html="listings.html",
    rows=4,
    cols=3,
    padding=320,
    canvas_size=(3200, 3200)
):
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    png_files = sorted(glob.glob(os.path.join(input_dir, "*.png")))
    total_files = len(png_files)
    if total_files == 0:
        print(f"No PNG files found in '{input_dir}' folder.")
        return

    print(f"Starting batch build for {total_files} designs with wide cutline padding...\n")

    # Calculate individual cell limits
    cell_w = (canvas_size[0] - (cols + 1) * padding) // cols
    cell_h = (canvas_size[1] - (rows + 1) * padding) // rows

    # Enforce safe internal boundary (85% of cell size)
    max_target_w = int(cell_w * 0.75)
    max_target_h = int(cell_h * 0.75)

    csv_rows = [["Filename", "Title", "Primary_Tag", "Tags", "Description"]]
    items_data = []
    txt_blocks = []

    for idx, img_path in enumerate(png_files, start=1):
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        
        # Terminal Progress
        print_progress(idx, total_files, filename=f"{base_name}.png")

        # Clean metadata strings
        clean_name = re.sub(r"\d+", "", base_name)
        display_name = clean_name.replace("_", " ").replace("-", " ").strip()
        display_name = re.sub(r"\s+", " ", display_name).title()
        if not display_name:
            display_name = base_name.replace("_", " ").replace("-", " ").strip().title()

        # 1. Clean alpha noise
        raw_img = Image.open(img_path)
        sticker = clean_alpha_channel(raw_img, threshold=35)

        # 2. Crop tightly to visible pixels
        bbox = sticker.getbbox()
        if bbox:
            sticker = sticker.crop(bbox)

        # 3. Proportional scale into safe bounding box
        scale = min(max_target_w / sticker.width, max_target_h / sticker.height)
        new_w = max(1, int(sticker.width * scale))
        new_h = max(1, int(sticker.height * scale))
        sticker = sticker.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # 4. Composite onto transparent canvas
        sheet = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        for r in range(rows):
            for c in range(cols):
                x = padding + c * (cell_w + padding) + (cell_w - sticker.width) // 2
                y = padding + r * (cell_h + padding) + (cell_h - sticker.height) // 2
                sheet.paste(sticker, (x, y), sticker)

        export_filename = f"{base_name}_sheet.png"
        sheet.save(os.path.join(output_dir, export_filename), "PNG")

        # 5. Metadata generation
        title = f"Minimalist {display_name} Bullet Journal Sticker Sheet"
        primary_tag = f"{display_name.lower()} planner sticker"
        tags = (
            f"{display_name.lower()} sticker, {display_name.lower()} planner sticker, "
            f"bujo {display_name.lower()}, functional planner sticker, bullet journal aesthetic, "
            f"habit tracker sticker, minimalist aesthetic sticker, black and white sticker, stationery addict"
        )
        desc = (
            f"Organize your routines with this minimalist black and white {display_name.lower()} sticker sheet. "
            f"Perfect for habit trackers, weekly spreads, and bullet journal margins. "
            f"Choose the matte finish for a seamless look."
        )

        csv_rows.append([export_filename, title, primary_tag, tags, desc])
        items_data.append({
            "id": idx,
            "filename": export_filename,
            "title": title,
            "primary_tag": primary_tag,
            "tags": tags,
            "desc": desc
        })

        txt_blocks.append(
            f"==================================================\n"
            f"FILE: {export_filename}\n"
            f"==================================================\n"
            f"TITLE:\n{title}\n\n"
            f"PRIMARY TAG:\n{primary_tag}\n\n"
            f"TAGS:\n{tags}\n\n"
            f"DESCRIPTION:\n{desc}\n\n"
        )

    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(csv_rows)

    with open(output_txt, mode="w", encoding="utf-8") as f:
        f.writelines(txt_blocks)

    generate_html_dashboard(items_data, output_html)

    print("\n\nPipeline complete!")
    print(f"• Generated cutline-isolated sticker sheets in '{output_dir}/'")

if __name__ == "__main__":
    run_full_pipeline()