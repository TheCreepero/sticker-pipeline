from typing import List
from PIL import Image
from src.image_ops import clean_alpha_channel, crop_visible, scale_to_bounding_box


def build_repeating_sheet(
    image_path: str,
    rows: int = 3,
    cols: int = 3,
    padding: int = 320,
    canvas_size: tuple = (3200, 3200),
    cell_fill_ratio: float = 0.85
) -> Image.Image:
    """Creates a grid sheet containing a single repeated design."""
    cell_w = (canvas_size[0] - (cols + 1) * padding) // cols
    cell_h = (canvas_size[1] - (rows + 1) * padding) // rows

    max_w = int(cell_w * cell_fill_ratio)
    max_h = int(cell_h * cell_fill_ratio)

    raw_img = Image.open(image_path)
    sticker = clean_alpha_channel(raw_img)
    sticker = crop_visible(sticker)
    sticker = scale_to_bounding_box(sticker, max_w, max_h)

    sheet = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    for r in range(rows):
        for c in range(cols):
            x = padding + c * (cell_w + padding) + (cell_w - sticker.width) // 2
            y = padding + r * (cell_h + padding) + (cell_h - sticker.height) // 2
            sheet.paste(sticker, (x, y), sticker)

    return sheet


def build_mixed_sheet(
    image_paths: List[str],
    cols: int = 3,
    max_rows: int = 6,
    padding: int = 320,
    canvas_size: tuple = (3200, 3200),
    cell_fill_ratio: float = 0.85
) -> Image.Image:
    """Creates a mixed sheet where each row contains 3 copies of a unique sticker."""
    cell_w = (canvas_size[0] - (cols + 1) * padding) // cols
    cell_h = (canvas_size[1] - (max_rows + 1) * padding) // max_rows

    max_w = int(cell_w * cell_fill_ratio)
    max_h = int(cell_h * cell_fill_ratio)

    sheet = Image.new("RGBA", canvas_size, (0, 0, 0, 0))

    for r, img_path in enumerate(image_paths[:max_rows]):
        raw_img = Image.open(img_path)
        sticker = clean_alpha_channel(raw_img)
        sticker = crop_visible(sticker)
        sticker = scale_to_bounding_box(sticker, max_w, max_h)

        for c in range(cols):
            x = padding + c * (cell_w + padding) + (cell_w - sticker.width) // 2
            y = padding + r * (cell_h + padding) + (cell_h - sticker.height) // 2
            sheet.paste(sticker, (x, y), sticker)

    return sheet