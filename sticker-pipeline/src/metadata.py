import csv
import json
import os
import re
import urllib.parse
from typing import Dict, List, Tuple


DEFAULT_PROFILES = {
    "Minimalist Bujo": {
        "rb_title_single": "Minimalist {name} Bullet Journal Sticker Sheet",
        "rb_title_mixed": "Minimalist {display_title} Bullet Journal Sticker Pack",
        "rb_ptag": "{first_name} planner sticker",
        "rb_tags_core": [
            "bujo typography", "functional planner sticker", "bullet journal aesthetic",
            "habit tracker sticker", "minimalist aesthetic sticker", "black and white sticker",
            "stationery addict"
        ],
        "rb_desc_single": "Organize your routines with this minimalist black and white {name_lower} sticker sheet. Perfect for habit trackers, weekly spreads, and bullet journal margins. Choose the matte finish for a seamless look.",
        "rb_desc_mixed": "Organize your routines with this minimalist functional sticker pack featuring {sample_names} and more. Perfect for habit trackers, weekly spreads, and bullet journal layouts. Choose the matte finish for a seamless look.",
        "pin_title_single": "Minimalist {name} Bullet Journal Sticker Sheet | Aesthetic Bujo Deco",
        "pin_title_mixed": "Minimalist {display_title} Sticker Pack | Aesthetic Bujo Deco",
        "pin_desc_single": "Keep your weekly spreads, reading logs, and habit trackers organized with this minimalist {name_lower} sticker pack. Printed on clean matte paper. #bulletjournal #bujoinspo #plannerstickers #studygram #functionalplanning #{hashtag}sticker",
        "pin_desc_mixed": "Keep your spreads and habit trackers organized with this minimalist {display_title} sticker pack. Designed for bullet journals and planners. #bulletjournal #bujoinspo #plannerstickers #studygram #functionalplanning #{hashtag}sticker"
    }
}


def load_seo_profiles(config_path: str = "config/seo_profiles.json") -> Dict[str, dict]:
    """Loads custom SEO profile definitions from JSON with fallback."""
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_PROFILES


def extract_clean_name(filename: str) -> str:
    """Strips digits, prefixes, trailing separators, and normalizes spacing."""
    base = os.path.splitext(os.path.basename(filename))[0]
    clean = re.sub(r"\d+", "", base)
    display_name = clean.replace("_", " ").replace("-", " ").strip()
    display_name = re.sub(r"\s+", " ", display_name).title()
    return display_name if display_name else base.title()


def build_seo_metadata(
    names: List[str], 
    is_mixed: bool = False, 
    profile_name: str = "Minimalist Bujo",
    profiles: dict = None
) -> Dict[str, str]:
    """Generates SEO metadata mapped through the selected thematic profile template."""
    if profiles is None:
        profiles = load_seo_profiles()

    profile = profiles.get(profile_name, list(profiles.values())[0] if profiles else DEFAULT_PROFILES["Minimalist Bujo"])

    first_name = names[0].lower()
    hashtag = first_name.replace(" ", "")
    sample_names = ", ".join(n.lower() for n in names[:4])

    if is_mixed:
        display_title = ", ".join(names[:2])
        if len(names) > 2:
            display_title += f" & {names[2]}"

        template_ctx = {
            "display_title": display_title,
            "first_name": first_name,
            "sample_names": sample_names,
            "hashtag": hashtag
        }

        rb_title = profile.get("rb_title_mixed", "Sticker Pack {display_title}").format(**template_ctx)
        rb_ptag = profile.get("rb_ptag", "{first_name} planner sticker").format(**template_ctx)

        specific_tags = [f"{name.lower()} sticker" for name in names[:4]]
        core_tags = profile.get("rb_tags_core", [])
        rb_tags = ", ".join(specific_tags + core_tags)

        rb_desc = profile.get("rb_desc_mixed", "Sticker pack featuring {sample_names}.").format(**template_ctx)
        pin_title = profile.get("pin_title_mixed", "{display_title} Sticker Pack").format(**template_ctx)
        pin_desc = profile.get("pin_desc_mixed", "Sticker pack {display_title} #{hashtag}sticker").format(**template_ctx)
    else:
        name = names[0]
        template_ctx = {
            "name": name,
            "name_lower": name.lower(),
            "first_name": first_name,
            "hashtag": hashtag
        }

        rb_title = profile.get("rb_title_single", "{name} Sticker Sheet").format(**template_ctx)
        rb_ptag = profile.get("rb_ptag", "{first_name} planner sticker").format(**template_ctx)

        specific_tags = [f"{name.lower()} sticker", f"{name.lower()} planner sticker", f"bujo {name.lower()}"]
        core_tags = profile.get("rb_tags_core", [])
        rb_tags = ", ".join(specific_tags + core_tags)

        rb_desc = profile.get("rb_desc_single", "{name} sticker sheet.").format(**template_ctx)
        pin_title = profile.get("pin_title_single", "{name} Sticker Sheet").format(**template_ctx)
        pin_desc = profile.get("pin_desc_single", "{name} sticker sheet #{hashtag}sticker").format(**template_ctx)

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


