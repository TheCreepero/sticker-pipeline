import os, glob, csv

def generate_metadata_csv(input_dir="assets", output_csv="listings.csv"):
    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Filename", "Title", "Primary_Tag", "Tags", "Description"])

        for img_path in glob.glob(f"{input_dir}/*.png"):
            name = os.path.splitext(os.path.basename(img_path))[0].capitalize()
            
            title = f"Minimalist {name} Bullet Journal Sticker Sheet"
            primary_tag = f"{name.lower()} planner sticker"
            tags = f"{name.lower()} sticker, {name.lower()} planner sticker, bujo {name.lower()}, functional planner sticker, bullet journal aesthetic, habit tracker sticker, minimalist aesthetic sticker, black and white sticker, stationery addict"
            desc = f"Organize your routines with this minimalist black and white {name.lower()} sticker sheet. Perfect for habit trackers, weekly spreads, and bullet journal margins. Choose matte finish for a seamless look."

            writer.writerow([os.path.basename(img_path), title, primary_tag, tags, desc])

generate_metadata_csv()