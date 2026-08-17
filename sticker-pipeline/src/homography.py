from typing import List, Tuple
import numpy as np
from PIL import Image, ImageChops


def warp_sticker_to_page(
    sticker_img: Image.Image,
    bg_img: Image.Image,
    page_corners: List[Tuple[int, int]],
    apply_multiply: bool = True
) -> Image.Image:
    """
    Warps a 2D sheet to fit 3D perspective coordinates:
    [Top-Left, Top-Right, Bottom-Right, Bottom-Left]
    """
    w, h = sticker_img.size
    source_corners = [(0, 0), (w, 0), (w, h), (0, h)]

    matrix = []
    for s, d in zip(source_corners, page_corners):
        matrix.append([d[0], d[1], 1, 0, 0, 0, -s[0] * d[0], -s[0] * d[1]])
        matrix.append([0, 0, 0, d[0], d[1], 1, -s[1] * d[0], -s[1] * d[1]])

    A = np.matrix(matrix, dtype=float)
    B = np.array(source_corners).reshape(8)

    coeffs = np.array(np.dot(np.linalg.inv(A.T * A) * A.T, B)).reshape(8)

    warped_sheet = sticker_img.transform(
        bg_img.size,
        Image.PERSPECTIVE,
        coeffs,
        Image.BICUBIC
    )

    bg_rgba = bg_img.convert("RGBA")

    if apply_multiply:
        # Multiply blending for realistic ink integration on textured paper
        multiply_layer = ImageChops.multiply(bg_rgba, warped_sheet)
        bg_rgba.paste(multiply_layer, (0, 0), mask=warped_sheet)
        return bg_rgba

    bg_rgba.paste(warped_sheet, (0, 0), mask=warped_sheet)
    return bg_rgba