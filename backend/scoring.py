from typing import Dict, Any, Tuple
import numpy as np


def calculate_risk_score(local_forensics: Dict[str, Any], gemini_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute unified forensic risk score (0 - 100) and risk tier.
    Evaluates metadata, continuous ELA compression, physical noise floor, and neural analysis.
    """
    img_data = local_forensics.get("image_forensics") or {}
    pdf_data = local_forensics.get("pdf_forensics") or {}
    ela_data = local_forensics.get("ela") or {}
    noise_data = local_forensics.get("noise_analysis") or {}

    metadata_score = 0
    ela_score = 0
    structure_score = 0
    neural_score = 0

    reasons = []

    # ------------------------------------------------------------------
    # 1. METADATA FACTOR (Max 30)
    # ------------------------------------------------------------------
    if img_data:
        if img_data.get("ai_metadata_detected"):
            metadata_score += 28
            reasons.append("Generative AI prompt / model parameters discovered in image container metadata")
        elif img_data.get("suspicious_software"):
            metadata_score += 24
            reasons.append(f"Image processed with editing software: {img_data['suspicious_software']}")

        if img_data.get("timestamp_discrepancy"):
            metadata_score += 14
            reasons.append("EXIF timestamp mismatch detected (creation vs modification time)")

        if not img_data.get("has_exif") and img_data.get("format") in ["JPEG", "PNG"]:
            dim = img_data.get("dimensions") or {}
            w, h = dim.get("width", 0), dim.get("height", 0)
            if w >= 500 and h >= 500 and not img_data.get("ai_metadata_detected"):
                # Proportional to image area
                area_factor = min(4, int((w * h) / (600 * 600)))
                metadata_score += (7 + area_factor)
                reasons.append("Photo-scale dimensions contain zero camera hardware EXIF tags (stripped or synthetic)")

    if pdf_data:
        if pdf_data.get("suspicious_software"):
            metadata_score += 22
            reasons.append(f"PDF processed by editing utility: {pdf_data['suspicious_software']}")
        if pdf_data.get("anomalies"):
            metadata_score += min(15, len(pdf_data["anomalies"]) * 5)

    metadata_score = min(30, metadata_score)

    # ------------------------------------------------------------------
    # 2. ELA & COMPRESSION FACTOR (Max 25) - Continuous Scaling
    # ------------------------------------------------------------------
    if ela_data and ela_data.get("ela_performed"):
        susp_pct = float(ela_data.get("suspicious_blocks_pct", 0.0))
        variance = float(ela_data.get("variance", 0.0))
        mean_err = float(ela_data.get("mean_error", 0.0))
        max_err = float(ela_data.get("max_error", 0.0))

        # Continuous scoring: captures both subtle and severe compression signatures
        ela_val = (susp_pct * 1.4) + (variance * 0.5) + (mean_err * 0.4) + (max_err * 0.04)
        ela_score = min(25, max(1, int(round(ela_val))))

        if susp_pct > 8.0 or variance > 20.0:
            reasons.append(f"Error Level Analysis (ELA) anomaly: {susp_pct:.1f}% irregular compression blocks (variance={variance:.2f})")
        elif susp_pct > 1.0 or variance > 3.0:
            reasons.append(f"Minor localized compression variation detected via ELA ({susp_pct:.1f}% deviant blocks)")
    else:
        ela_score = 0

    # ------------------------------------------------------------------
    # 3. CONTAINER STRUCTURE & PHYSICAL NOISE FLOOR (Max 20)
    # ------------------------------------------------------------------
    if noise_data and noise_data.get("analysis_performed"):
        sharpness_disc = float(noise_data.get("regional_sharpness_discrepancy", 0.0))
        noise_std = float(noise_data.get("noise_floor_std", 0.0))

        if noise_data.get("spliced_noise_signature"):
            spliced_pts = min(18, max(8, int(6 + sharpness_disc * 4)))
            structure_score += spliced_pts
            reasons.append(f"Regional sharpness/noise discrepancy detected across quadrants (ratio {sharpness_disc:.2f})")
        elif noise_data.get("ai_diffusion_noise_signature"):
            # Smooth noise floor characteristic of diffusion
            diff_pts = min(16, max(8, int(8 + (2.2 - noise_std) * 4)))
            structure_score += diff_pts
            reasons.append(f"Unnaturally smooth noise floor (sigma={noise_std:.2f}): lacks physical sensor shot noise")
        else:
            # Genuine camera noise floor
            structure_score += min(3, max(1, int(noise_std * 0.3)))

    if pdf_data:
        if pdf_data.get("incremental_updates_detected"):
            structure_score += 15
            reasons.append("Document modified after signing/creation (multiple incremental revision layers)")
        if pdf_data.get("security_flags"):
            structure_score += min(15, len(pdf_data["security_flags"]) * 8)
            reasons.append(f"PDF contains executable or suspicious objects: {', '.join(pdf_data['security_flags'])}")

    structure_score = min(20, structure_score)

    # ------------------------------------------------------------------
    # 4. NEURAL AI / GEMINI FACTOR (Max 25)
    # ------------------------------------------------------------------
    if gemini_results:
        is_ai = bool(gemini_results.get("is_ai_generated", False))
        ai_conf = int(gemini_results.get("ai_confidence", 5))
        is_tampered = bool(gemini_results.get("is_tampered_or_spliced", False))
        tamper_conf = int(gemini_results.get("tampering_confidence", 5))
        gen_guess = gemini_results.get("generator_family_guess", "Unknown")

        if is_ai and ai_conf > 30:
            ai_pts = min(25, max(6, int(round(ai_conf * 0.25))))
            neural_score = max(neural_score, ai_pts)
            reasons.append(f"Neural vision model flags synthetic AI generation ({ai_conf}% confidence, {gen_guess})")

        if is_tampered and tamper_conf > 30:
            tamper_pts = min(25, max(6, int(round(tamper_conf * 0.25))))
            neural_score = max(neural_score, tamper_pts)
            reasons.append(f"Neural vision model flags visual tampering/splicing ({tamper_conf}% confidence)")

        if not is_ai and not is_tampered:
            neural_score = max(1, min(3, int(ai_conf * 0.25)))

    neural_score = min(25, neural_score)

    # ------------------------------------------------------------------
    # TOTAL SCORE & CLASSIFICATION TIER
    # ------------------------------------------------------------------
    total_score = metadata_score + ela_score + structure_score + neural_score
    total_score = min(100, max(2, total_score))

    # Tiers
    if total_score <= 20:
        tier = "AUTHENTIC"
        color = "#10b981"  # Emerald Green
        verdict_badge = "VERIFIED AUTHENTIC"
        recommendation = "Content demonstrates consistent integrity, genuine hardware camera metadata, and natural optical sensor characteristics."
    elif total_score <= 50:
        tier = "SUSPICIOUS"
        color = "#f59e0b"  # Amber Orange
        verdict_badge = "ANOMALIES FLAGGED"
        recommendation = "Secondary investigation recommended. Inconsistencies detected in metadata, localized compression, or noise floor."
    elif total_score <= 75:
        tier = "HIGH_RISK"
        color = "#ef4444"  # Red
        verdict_badge = "EVIDENCE OF MANIPULATION"
        recommendation = "High probability of alteration. Clear signatures of editing software, ELA discrepancies, or structural composite revisions."
    else:
        tier = "FABRICATED"
        color = "#dc2626"  # Dark Crimson
        verdict_badge = "SYNTHETIC / FABRICATED"
        recommendation = "Critical risk. Strong indicators of AI diffusion generation, deliberate forgery, or composite tampering."

    return {
        "score": total_score,
        "tier": tier,
        "color": color,
        "badge": verdict_badge,
        "recommendation": recommendation,
        "factors": {
            "metadata_risk": metadata_score,
            "ela_compression_risk": ela_score,
            "container_structure_risk": structure_score,
            "neural_ai_risk": neural_score
        },
        "flagged_reasons": reasons
    }
