import numpy as np
from PIL import ImageFont
from PIL import Image, ImageDraw, ImageFilter


def clean_alpha_channel(img: Image.Image, threshold: int = 35) -> Image.Image:
    """Strips invisible anti-aliasing artifacts to prevent cutline merging on Redbubble."""
    img = img.convert("RGBA")
    r, g, b, a = img.split()
    a = a.point(lambda p: p if p > threshold else 0)
    img.putalpha(a)
    return img


def crop_visible(img: Image.Image) -> Image.Image:
    """Crops transparent borders around artwork."""
    bbox = img.getbbox()
    return img.crop(bbox) if bbox else img


def scale_to_bounding_box(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
    """Scales image proportionally to fill a bounding box."""
    scale = min(max_w / img.width, max_h / img.height)
    new_w = max(1, int(img.width * scale))
    new_h = max(1, int(img.height * scale))
    return img.resize((new_w, new_h), Image.Resampling.LANCZOS)


def build_physical_sheet(
    sticker_img: Image.Image,
    margin: int = 24,
    corner_radius: int = 18,
    card_color: tuple = (255, 255, 255, 255)
) -> Image.Image:
    """Wraps transparent sticker grids in a rounded matte backing."""
    w = sticker_img.width + margin * 2
    h = sticker_img.height + margin * 2
    sheet_card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(sheet_card)
    draw.rounded_rectangle([0, 0, w, h], radius=corner_radius, fill=card_color)
    sheet_card.paste(sticker_img, (margin, margin), mask=sticker_img)
    return sheet_card


def add_drop_shadow(
    image: Image.Image,
    offset: tuple = (10, 18),
    blur_radius: int = 20,
    shadow_alpha: int = 75
) -> Image.Image:
    """Adds a Gaussian blur drop shadow underneath the image."""
    shadow_w = image.width + blur_radius * 4
    shadow_h = image.height + blur_radius * 4
    shadow = Image.new("RGBA", (shadow_w, shadow_h), (0, 0, 0, 0))

    mask = image.split()[3]
    shadow_base = Image.new("RGBA", image.size, (20, 20, 20, shadow_alpha))
    shadow.paste(shadow_base, (blur_radius * 2 + offset[0], blur_radius * 2 + offset[1]), mask=mask)

    shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))
    shadow.paste(image, (blur_radius * 2, blur_radius * 2), mask=image)
    return shadow


def create_dot_grid_background(
    width: int = 1000,
    height: int = 1500,
    dot_spacing: int = 40,
    dot_radius: int = 2,
    bg_color: str = "#f8f6f0",
    dot_color: str = "#ded9cf",
    grid_angle: float = 0.0
) -> Image.Image:
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

def add_cta_badge(
    image: Image.Image,
    text: str = "Shop on Redbubble",
    bg_color: tuple = (227, 20, 33, 255),  # Redbubble Red
    text_color: tuple = (255, 255, 255, 255)
) -> Image.Image:
    """Overlays a clean, pill-shaped Call-To-Action badge on the bottom-left."""
    draw = ImageDraw.Draw(image, "RGBA")
    
    # Dynamically scale sizes based on the background image resolution
    base_scale = image.width
    font_size = max(24, int(base_scale * 0.03))  # ~3.0% of image width
    padding_x = int(base_scale * 0.035)            # ~4% of image width
    padding_y = int(base_scale * 0.012)           # ~1.2% of image width
    margin = int(image.width * 0.04)              # ~5% margin from the edges
    
    # Attempt to load Arial Bold, fallback to default if missing
    try:
        font = ImageFont.truetype("arialbd.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()
    
    # Calculate text dimensions
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    badge_w = text_w + padding_x * 2
    badge_h = text_h + padding_y * 2
    
    # --- NEW POSITIONING: Bottom-Left Corner ---
    x = margin
    y = image.height - badge_h - margin
    
    # --- NEW DROP SHADOW ---
    shadow_offset = max(2, int(base_scale * 0.005))
    draw.rounded_rectangle(
        [x + shadow_offset, y + shadow_offset, x + badge_w + shadow_offset, y + badge_h + shadow_offset],
        radius=badge_h // 2,
        fill=(0, 0, 0, 90) # Semi-transparent black shadow
    )
    
    # Draw the pill-shaped background
    draw.rounded_rectangle(
        [x, y, x + badge_w, y + badge_h],
        radius=badge_h // 2,
        fill=bg_color
    )
    
    # Draw the text perfectly centered inside the pill
    text_x = x + padding_x
    text_y = y + padding_y - bbox[1]
    draw.text((text_x, text_y), text, font=font, fill=text_color)
    
    return image
