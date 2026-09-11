import os
import hashlib
import json
import math
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import cv2
from PIL import Image, ImageChops, ImageEnhance
from PIL.ExifTags import TAGS, GPSTAGS

# Try importing PDF libraries
HAS_FITZ = False
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    pass

HAS_PYPDF = False
try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    pass


def calculate_hashes(file_path: Path) -> Dict[str, Any]:
    """Calculate cryptographic hashes and file metrics."""
    md5_h = hashlib.md5()
    sha1_h = hashlib.sha1()
    sha256_h = hashlib.sha256()

    size_bytes = 0
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            size_bytes += len(chunk)
            md5_h.update(chunk)
            sha1_h.update(chunk)
            sha256_h.update(chunk)

    def format_size(bytes_val: int) -> str:
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024 * 1024:
            return f"{bytes_val / 1024:.2f} KB"
        else:
            return f"{bytes_val / (1024 * 1024):.2f} MB"

    return {
        "md5": md5_h.hexdigest(),
        "sha1": sha1_h.hexdigest(),
        "sha256": sha256_h.hexdigest(),
        "size_bytes": size_bytes,
        "size_formatted": format_size(size_bytes)
    }


def parse_gps_data(gps_info: dict) -> Dict[str, Any]:
    """Convert raw EXIF GPS info into decimal latitude and longitude."""
    def _convert_to_degrees(value):
        try:
            d = float(value[0])
            m = float(value[1])
            s = float(value[2])
            return d + (m / 60.0) + (s / 3600.0)
        except Exception:
            return None

    result = {}
    try:
        gps_tags = {}
        for key, val in gps_info.items():
            sub_tag = GPSTAGS.get(key, key)
            gps_tags[sub_tag] = val

        if "GPSLatitude" in gps_tags and "GPSLatitudeRef" in gps_tags:
            lat = _convert_to_degrees(gps_tags["GPSLatitude"])
            if lat is not None:
                if gps_tags["GPSLatitudeRef"].upper() == "S":
                    lat = -lat
                result["latitude"] = round(lat, 6)

        if "GPSLongitude" in gps_tags and "GPSLongitudeRef" in gps_tags:
            lon = _convert_to_degrees(gps_tags["GPSLongitude"])
            if lon is not None:
                if gps_tags["GPSLongitudeRef"].upper() == "W":
                    lon = -lon
                result["longitude"] = round(lon, 6)

        if "GPSAltitude" in gps_tags:
            try:
                result["altitude"] = float(gps_tags["GPSAltitude"])
            except Exception:
                pass
    except Exception:
        pass
    return result