def load_existing_metadata(csv_path: str) -> Tuple[List[List[str]], List[Dict]]:
    """Loads existing CSV data to prevent overwriting the dashboard on new runs."""
    csv_rows = []
    dashboard_items = []
    
    if os.path.exists(csv_path):
        with open(csv_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f, delimiter=";")
            headers = next(reader, None)
            if headers:
                csv_rows.append(headers)
                for idx, row in enumerate(reader):
                    if len(row) >= 9:
                        csv_rows.append(row)
                        adv_pins = row[6].split("|") if row[6] else []
                        dashboard_items.append({
                            "id": f"prev_{idx}",
                            "rb_filepath": row[0],
                            "rb_title": row[1],
                            "rb_ptag": row[2],
                            "rb_tags": row[3],
                            "rb_desc": row[4],
                            "simple_pin_filepath": row[5],
                            "adv_pin_filepaths": adv_pins,
                            "pin_title": row[7],
                            "pin_desc": row[8]
                        })
    else:
        csv_rows = [[
            "RB_Filepath", "RB_Title", "RB_Primary_Tag", "RB_Tags", "RB_Description",
            "Simple_Pin_Filepath", "Advanced_Pin_Filepaths", "Pin_Title", "Pin_Description"
        ]]
        
    return csv_rows, dashboard_items


def generate_unified_html(items: List[Dict], output_html: str):
    """Generates an interactive web dashboard with 3-way visual previews and copy buttons."""
    html_cards = ""
    for item in items:
        adv_previews = ""
        for adv_pin in item.get("adv_pin_filepaths", []):
            if adv_pin:
                safe_path = urllib.parse.quote(adv_pin, safe="/")
                adv_previews += f"""
                <div class="preview">
                    <strong>Advanced Mockup</strong>
                    <img src="{safe_path}" alt="Photo mockup" style="object-fit: cover;">
                    <span>{os.path.basename(adv_pin)}</span>
                </div>
                """

        simple_preview = ""
        if item.get("simple_pin_filepath"):
            safe_path = urllib.parse.quote(item['simple_pin_filepath'], safe="/")
            simple_preview = f"""
            <div class="preview">
                <strong>Dot Grid Pin</strong>
                <img src="{safe_path}" alt="Simple pin preview" style="object-fit: cover;">
                <span>{os.path.basename(item['simple_pin_filepath'])}</span>
            </div>
            """

        sheet_preview = ""
        if item.get("rb_filepath"):
            safe_path = urllib.parse.quote(item['rb_filepath'], safe="/")
            sheet_preview = f"""
            <div class="preview">
                <strong>Redbubble Sheet</strong>
                <img src="{safe_path}" alt="Sheet preview" style="object-fit: contain;">
                <span>{os.path.basename(item['rb_filepath'])}</span>
            </div>
            """

        html_cards += f"""
        <div class="card">
            <div class="preview-section">
                {sheet_preview}
                {simple_preview}
                {adv_previews}
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
    <title>Sticker Production Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f4f5f7; margin: 0; padding: 24px; color: #172b4d; }}
        h1 {{ margin-bottom: 24px; font-size: 24px; }}
        .card {{ background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 30px; display: flex; flex-direction: column; gap: 24px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }}
        .preview-section {{ display: flex; gap: 20px; padding-bottom: 20px; border-bottom: 1px solid #ebecf0; flex-wrap: wrap; }}
        .preview {{ display: flex; flex-direction: column; align-items: center; gap: 8px; font-size: 13px; color: #5e6c84; }}
        .preview img {{ width: 170px; height: 230px; border: 1px dashed #ccc; border-radius: 6px; background: #fafafa; }}
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