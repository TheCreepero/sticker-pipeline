import os
import glob
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
    
    # 3. Apply the 3D warp to the sticker sheet using BICUBIC for sharp text
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

def batch_generate_photorealistic_pins(
    input_dir="output", 
    template_path="templates/desk_mockup.jpg",
    output_dir="output"
):
    # 1. Load the background stock photo once
    if not os.path.exists(template_path):
        print(f"Error: Could not find template at '{template_path}'.")
        print("Make sure you have a 'templates' folder with 'desk_mockup.jpg' inside it.")
        return
        
    background = Image.open(template_path)
    
    # 2. Define your 4 coordinates here
    # (Update these with the X, Y coordinates from your specific stock photo!)
    notebook_corners = [
        (2016, 1208),   # Top-Left
        (3009, 1181),   # Top-Right
        (3023, 2870),  # Bottom-Right
        (2009, 2908)   # Bottom-Left
    ]
    
    # 3. Find all Redbubble sheets in the output folder
    # We filter by 'mixed_pack_*.png' to avoid accidentally warping the digital pins or other files
    sheet_files = sorted(glob.glob(os.path.join(input_dir, "mixed_pack_*.png")))
    
    if not sheet_files:
        print(f"No sticker sheets found in '{input_dir}/'. Run your master pipeline first.")
        return
        
    print(f"Found {len(sheet_files)} sticker sheets. Generating photorealistic pins...\n")
    
    for idx, sheet_path in enumerate(sheet_files, start=1):
        filename = os.path.basename(sheet_path)
        base_name = os.path.splitext(filename)[0]
        
        # Load the generated transparent sticker sheet
        sticker_sheet = Image.open(sheet_path)
        
        # Apply the warp and composite
        final_mockup = warp_sticker_to_page(sticker_sheet, background, notebook_corners)
        
        # Save the finalized Pinterest Pin
        out_filename = f"photo_{base_name}.jpg"
        out_path = os.path.join(output_dir, out_filename)
        
        final_mockup.convert("RGB").save(out_path, quality=95)
        print(f"[{idx}/{len(sheet_files)}] Saved photorealistic pin: {out_filename}")
        
    print("\nSuccess! All photorealistic mockups are ready for Pinterest.")

if __name__ == "__main__":
    batch_generate_photorealistic_pins()