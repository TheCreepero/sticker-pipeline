import os, glob
from PIL import Image

def batch_process_repeats(input_dir="assets", output_dir="exports_repeating", rows=3, cols=3, padding=80, canvas_size=(3200, 3200)):
    os.makedirs(output_dir, exist_ok=True)
    cell_w = (canvas_size[0] - (cols + 1) * padding) // cols
    cell_h = (canvas_size[1] - (rows + 1) * padding) // rows

    for img_path in glob.glob(f"{input_dir}/*.png"):
        name = os.path.splitext(os.path.basename(img_path))[0]
        sticker = Image.open(img_path).convert("RGBA")
        sticker.thumbnail((cell_w, cell_h), Image.Resampling.LANCZOS)
        
        sheet = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        for r in range(rows):
            for c in range(cols):
                x = padding + c * (cell_w + padding) + (cell_w - sticker.width) // 2
                y = padding + r * (cell_h + padding) + (cell_h - sticker.height) // 2
                sheet.paste(sticker, (x, y), sticker)
        
        sheet.save(os.path.join(output_dir, f"{name}_sheet.png"), "PNG")

# Runs all PNGs in the assets folder at once
batch_process_repeats()