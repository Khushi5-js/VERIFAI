import os
from pathlib import Path
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter
from PIL.PngImagePlugin import PngInfo

TEST_DIR = Path(__file__).resolve().parent / "test_images"
TEST_DIR.mkdir(parents=True, exist_ok=True)


def create_authentic_canon_photo():
    """
    Simulate authentic camera photo:
    - High-frequency natural scenery with trees and sky
    - Realistic sensor noise (Gaussian + Poisson shot noise)
    - Full Canon EOS R5 camera EXIF metadata
    """
    path = TEST_DIR / "real_camera_canon_eos.jpg"
    w, h = 900, 600
    img_arr = np.zeros((h, w, 3), dtype=np.uint8)

    # Sky gradient
    for y in range(350):
        factor = y / 350.0
        img_arr[y, :] = [int(220 - 40 * factor), int(160 - 30 * factor), int(100 - 20 * factor)] # BGR

    # Mountain landscape with foliage
    for y in range(350, h):
        factor = (y - 350) / 250.0
        img_arr[y, :] = [int(40 + 20 * factor), int(70 + 40 * factor), int(30 + 15 * factor)]

    # Add realistic photographic camera sensor noise (ISO 400 grain)
    noise = np.random.normal(0, 5.5, (h, w, 3)).astype(np.float32)
    noisy_img = np.clip(img_arr.astype(np.float32) + noise, 0, 255).astype(np.uint8)

    # Convert to PIL and attach genuine EXIF tags
    pil_img = Image.fromarray(cv2.cvtColor(noisy_img, cv2.COLOR_BGR2RGB))
    exif = pil_img.getexif()
    exif[0x010F] = "Canon"                                     # Make
    exif[0x0110] = "Canon EOS R5"                              # Model
    exif[0x0131] = "Canon Digital Photo Professional 4.15"     # Software
    exif[0x0132] = "2026:07:15 14:32:01"                      # DateTime

    pil_img.save(path, "JPEG", quality=94, exif=exif)
    print(f"Created: {path.name}")


def create_authentic_iphone_photo():
    """
    Simulate smartphone photo:
    - Urban street perspective
    - Smartphone computational HDR noise pattern
    - Apple iPhone 15 Pro EXIF
    """
    path = TEST_DIR / "real_camera_iphone_15pro.jpg"
    w, h = 800, 600
    img_arr = np.zeros((h, w, 3), dtype=np.uint8)

    # Architectural building facade
    for x in range(w):
        val = int(120 + 40 * np.sin(x / 30.0))
        img_arr[:, x] = [val, val + 5, val + 15]

    # Sensor noise (iPhone ISO 64 fine grain)
    noise = np.random.normal(0, 3.2, (h, w, 3)).astype(np.float32)
    noisy_img = np.clip(img_arr.astype(np.float32) + noise, 0, 255).astype(np.uint8)

    pil_img = Image.fromarray(cv2.cvtColor(noisy_img, cv2.COLOR_BGR2RGB))
    exif = pil_img.getexif()
    exif[0x010F] = "Apple"
    exif[0x0110] = "iPhone 15 Pro"
    exif[0x0131] = "iOS 17.5.1"
    exif[0x0132] = "2026:08:20 18:10:45"

    pil_img.save(path, "JPEG", quality=92, exif=exif)
    print(f"Created: {path.name}")


