import sys
from PIL import Image

def create_repeating_sheet(
    image_path="sticker.png",
    output_path="repeating_sheet.png",
    rows=3,
    cols=3,
    canvas_size=(3200, 3200),
    padding=80,
):
    """
    Tiles a single transparent PNG sticker across a grid on a single sheet.
    """
    try:
        sticker = Image.open(image_path).convert("RGBA")
    except FileNotFoundError:
        print(f"Error: Could not find image '{image_path}'.")
        return

    # Calculate max dimension per cell accounting for spacing
    cell_w = (canvas_size[0] - (cols + 1) * padding) // cols
    cell_h = (canvas_size[1] - (rows + 1) * padding) // rows

    # Scale the sticker to fit within the cell maintaining aspect ratio
    sticker.thumbnail((cell_w, cell_h), Image.Resampling.LANCZOS)

    sheet = Image.new("RGBA", canvas_size, (0, 0, 0, 0))

    # Tile the single image across every row and column
    for r in range(rows):
        for c in range(cols):
            x = padding + c * (cell_w + padding) + (cell_w - sticker.width) // 2
            y = padding + r * (cell_h + padding) + (cell_h - sticker.height) // 2
            sheet.paste(sticker, (x, y), sticker)

    sheet.save(output_path, "PNG")
    print(f"Created '{output_path}' with {rows * cols} repeating stickers ({rows}x{cols} grid).")

if __name__ == "__main__":
    img_in = sys.argv[1] if len(sys.argv) > 1 else "study.png"
    img_out = sys.argv[2] if len(sys.argv) > 2 else "study_sheet.png"
    
    # Adjust rows and cols as desired (e.g., rows=4, cols=3 for 12 stickers)
    create_repeating_sheet(
        image_path=img_in,
        output_path=img_out,
        rows=3,
        cols=3,
        padding=80
    )