def analyze_image_exif(file_path: Path) -> Dict[str, Any]:
    """Inspect image structure, Pillow properties, EXIF tags, and PNG metadata."""
    res: Dict[str, Any] = {
        "is_image": True,
        "format": "UNKNOWN",
        "dimensions": None,
        "mode": "UNKNOWN",
        "has_exif": False,
        "exif_data": {},
        "ai_metadata_detected": False,
        "ai_prompt_excerpt": None,
        "suspicious_software": None,
        "timestamp_discrepancy": False,
        "camera_info": None,
        "gps_coordinates": None,
        "icc_profile": None,
        "quantization_tables": None,
        "anomalies": []
    }

    try:
        with Image.open(file_path) as img:
            res["format"] = img.format
            res["dimensions"] = {"width": img.width, "height": img.height}
            res["mode"] = img.mode
            res["info_keys"] = list(img.info.keys())

            if "icc_profile" in img.info:
                res["icc_profile"] = {
                    "present": True,
                    "bytes": len(img.info["icc_profile"])
                }

            if hasattr(img, "quantization") and img.quantization:
                try:
                    res["quantization_tables"] = {
                        "tables_count": len(img.quantization),
                        "sample_luma": list(img.quantization[0])[:8] if 0 in img.quantization else []
                    }
                except Exception:
                    pass

            # Extract EXIF
            exif_raw = img.getexif()
            if exif_raw and len(exif_raw) > 0:
                res["has_exif"] = True
                clean_exif = {}
                for tag_id, value in exif_raw.items():
                    tag_name = TAGS.get(tag_id, str(tag_id))
                    if isinstance(value, bytes):
                        try:
                            value = value.decode("utf-8", errors="ignore").strip("\x00")
                        except Exception:
                            value = f"<binary {len(value)} bytes>"
                    elif not isinstance(value, (int, float, str, bool, list, dict)):
                        value = str(value)
                    clean_exif[tag_name] = value

                res["exif_data"] = clean_exif

                # Inspect Camera info
                make = clean_exif.get("Make", "").strip()
                model = clean_exif.get("Model", "").strip()
                if make or model:
                    res["camera_info"] = f"{make} {model}".strip()

                # Inspect Software tag for editing signatures
                software = clean_exif.get("Software", "")
                if software:
                    known_editors = [
                        "photoshop", "gimp", "canva", "lightroom", "paint.net",
                        "snapseed", "pixlr", "vsco", "midjourney", "stable diffusion",
                        "dall-e", "novelai", "automatic1111", "comfyui", "faceapp"
                    ]
                    for editor in known_editors:
                        if editor in software.lower():
                            res["suspicious_software"] = software
                            res["anomalies"].append(f"Editing/Creation tool detected in EXIF: '{software}'")
                            break

                # Inspect Dates for mismatch
                dto = clean_exif.get("DateTimeOriginal")
                dt = clean_exif.get("DateTime")
                if dto and dt and dto != dt:
                    res["timestamp_discrepancy"] = True
                    res["anomalies"].append(f"Timestamp mismatch: Captured '{dto}' vs Saved '{dt}'")

                # GPS extraction
                if "GPSInfo" in clean_exif and isinstance(clean_exif["GPSInfo"], dict):
                    gps = parse_gps_data(clean_exif["GPSInfo"])
                    if gps:
                        res["gps_coordinates"] = gps

            # Inspect PNG text chunks for AI generation signatures
            png_text = getattr(img, "text", {}) or {}
            combined_meta = {**img.info, **png_text}
            for k, v in combined_meta.items():
                if isinstance(v, str):
                    lower_v = v.lower()
                    ai_signals = [
                        "stable diffusion", "comfyui", "midjourney", "dall-e", "novelai",
                        "automatic1111", "prompt", "negative_prompt", "lora", "sampler:", "steps:"
                    ]
                    for sig in ai_signals:
                        if sig in lower_v or sig in k.lower():
                            res["ai_metadata_detected"] = True
                            res["ai_prompt_excerpt"] = v[:100]
                            if not res["suspicious_software"]:
                                res["suspicious_software"] = f"Generative AI ({k})"
                            res["anomalies"].append(f"AI generator metadata in '{k}': {v[:60]}...")
                            break

            # Absence of EXIF in high-res photo dimensions is an anomaly
            if not res["has_exif"] and (img.width >= 500 and img.height >= 500):
                if not res.get("ai_metadata_detected"):
                    res["anomalies"].append(f"Container contains zero camera hardware EXIF tags (synthetic or stripped)")

    except Exception as e:
        res["anomalies"].append(f"Image parsing error: {str(e)}")

    return res


