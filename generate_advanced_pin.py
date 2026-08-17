import numpy as np
from PIL import Image

def warp_sticker_to_page(sticker_img, bg_img, page_corners):
    """
    Warps a 2D sticker sheet to fit the 3D perspective of a notebook page.
    page_corners must be a list of 4 (x, y) tuples in this exact order:
    [Top-Left, Top-Right, Bottom-Right, Bottom-Left]
    """
    # 1. Get the 4 corners of the flat sticker sheet
    w, h = sticker_img.size
    source_corners = [(0, 0), (w, 0), (w, h), (0, h)]
    
    # 2. Calculate the Homography matrix (the 3D camera distortion math)
    matrix = []
    for s, d in zip(source_corners, page_corners):
        matrix.append([d[0], d[1], 1, 0, 0, 0, -s[0]*d[0], -s[0]*d[1]])
        matrix.append([0, 0, 0, d[0], d[1], 1, -s[1]*d[0], -s[1]*d[1]])
        
    A = np.matrix(matrix, dtype=float)
    B = np.array(source_corners).reshape(8)
    
    # Solve for the 8 perspective coefficients
    coeffs = np.array(np.dot(np.linalg.inv(A.T * A) * A.T, B)).reshape(8)
    
    # 3. Apply the 3D warp to the sticker sheet
    # We use Image.BICUBIC to ensure the text remains sharp during the distortion
    warped_sheet = sticker_img.transform(
        bg_img.size, 
        Image.PERSPECTIVE, 
        coeffs, 
        Image.BICUBIC
    )
    
    # 4. Composite the warped sheet onto the stock photo
    result = bg_img.copy().convert("RGBA")
    result.paste(warped_sheet, (0, 0), warped_sheet)
    
    return result

# ==========================================
# HOW TO USE IT IN YOUR PIPELINE
# ==========================================

# 1. Load your background stock photo
background = Image.open("templates/desk_mockup.jpg")

# 2. Load your generated sticker sheet
sticker_sheet = Image.open("output/mixed_pack_20260817.png")

# 3. Enter the 4 coordinates you found in MS Paint/Preview
# (Replace these numbers with the actual coordinates from your photo)
notebook_corners = [
    (150, 200),   # Top-Left corner of the paper
    (800, 250),   # Top-Right corner of the paper
    (850, 1300),  # Bottom-Right corner of the paper
    (100, 1250)   # Bottom-Left corner of the paper
]

# 4. Generate the photorealistic mockup
final_mockup = warp_sticker_to_page(sticker_sheet, background, notebook_corners)

# 5. Save the ready-to-post Pinterest Pin
final_mockup.convert("RGB").save("output/photorealistic_pin.jpg", quality=95)
print("Photorealistic Pinterest mockup generated!")