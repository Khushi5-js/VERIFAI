import os
from pathlib import Path
from PIL import Image, ImageDraw
from PIL.PngImagePlugin import PngInfo

DEMO_DIR = Path(__file__).resolve().parent / "demo_files"
DEMO_DIR.mkdir(parents=True, exist_ok=True)


def create_authentic_sample():
    """Create a realistic clean photograph with authentic camera EXIF."""
    path = DEMO_DIR / "demo_authentic.jpg"
    w, h = 800, 600
    img = Image.new("RGB", (w, h), color=(30, 45, 60))
    draw = ImageDraw.Draw(img)

    # Natural gradient scenery
    for y in range(h):
        r = int(20 + 40 * (y / h))
        g = int(35 + 80 * (y / h))
        b = int(50 + 120 * (y / h))
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # Mountain silhouettes
    draw.polygon([(0, 450), (200, 250), (450, 480)], fill=(15, 25, 35))
    draw.polygon([(250, 460), (550, 200), (800, 490)], fill=(25, 35, 45))
    draw.ellipse([580, 80, 680, 180], fill=(245, 240, 220))

    # Native Pillow EXIF
    exif = img.getexif()
    exif[0x010F] = "Canon"                                     # Make
    exif[0x0110] = "Canon EOS R5"                              # Model
    exif[0x0131] = "Canon Digital Photo Professional 4.15"     # Software
    exif[0x0132] = "2026:08:14 10:20:00"                      # DateTime

    img.save(path, "JPEG", quality=95, exif=exif)
    print(f"Created authentic sample: {path}")


def create_edited_spliced_sample():
    """Create an image with a heavily spliced region and Photoshop EXIF."""
    path = DEMO_DIR / "demo_edited_spliced.jpg"
    w, h = 800, 600
    base = Image.new("RGB", (w, h), color=(40, 50, 65))
    draw = ImageDraw.Draw(base)

    for y in range(h):
        draw.line([(0, y), (w, y)], fill=(int(30 + 30 * (y / h)), int(40 + 40 * (y / h)), int(60 + 50 * (y / h))))

    # Spliced element (re-saved at very low quality to create strong ELA difference)
    splice_patch = Image.new("RGB", (260, 160), color=(220, 80, 50))
    patch_draw = ImageDraw.Draw(splice_patch)
    patch_draw.rectangle([10, 10, 250, 150], fill=(255, 220, 0))
    patch_draw.text((30, 50), "TAMPERED PAYLOAD", fill=(0, 0, 0))

    temp_patch = DEMO_DIR / "temp_patch.jpg"
    splice_patch.save(temp_patch, "JPEG", quality=20)
    with Image.open(temp_patch) as p_img:
        base.paste(p_img, (260, 220))
    if temp_patch.exists():
        temp_patch.unlink()

    # Photoshop EXIF with suspicious software
    exif = base.getexif()
    exif[0x010F] = "Sony"
    exif[0x0110] = "ILCE-7RM5"
    exif[0x0131] = "Adobe Photoshop 2026 (Windows)"
    exif[0x0132] = "2026:09:10 18:45:12"

    base.save(path, "JPEG", quality=88, exif=exif)
    print(f"Created edited spliced sample: {path}")


def create_ai_generated_sample():
    """Create an AI-like synthetic visual with diffusion text prompts and no camera EXIF."""
    path = DEMO_DIR / "demo_ai_generated.png"
    w, h = 800, 600
    img = Image.new("RGB", (w, h), color=(10, 15, 30))
    draw = ImageDraw.Draw(img)

    for r in range(300, 10, -15):
        c_val = int(255 * (1 - (r / 300)))
        draw.ellipse([400 - r, 300 - r, 400 + r, 300 + r], outline=(c_val, 100, 255 - c_val), width=3)

    meta = PngInfo()
    meta.add_text("prompt", "Hyper-detailed cybernetic android face, volumetric neon lighting, octane render, 8k resolution")
    meta.add_text("Software", "Stable Diffusion WebUI / ComfyUI v0.3.1")
    meta.add_text("negative_prompt", "blurry, deformed, mutated hands")
    meta.add_text("model", "sd_xl_base_1.0")

    img.save(path, "PNG", pnginfo=meta)
    print(f"Created AI-generated sample: {path}")


def create_tampered_pdf():
    """Create a PDF with multiple incremental revisions and online editor signature."""
    path = DEMO_DIR / "demo_tampered_document.pdf"
    
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length 77 >>\nstream\nBT /F1 24 Tf 70 700 Td (CONFIDENTIAL ACQUISITION AGREEMENT) Tj ET\nendstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"6 0 obj\n<< /Producer (Acrobat Distiller 11.0) /CreationDate (D:20250101100000Z) >>\nendobj\n"
        b"xref\n0 7\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000244 00000 n \n0000000371 00000 n \n0000000450 00000 n \n"
        b"trailer\n<< /Size 7 /Root 1 0 R /Info 6 0 R >>\nstartxref\n550\n%%EOF\n"
        # Incremental revision tampering
        b"4 0 obj\n<< /Length 110 >>\nstream\nBT /F1 24 Tf 70 700 Td (SETTLEMENT CLAUSE ALTERED: PAYABLE $1,500,000) Tj ET\nendstream\nendobj\n"
        b"6 0 obj\n<< /Producer (iLovePDF Online Editor) /ModDate (D:20260901153000Z) >>\nendobj\n"
        b"xref\n4 1\n0000000620 00000 n \n6 1\n0000000780 00000 n \n"
        b"trailer\n<< /Size 7 /Root 1 0 R /Info 6 0 R /Prev 550 >>\nstartxref\n870\n%%EOF\n"
    )

    with open(path, "wb") as f:
        f.write(pdf_content)
    print(f"Created tampered PDF sample: {path}")


if __name__ == "__main__":
    create_authentic_sample()
    create_edited_spliced_sample()
    create_ai_generated_sample()
    create_tampered_pdf()