def perform_ela(file_path: Path, output_dir: Path, quality: int = 90, scale: int = 15) -> Dict[str, Any]:
    """
    Perform rigorous Error Level Analysis (ELA).
    Uses unique file hashing to prevent stale cache collisions.
    Calculates block-level variance, mean error, and localized anomaly percentages.
    """
    ela_result = {
        "ela_performed": False,
        "ela_image_filename": None,
        "ela_image_url": None,
        "mean_error": 0.0,
        "max_error": 0,
        "variance": 0.0,
        "std_dev": 0.0,
        "suspicious_blocks_pct": 0.0,
        "ela_anomaly_index": 0.0,
        "verdict": "Unavailable"
    }

    temp_resaved = None
    try:
        # Generate unique filenames based on hash & UUID
        file_hash = hashlib.sha256(open(file_path, "rb").read()).hexdigest()[:12]
        unique_token = uuid.uuid4().hex[:6]
        ela_filename = f"ela_{file_hash}_{unique_token}.png"
        ela_path = output_dir / ela_filename
        temp_resaved = output_dir / f"temp_{file_hash}_{unique_token}.jpg"

        with Image.open(file_path) as original:
            rgb_orig = original.convert("RGB")
            w, h = rgb_orig.size

            # Save at baseline quality
            rgb_orig.save(temp_resaved, "JPEG", quality=quality)

            with Image.open(temp_resaved) as resaved:
                rgb_resaved = resaved.convert("RGB")
                diff = ImageChops.difference(rgb_orig, rgb_resaved)

                extrema = diff.getextrema()
                max_diff = max([ex[1] for ex in extrema])
                if max_diff == 0:
                    max_diff = 1

                scale_factor = scale if scale > 0 else int(255.0 / max_diff)
                scale_factor = max(5, min(scale_factor, 25))

                enhanced_diff = ImageEnhance.Brightness(diff).enhance(scale_factor)
                enhanced_diff.save(ela_path, "PNG")

                # Convert difference to grayscale for pixel analysis
                diff_gray = diff.convert("L")
                diff_arr = np.array(diff_gray, dtype=np.float32)

                mean_val = float(np.mean(diff_arr))
                variance_val = float(np.var(diff_arr))
                std_dev = float(np.std(diff_arr))

                # Divide into grid of blocks (e.g. 24x24 pixels)
                block_size = 24
                blocks_x = max(1, w // block_size)
                blocks_y = max(1, h // block_size)
                block_means = []
                block_maxs = []

                for by in range(blocks_y):
                    for bx in range(blocks_x):
                        blk = diff_arr[by*block_size:(by+1)*block_size, bx*block_size:(bx+1)*block_size]
                        if blk.size > 0:
                            block_means.append(float(np.mean(blk)))
                            block_maxs.append(float(np.max(blk)))

                total_blocks = len(block_means)
                suspicious_blocks = 0

                if total_blocks > 0:
                    median_blk_mean = float(np.median(block_means))
                    blk_std = float(np.std(block_means))

                    # A block is suspicious if its error delta significantly deviates from global median
                    threshold = max(1.2 * blk_std, 1.0)
                    for bm, bmax in zip(block_means, block_maxs):
                        if abs(bm - median_blk_mean) > threshold or bmax > (mean_val * 3.0 + 10.0):
                            suspicious_blocks += 1

                    suspicious_pct = round((suspicious_blocks / total_blocks) * 100, 2)
                    
                    # Continuous ELA anomaly index (0 to 100)
                    anomaly_idx = min(100.0, round(suspicious_pct * 2.5 + variance_val * 1.2, 1))

                    ela_result.update({
                        "ela_performed": True,
                        "ela_image_filename": ela_filename,
                        "ela_image_url": f"/uploads/{ela_filename}",
                        "mean_error": round(mean_val, 2),
                        "max_error": int(max_diff),
                        "variance": round(variance_val, 2),
                        "std_dev": round(std_dev, 2),
                        "suspicious_blocks_pct": suspicious_pct,
                        "ela_anomaly_index": anomaly_idx
                    })

                    if anomaly_idx > 30.0 or suspicious_pct > 12.0:
                        ela_result["verdict"] = f"High ELA variance ({suspicious_pct}% deviant blocks): localized regions demonstrate discordant compression history (splicing hallmark)."
                    elif anomaly_idx > 10.0 or suspicious_pct > 4.0:
                        ela_result["verdict"] = f"Moderate ELA variation ({suspicious_pct}% deviant blocks): minor localized compression deviations detected."
                    else:
                        ela_result["verdict"] = "Uniform compression error level: consistent across container surface."

    except Exception as e:
        ela_result["verdict"] = f"ELA generation error: {str(e)}"
    finally:
        if temp_resaved and temp_resaved.exists():
            try:
                temp_resaved.unlink()
            except Exception:
                pass

    return ela_result


def analyze_noise_and_textures(file_path: Path) -> Dict[str, Any]:
    """
    Perform local mathematical texture and noise floor analysis using OpenCV & NumPy:
    - Laplacian variance (focus/sharpness consistency across quadrants)
    - High-frequency noise standard deviation (detects presence of camera sensor shot noise vs smooth AI diffusion)
    - Regional noise variance (detects composite splicing)
    """
    res = {
        "analysis_performed": False,
        "global_sharpness_laplacian": 0.0,
        "regional_sharpness_discrepancy": 0.0,
        "noise_floor_std": 0.0,
        "noise_floor_uniformity": 1.0,
        "ai_diffusion_noise_signature": False,
        "spliced_noise_signature": False,
        "observations": []
    }

    try:
        # Load image via cv2
        img = cv2.imread(str(file_path))
        if img is None:
            return res

        h, w, c = img.shape
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 1. Laplacian Sharpness across 4 quadrants
        lap = cv2.Laplacian(gray, cv2.CV_64F)
        global_lap_var = float(lap.var())
        res["global_sharpness_laplacian"] = round(global_lap_var, 2)

        mid_y, mid_x = h // 2, w // 2
        quadrants = [
            lap[0:mid_y, 0:mid_x],
            lap[0:mid_y, mid_x:w],
            lap[mid_y:h, 0:mid_x],
            lap[mid_y:h, mid_x:w]
        ]
        quad_vars = [float(q.var()) for q in quadrants]
        min_qv = min(quad_vars)
        max_qv = max(quad_vars)
        mean_qv = sum(quad_vars) / len(quad_vars)

        sharpness_disc = round((max_qv - min_qv) / (mean_qv + 1e-4), 2)
        res["regional_sharpness_discrepancy"] = sharpness_disc

        if sharpness_disc > 2.2:
            res["spliced_noise_signature"] = True
            res["observations"].append(f"Severe regional sharpness mismatch (ratio {sharpness_disc}): indicates composite splicing of elements with different focus/resolution")

        # 2. High-Frequency Noise Residual
        # Subtract median blur to isolate high frequency noise floor
        median_blur = cv2.medianBlur(gray, 3)
        noise_residual = gray.astype(np.float32) - median_blur.astype(np.float32)
        noise_std = float(np.std(noise_residual))
        res["noise_floor_std"] = round(noise_std, 2)

        # Block-level noise variance
        bw, bh = max(1, w // 4), max(1, h // 4)
        block_stds = []
        for by in range(4):
            for bx in range(4):
                blk = noise_residual[by*bh:(by+1)*bh, bx*bw:(bx+1)*bw]
                if blk.size > 0:
                    block_stds.append(float(np.std(blk)))

        noise_std_var = float(np.var(block_stds))
        res["noise_floor_uniformity"] = round(noise_std_var, 3)

        # AI Diffusion Hallmark: Extremely low or artificially smooth noise floor (< 2.2)
        if noise_std < 2.2:
            res["ai_diffusion_noise_signature"] = True
            res["observations"].append(f"Unnaturally smooth noise floor (sigma {noise_std:.2f}): lacks photographic camera sensor shot noise (diffusion airbrushing signature)")
        elif noise_std_var > 0.8:
            res["spliced_noise_signature"] = True
            res["observations"].append(f"Inconsistent noise floor variance across blocks ({noise_std_var:.2f}): characteristic of splicing elements from different camera sources")
        else:
            res["observations"].append(f"Natural photographic sensor noise floor observed (sigma {noise_std:.2f})")

        res["analysis_performed"] = True

    except Exception as e:
        res["observations"].append(f"Noise texture analysis error: {str(e)}")

    return res


def analyze_pdf(file_path: Path) -> Dict[str, Any]:
    """Inspect PDF structure, revisions, metadata, and security anomalies."""
    res: Dict[str, Any] = {
        "is_pdf": True,
        "page_count": 0,
        "metadata": {},
        "pdf_version": "UNKNOWN",
        "suspicious_software": None,
        "incremental_updates_detected": False,
        "security_flags": [],
        "embedded_fonts_count": 0,
        "embedded_images_count": 0,
        "anomalies": []
    }

    if HAS_FITZ:
        try:
            doc = fitz.open(file_path)
            res["page_count"] = len(doc)
            meta = doc.metadata or {}
            res["metadata"] = {k: v for k, v in meta.items() if v}
            res["pdf_version"] = f"PDF-{doc.pdf_version() / 10:.1f}" if hasattr(doc, "pdf_version") else "Standard"

            for i in range(len(doc)):
                page = doc[i]
                res["embedded_images_count"] += len(page.get_images())
                res["embedded_fonts_count"] += len(page.get_fonts())
            doc.close()
        except Exception as e:
            res["anomalies"].append(f"PyMuPDF error: {str(e)}")

    elif HAS_PYPDF:
        try:
            reader = pypdf.PdfReader(file_path)
            res["page_count"] = len(reader.pages)
            if reader.metadata:
                for k, v in reader.metadata.items():
                    key_clean = str(k).replace("/", "")
                    res["metadata"][key_clean] = str(v)

            img_count = 0
            for p in reader.pages:
                try:
                    img_count += len(p.images)
                except Exception:
                    pass
            res["embedded_images_count"] = img_count
        except Exception as e:
            res["anomalies"].append(f"pypdf error: {str(e)}")

    try:
        with open(file_path, "rb") as f:
            content = f.read()

        eof_count = content.count(b"%%EOF")
        if eof_count > 1:
            res["incremental_updates_detected"] = True
            res["security_flags"].append(f"Incremental revisions detected ({eof_count} %%EOF markers found in stream)")
            res["anomalies"].append(f"Document contains {eof_count} revision layers appended after initial creation")

        suspicious_tags = [
            (b"/JavaScript", "Embedded JavaScript execution object (/JavaScript)"),
            (b"/JS", "Direct JS code action (/JS)"),
            (b"/Launch", "External command launcher (/Launch)"),
            (b"/EmbeddedFiles", "Embedded binary file payload (/EmbeddedFiles)")
        ]
        for tag, desc in suspicious_tags:
            if tag in content:
                res["security_flags"].append(desc)
                res["anomalies"].append(f"Suspicious PDF object: {desc}")

        prod = str(res["metadata"].get("Producer", "")).lower()
        creator = str(res["metadata"].get("Creator", "")).lower()
        combined_tools = f"{prod} {creator}"
        known_pdf_tools = ["ilovepdf", "smallpdf", "pdfescape", "canva", "sejda", "acrobat distiller", "photoshop"]
        for tool in known_pdf_tools:
            if tool in combined_tools:
                res["suspicious_software"] = tool
                res["anomalies"].append(f"Document processed with online editor/manipulator: '{tool}'")
                break

        c_date = res["metadata"].get("CreationDate", "")
        m_date = res["metadata"].get("ModDate", "")
        if c_date and m_date and c_date != m_date:
            res["anomalies"].append(f"PDF modified after creation: Created '{c_date}' vs Modified '{m_date}'")

    except Exception as e:
        res["anomalies"].append(f"Raw PDF stream analysis error: {str(e)}")

    return res


def perform_full_local_analysis(file_path: Path, output_dir: Path) -> Dict[str, Any]:
    """
    Main orchestrator for local forensics:
    Calculates Hashes, performs Image/PDF analysis, ELA, and noise/texture analysis.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    file_hashes = calculate_hashes(file_path)

    suffix = file_path.suffix.lower()
    is_image = suffix in [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"]
    is_pdf = suffix == ".pdf"

    image_forensics = None
    pdf_forensics = None
    ela_forensics = None
    noise_forensics = None

    if is_image:
        image_forensics = analyze_image_exif(file_path)
        ela_forensics = perform_ela(file_path, output_dir)
        noise_forensics = analyze_noise_and_textures(file_path)
    elif is_pdf:
        pdf_forensics = analyze_pdf(file_path)

    return {
        "filename": file_path.name,
        "file_type": "image" if is_image else ("pdf" if is_pdf else "other"),
        "hashes": file_hashes,
        "image_forensics": image_forensics,
        "pdf_forensics": pdf_forensics,
        "ela": ela_forensics,
        "noise_analysis": noise_forensics
    }
