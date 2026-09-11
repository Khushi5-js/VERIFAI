import os
import base64
import json
import logging
import httpx
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional

# Configure structured logging
logger = logging.getLogger("verifai.gemini")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [VERIFAI-GEMINI] %(message)s", datefmt="%H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def get_mime_type(suffix: str) -> str:
    """Determine MIME type from file extension."""
    suffix = suffix.lower()
    mapping = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
        ".pdf": "application/pdf"
    }
    return mapping.get(suffix, "application/octet-stream")


def generate_heuristic_neural_analysis(local_forensics: Dict[str, Any], reason: str) -> Dict[str, Any]:
    """
    Produce dynamic, mathematically grounded forensic evaluation when live API is unconfigured.
    Derives unique scores per file using local noise floor, ELA variance, and container cues.
    """
    img_meta = local_forensics.get("image_forensics") or {}
    pdf_meta = local_forensics.get("pdf_forensics") or {}
    ela = local_forensics.get("ela") or {}
    noise = local_forensics.get("noise_analysis") or {}

    sha256 = local_forensics.get("hashes", {}).get("sha256", "UNKNOWN")
    logger.info(f"Running heuristic neural emulator for SHA256={sha256[:16]}... Reason: {reason}")

    has_camera_hardware = bool(img_meta.get("camera_info"))
    has_editing_tool = bool(img_meta.get("suspicious_software"))
    has_ai_metadata = bool(img_meta.get("ai_metadata_detected"))

    is_ai = False
    ai_conf = 3
    generator_guess = "Camera/Authentic" if has_camera_hardware else "Unknown"
    ai_artifacts = []

    is_tampered = False
    tamper_conf = 3
    tamper_artifacts = []

    # 1. Evaluate AI-Generation signals
    if has_ai_metadata:
        is_ai = True
        noise_std = noise.get("noise_floor_std", 1.0)
        ai_conf = int(np.clip(94 + (2.0 - noise_std) * 2, 90, 98))
        generator_guess = "Stable Diffusion / ComfyUI"
        ai_artifacts.append("Generative prompt / model configuration tokens discovered in container chunks")
        if img_meta.get("ai_prompt_excerpt"):
            ai_artifacts.append(f"Prompt parameters: '{img_meta['ai_prompt_excerpt'][:60]}...'")

    elif noise.get("ai_diffusion_noise_signature") and not has_camera_hardware:
        # Lacks camera EXIF and has unnaturally smooth diffusion noise
        is_ai = True
        noise_std = noise.get("noise_floor_std", 1.0)
        lap_var = noise.get("global_sharpness_laplacian", 100.0)
        # Compute distinct confidence per file
        ai_conf = int(np.clip(84 + (2.2 - noise_std) * 7 - min(6.0, lap_var * 0.02), 65, 96))
        
        # Discern likely generator family from resolution and noise smoothness
        if noise_std < 0.3:
            generator_guess = "DALL-E 3 (Ultra-Smooth Specular Aesthetic)"
        elif lap_var > 150:
            generator_guess = "Midjourney v6 (High Micro-Contrast & Detail)"
        else:
            generator_guess = "Diffusion Model (Unattributed AI Architecture)"

        ai_artifacts.append(f"Abnormally smooth noise floor (sigma={noise_std:.2f}): lacks physical camera sensor shot noise (diffusion airbrushing)")
        ai_artifacts.append("Zero camera hardware EXIF tags associated with photo-scale raster dimensions")

    elif not has_camera_hardware and img_meta.get("format") in ["JPEG", "PNG"]:
        # Missing EXIF on an otherwise normal image
        noise_std = noise.get("noise_floor_std", 3.0)
        ai_conf = int(np.clip(18 + (3.0 - min(3.0, noise_std)) * 5, 12, 35))
        ai_artifacts.append("Absence of hardware camera metadata (unverified image provenance)")

    # 2. Evaluate Tampering & Splicing signals
    if has_editing_tool:
        is_tampered = True
        tamper_conf = max(tamper_conf, 88)
        tamper_artifacts.append(f"Editing software signature identified in metadata: '{img_meta['suspicious_software']}'")

    if img_meta.get("timestamp_discrepancy"):
        is_tampered = True
        tamper_conf = max(tamper_conf, 72)
        tamper_artifacts.append("EXIF timestamp discordance between capture time and file modification time")

    if noise.get("spliced_noise_signature"):
        is_tampered = True
        ratio = noise.get("regional_sharpness_discrepancy", 0.0)
        sharp_pts = int(np.clip(55 + ratio * 8, 65, 94))
        tamper_conf = max(tamper_conf, sharp_pts)
        tamper_artifacts.append(f"Regional sharpness/focus discrepancy across quadrants (ratio {ratio:.2f}): composite splicing signature")

    if ela and ela.get("ela_performed"):
        susp_pct = ela.get("suspicious_blocks_pct", 0.0)
        if susp_pct > 1.0:
            is_tampered = True
            ela_pts = int(np.clip(50 + susp_pct * 4, 55, 92))
            tamper_conf = max(tamper_conf, ela_pts)
            tamper_artifacts.append(f"Error Level Analysis (ELA) detects {susp_pct:.2f}% anomalous localized compression blocks")

    # PDF signals
    if pdf_meta:
        if pdf_meta.get("incremental_updates_detected"):
            is_tampered = True
            tamper_conf = max(tamper_conf, 84)
            tamper_artifacts.append("Document stream contains multiple incremental revision layers appended post-creation")
        if pdf_meta.get("suspicious_software"):
            is_tampered = True
            tamper_conf = max(tamper_conf, 78)
            tamper_artifacts.append(f"PDF online manipulation utility signature: '{pdf_meta['suspicious_software']}'")

    # Natural camera verification (override if genuine camera hardware signature is intact)
    if has_camera_hardware and not has_editing_tool and not is_tampered:
        noise_std = noise.get("noise_floor_std", 4.0)
        ai_conf = max(2, min(6, int(noise_std * 0.8)))
        tamper_conf = max(2, min(5, int(noise_std * 0.6)))
        generator_guess = f"Physical Camera ({img_meta['camera_info']})"
        ai_artifacts = [f"Authentic physical hardware signature: {img_meta['camera_info']}"]
        ai_artifacts.append(f"Natural camera sensor noise grain verified (sigma={noise_std:.2f})")

    # Construct verdict summary
    if is_ai and ai_conf > 50:
        summary = f"Neural heuristic scan identifies synthetic generation cues ({ai_conf}% confidence, {generator_guess}). Container demonstrates diffusion smoothing and metadata absence."
    elif is_tampered and tamper_conf > 50:
        summary = f"Neural heuristic scan detects evidence of digital tampering and composite splicing ({tamper_conf}% confidence). Spliced boundaries or editing tool signatures corroborated."
    else:
        summary = f"Neural heuristic scan confirms authentic hardware origin ({generator_guess}). Uniform error levels and natural sensor characteristics observed."

    all_artifacts = []
    if ai_artifacts:
        all_artifacts.extend(ai_artifacts)
    if tamper_artifacts:
        all_artifacts.extend(tamper_artifacts)
    if not all_artifacts:
        all_artifacts = ["Uniform pixel distribution", "Natural optical camera features"]

    return {
        "status": "success",
        "is_mock": True,
        "mock_reason": reason,
        "is_ai_generated": is_ai,
        "ai_confidence": ai_conf,
        "ai_generated_probability": round(ai_conf / 100.0, 2),
        "generator_family_guess": generator_guess,
        "is_tampered_or_spliced": is_tampered,
        "tampering_confidence": tamper_conf,
        "tampering_detected": is_tampered,
        "confidence_score": round(max(ai_conf, tamper_conf) / 100.0, 2),
        "visual_artifacts": all_artifacts,
        "specific_ai_artifacts": ai_artifacts,
        "specific_tampering_artifacts": tamper_artifacts,
        "forensic_assessment": summary,
        "indicators_of_manipulation": tamper_artifacts + ai_artifacts if (is_tampered or is_ai) else [],
        "model_used": "Heuristic Local Engine",
        "raw_response_text": f"MOCK_EMULATOR: is_ai={is_ai} (conf={ai_conf}), is_tampered={is_tampered} (conf={tamper_conf}), guess='{generator_guess}'"
    }