def create_edited_spliced_composite():
    """
    Simulate spliced composite forgery:
    - Base photo at quality 92
    - Spliced patch taken from a heavily compressed image (quality 30) with different noise floor
    - Photoshop EXIF software signature and timestamp discordance
    """
    path = TEST_DIR / "edited_spliced_composite.jpg"
    w, h = 900, 600
    
    # Base background: smooth room wall with fine noise
    base = np.full((h, w, 3), 140, dtype=np.uint8)
    base_noise = np.random.normal(0, 4.0, (h, w, 3)).astype(np.float32)
    base = np.clip(base.astype(np.float32) + base_noise, 0, 255).astype(np.uint8)
    
    # Spliced foreground element: distinct high-contrast object with severe JPEG blocking artifacts
    patch_w, patch_h = 320, 220
    patch = np.zeros((patch_h, patch_w, 3), dtype=np.uint8)
    cv2.circle(patch, (160, 110), 80, (230, 50, 40), -1) # Red circle
    cv2.putText(patch, "INSERTED", (60, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
    
    # Compress patch heavily
    _, enc = cv2.imencode(".jpg", patch, [int(cv2.IMWRITE_JPEG_QUALITY), 25])
    patch_comp = cv2.imdecode(enc, cv2.IMREAD_COLOR)

    # Splice onto base at (280, 180)
    base[180:180+patch_h, 280:280+patch_w] = patch_comp

    pil_img = Image.fromarray(cv2.cvtColor(base, cv2.COLOR_BGR2RGB))
    exif = pil_img.getexif()
    exif[0x010F] = "Nikon"
    exif[0x0110] = "NIKON Z8"
    exif[0x0131] = "Adobe Photoshop 2026 (Windows)"
    exif[0x0132] = "2026:09:11 11:20:00" # Mod date differs from capture

    pil_img.save(path, "JPEG", quality=88, exif=exif)
    print(f"Created: {path.name}")


def create_ai_midjourney_style():
    """
    Simulate Midjourney v6 output:
    - Painterly, hyper-smooth micro-textures without natural ISO noise
    - Specular micro-lighting highlights
    - Clean PNG with zero camera EXIF
    """
    path = TEST_DIR / "ai_midjourney_portrait.png"
    w, h = 800, 600
    img = np.zeros((h, w, 3), dtype=np.float32)

    # Ultra-smooth stylized gradient lighting
    for y in range(h):
        for x in range(w):
            val = 0.5 + 0.3 * np.sin(x / 90.0) * np.cos(y / 110.0)
            img[y, x] = [val * 210, val * 160, val * 120]

    # Distinctive Midjourney-style hyper-contrast glowing rings
    cv2.circle(img, (400, 280), 160, (255, 220, 180), 4)
    cv2.circle(img, (400, 280), 70, (240, 180, 130), -1)
    
    # Gaussian blur to simulate diffusion airbrushing (eliminating camera sensor grain)
    img_blurred = cv2.GaussianBlur(img, (7, 7), 2.5)
    img_uint = np.clip(img_blurred, 0, 255).astype(np.uint8)

    pil_img = Image.fromarray(cv2.cvtColor(img_uint, cv2.COLOR_BGR2RGB))
    # No EXIF attached - characteristic of web-downloaded AI art
    pil_img.save(path, "PNG")
    print(f"Created: {path.name}")


def create_ai_dalle_style():
    """
    Simulate DALL-E 3 output:
    - Distinctive vibrant pastel saturation
    - Symmetrical surreal geometry
    - Plastic smooth shading, zero sensor shot noise
    """
    path = TEST_DIR / "ai_dalle3_surreal.png"
    w, h = 800, 600
    img = np.zeros((h, w, 3), dtype=np.uint8)

    # Vibrant dreamscape colors
    for y in range(h):
        r = int(180 + 70 * np.cos(y / 80.0))
        g = int(120 + 60 * np.sin(y / 90.0))
        b = int(210 + 40 * np.sin(y / 60.0))
        img[y, :] = [b, g, r]

    # Perfect floating geometric spheres with plastic specular sheen
    cv2.circle(img, (400, 300), 110, (255, 230, 240), -1)
    cv2.circle(img, (370, 270), 30, (255, 255, 255), -1) # Specular sheen

    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    pil_img.save(path, "PNG")
    print(f"Created: {path.name}")


def create_ai_stablediffusion_style():
    """
    Simulate Stable Diffusion XL output:
    - Complex recursive patterns with slight structural distortions
    - PNG with generative prompt parameters in tEXt chunk
    """
    path = TEST_DIR / "ai_stablediffusion_xl.png"
    w, h = 800, 600
    img = np.zeros((h, w, 3), dtype=np.uint8)

    # Radial frequency wave patterns
    center_x, center_y = 400, 300
    Y, X = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
    pattern = (np.sin(dist_from_center / 12.0) * 127 + 128).astype(np.uint8)
    
    img[:, :, 0] = pattern
    img[:, :, 1] = np.roll(pattern, 20, axis=0)
    img[:, :, 2] = np.roll(pattern, 40, axis=1)

    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    
    # Embedded SD parameters
    meta = PngInfo()
    meta.add_text("parameters", "cybernetic mechanical heart, octane render, unreal engine 5, 8k, photorealistic\nNegative prompt: cartoon, 3d, sketch\nSteps: 30, Sampler: DPM++ 2M Karras, CFG scale: 7, Seed: 3948271048")
    
    pil_img.save(path, "PNG", pnginfo=meta)
    print(f"Created: {path.name}")


if __name__ == "__main__":
    create_authentic_canon_photo()
    create_authentic_iphone_photo()
    create_edited_spliced_composite()
    create_ai_midjourney_style()
    create_ai_dalle_style()
    create_ai_stablediffusion_style()
