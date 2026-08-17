import csv
import os
import re
from typing import Dict, List


def extract_clean_name(filename: str) -> str:
    """Strips digits, prefixes, trailing separators, and normalizes spacing."""
    base = os.path.splitext(os.path.basename(filename))[0]
    clean = re.sub(r"\d+", "", base)
    display_name = clean.replace("_", " ").replace("-", " ").strip()
    display_name = re.sub(r"\s+", " ", display_name).title()
    return display_name if display_name else base.title()


def build_seo_metadata(names: List[str], is_mixed: bool = False) -> Dict[str, str]:
    """Generates optimized listings for Redbubble and Pinterest."""
    if is_mixed:
        display_title = ", ".join(names[:2])
        if len(names) > 2:
            display_title += f" & {names[2]}"

        rb_title = f"Minimalist {display_title} Bullet Journal Sticker Pack"
        rb_ptag = f"{names[0].lower()} planner sticker"
        specific_tags = [f"{name.lower()} sticker" for name in names[:4]]
        core_tags = [
            "bujo typography", "functional planner sticker", "bullet journal aesthetic",
            "habit tracker sticker", "minimalist aesthetic sticker", "black and white sticker",
            "stationery addict"
        ]
        rb_tags = ", ".join(specific_tags + core_tags)
        rb_desc = (
            f"Organize your routines with this minimalist functional sticker pack featuring "
            f"{', '.join(name.lower() for name in names[:4])} and more. Perfect for habit trackers, "
            f"weekly spreads, and bullet journal layouts. Choose the matte finish for a seamless look."
        )

        pin_title = f"Minimalist {display_title} Sticker Pack | Aesthetic Bujo Deco"
        hashtag_tag = names[0].lower().replace(" ", "")
        pin_desc = (
            f"Keep your spreads and habit trackers organized with this minimalist "
            f"{display_title} sticker pack. Designed for bullet journals and planners. "
            f"#bulletjournal #bujoinspo #plannerstickers #studygram #functionalplanning #{hashtag_tag}sticker"
        )
    else:
        name = names[0]
        rb_title = f"Minimalist {name} Bullet Journal Sticker Sheet"
        rb_ptag = f"{name.lower()} planner sticker"
        rb_tags = (
            f"{name.lower()} sticker, {name.lower()} planner sticker, "
            f"bujo {name.lower()}, functional planner sticker, bullet journal aesthetic, "
            f"habit tracker sticker, minimalist aesthetic sticker, black and white sticker, stationery addict"
        )
        rb_desc = (
            f"Organize your routines with this minimalist black and white {name.lower()} sticker sheet. "
            f"Perfect for habit trackers, weekly spreads, and bullet journal margins. "
            f"Choose the matte finish for a seamless look."
        )

        pin_title = f"Minimalist {name} Bullet Journal Sticker Sheet | Aesthetic Bujo Deco"
        hashtag_tag = name.lower().replace(" ", "")
        pin_desc = (
            f"Keep your weekly spreads, reading logs, and habit trackers organized with this minimalist "
            f"{name.lower()} sticker pack. Printed on clean matte paper. "
            f"#bulletjournal #bujoinspo #plannerstickers #studygram #functionalplanning #{hashtag_tag}sticker"
        )

    return {
        "rb_title": rb_title,
        "rb_ptag": rb_ptag,
        "rb_tags": rb_tags,
        "rb_desc": rb_desc,
        "pin_title": pin_title,
        "pin_desc": pin_desc
    }


def save_csv(data_rows: List[List[str]], output_path: str):
    """Saves CSV with semicolon delimiters and UTF-8-SIG for European Excel compatibility."""
    with open(output_path, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerows(data_rows)


def generate_unified_html(items: List[Dict], output_html: str):
    """Generates an interactive web dashboard with one-click copy buttons."""
    html_cards = ""
    for item in items:
        html_cards += f"""
        <div class="card">
            <div class="preview-section">
                <div class="preview">
                    <strong>Redbubble Sheet</strong>
                    <img src="{item['rb_filename']}" alt="Sheet preview" style="object-fit: contain;">
                    <span>{item['rb_filename']}</span>
                </div>
                <div class="preview">
                    <strong>Pinterest Pin</strong>
                    <img src="{item['pin_filename']}" alt="Pin preview" style="object-fit: cover;">
                    <span>{item['pin_filename']}</span>
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
                        <label>Tags</label>
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
    <title>Sticker Metadata Dashboard</title>
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
    <h1>Sticker Production & Promotion Dashboard</h1>
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