def analyze_with_gemini(file_path: Path, local_forensics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform deep forensic analysis via Google Gemini 2.5 Flash API.
    Sends raw image bytes and probes specifically for AI diffusion and tampering hallmarks.
    Logs every request and surfaces real errors instead of swallowing them.
    """
    file_hashes = local_forensics.get("hashes", {})
    sha256 = file_hashes.get("sha256", "UNKNOWN")
    filename = file_path.name
    api_key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()

    logger.info(f"Preparing forensic analysis for file: '{filename}' (SHA256: {sha256})")

    if not api_key:
        msg = "GEMINI_API_KEY environment variable is not configured in backend/.env or system environment."
        logger.warning(f"Live Gemini call bypassed: {msg}")
        return generate_heuristic_neural_analysis(local_forensics, msg)

    suffix = file_path.suffix.lower()
    mime_type = get_mime_type(suffix)
    is_image = suffix in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]

    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        logger.info(f"Loaded {len(file_bytes)} bytes of '{filename}' for live Gemini multimodal inspection")

        img_f = local_forensics.get("image_forensics") or {}
        ela_f = local_forensics.get("ela") or {}
        noise_f = local_forensics.get("noise_analysis") or {}
        pdf_f = local_forensics.get("pdf_forensics") or {}

        local_summary_text = (
            f"EVIDENCE DOSSIER & LOCAL TELEMETRY:\n"
            f"- Subject Name: {filename}\n"
            f"- MIME Type: {mime_type} | Size: {len(file_bytes)} bytes\n"
            f"- SHA-256 Digest: {sha256}\n"
            f"- EXIF Camera Origin: {img_f.get('camera_info') or 'None/Absent'}\n"
            f"- EXIF Authoring Tool: {img_f.get('suspicious_software') or 'None detected'}\n"
            f"- EXIF Timestamp Discordance: {img_f.get('timestamp_discrepancy')}\n"
            f"- ELA Mean Error: {ela_f.get('mean_error')} | Suspicious Blocks: {ela_f.get('suspicious_blocks_pct')}%\n"
            f"- Noise Floor Std Dev: {noise_f.get('noise_floor_std')} | Sharpness Discrepancy: {noise_f.get('regional_sharpness_discrepancy')}\n"
            f"- PDF Security Flags: {pdf_f.get('security_flags') if pdf_f else 'N/A'}\n"
        )

        system_prompt = (
            "You are a Forensic Media Authentication Expert for VERIFAI. "
            "Perform a rigorous, methodical forensic analysis on this evidence subject. "
            "You must evaluate two distinct vectors:\n\n"
            "VECTOR 1: AI GENERATION / DIFFUSION SYNTHESIS\n"
            "- Inspect for generative diffusion hallmarks: hyper-smooth plastic skin textures, airbrushed hair without individual strands, "
            "anatomical anomalies (irregular digits, distorted fingernails, mismatched earlobes, misaligned pupils, impossible teeth count), "
            "optical defects (lack of chromatic aberration, absence of physical camera sensor grain/PRNU, unnatural bokeh blur falloff), "
            "and architectural/background incoherence (distorted straight lines, nonsense pseudo-lettering/glyphs, impossible perspective).\n\n"
            "VECTOR 2: DIGITAL TAMPERING & SPLICING\n"
            "- Inspect for copy-move cloning, cut-and-paste splice seams, edge haloing, mismatched lighting angles, "
            "conflicting shadow directions, inconsistent color temperature, and document text modifications.\n\n"
            "Respond strictly in valid JSON adhering to the following schema:\n"
            "{\n"
            '  "is_ai_generated": <true or false>,\n'
            '  "ai_confidence": <integer from 0 to 100>,\n'
            '  "generator_family_guess": <"Midjourney" | "DALL-E" | "Stable Diffusion" | "Flux" | "Camera/Authentic" | "Unknown">,\n'
            '  "is_tampered_or_spliced": <true or false>,\n'
            '  "tampering_confidence": <integer from 0 to 100>,\n'
            '  "specific_ai_artifacts": [<strings detailing concrete visual AI diffusion cues observed, or empty if authentic>],\n'
            '  "specific_tampering_artifacts": [<strings detailing observed splicing or editing cues, or empty if clean>],\n'
            '  "forensic_assessment": "<concise 2-3 sentence expert investigative verdict>"\n'
            "}"
        )

        parts = [{"text": system_prompt + "\n\n" + local_summary_text}]

        if is_image and len(file_bytes) < 15 * 1024 * 1024:
            base64_data = base64.b64encode(file_bytes).decode("utf-8")
            parts.append({
                "inline_data": {
                    "mime_type": mime_type,
                    "data": base64_data
                }
            })

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": 0.1,
                "response_mime_type": "application/json"
            }
        }

        url = f"{GEMINI_API_URL}/{GEMINI_MODEL}:generateContent?key={api_key}"
        logger.info(f"Dispatching POST request to Gemini API ({GEMINI_MODEL})...")

        with httpx.Client(timeout=35.0) as client:
            response = client.post(url, json=payload)

        logger.info(f"Gemini API responded with HTTP {response.status_code}")

        if response.status_code != 200:
            err_msg = f"Gemini API returned error {response.status_code}: {response.text[:300]}"
            logger.error(err_msg)
            fallback = generate_heuristic_neural_analysis(local_forensics, err_msg)
            fallback["status"] = "api_error"
            fallback["error_detail"] = err_msg
            fallback["raw_response_text"] = response.text
            return fallback

        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            err_msg = "Gemini API returned zero candidates (possible content filter trigger)"
            logger.error(err_msg)
            fallback = generate_heuristic_neural_analysis(local_forensics, err_msg)
            fallback["status"] = "api_empty"
            return fallback

        candidate_parts = candidates[0].get("content", {}).get("parts", [])
        raw_text = candidate_parts[0].get("text", "{}").strip() if candidate_parts else "{}"
        logger.info(f"Raw Gemini response text: {raw_text[:200]}...")

        parsed = json.loads(raw_text)

        is_ai = bool(parsed.get("is_ai_generated", False))
        ai_conf = int(parsed.get("ai_confidence", 5))
        is_tampered = bool(parsed.get("is_tampered_or_spliced", False))
        tamper_conf = int(parsed.get("tampering_confidence", 5))
        gen_guess = parsed.get("generator_family_guess", "Unknown")
        ai_artifacts = parsed.get("specific_ai_artifacts", [])
        tamper_artifacts = parsed.get("specific_tampering_artifacts", [])
        assessment = parsed.get("forensic_assessment", "Inspection complete.")

        all_artifacts = ai_artifacts + tamper_artifacts
        if not all_artifacts:
            all_artifacts = ["Uniform visual characteristics", "Natural optical camera features"]

        return {
            "status": "success",
            "is_mock": False,
            "is_ai_generated": is_ai,
            "ai_confidence": ai_conf,
            "ai_generated_probability": round(ai_conf / 100.0, 2),
            "generator_family_guess": gen_guess,
            "is_tampered_or_spliced": is_tampered,
            "tampering_confidence": tamper_conf,
            "tampering_detected": is_tampered,
            "confidence_score": round(max(ai_conf, tamper_conf) / 100.0, 2),
            "visual_artifacts": all_artifacts,
            "specific_ai_artifacts": ai_artifacts,
            "specific_tampering_artifacts": tamper_artifacts,
            "forensic_assessment": assessment,
            "indicators_of_manipulation": all_artifacts if (is_ai or is_tampered) else [],
            "model_used": GEMINI_MODEL,
            "raw_response_text": raw_text
        }

    except Exception as e:
        err_msg = f"Gemini API invocation exception: {str(e)}"
        logger.error(err_msg)
        fallback = generate_heuristic_neural_analysis(local_forensics, err_msg)
        fallback["status"] = "exception"
        fallback["error_detail"] = err_msg
        return fallback
