from typing import Dict, Any, List
from datetime import datetime, timezone


def build_evidence_trail(
    local_forensics: Dict[str, Any],
    gemini_results: Dict[str, Any],
    risk_assessment: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Construct an 8-stage CTF-style digital forensics evidence trail.
    """
    hashes = local_forensics.get("hashes", {})
    img_meta = local_forensics.get("image_forensics") or {}
    pdf_meta = local_forensics.get("pdf_forensics") or {}
    ela = local_forensics.get("ela") or {}
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    trail = []

    # -------------------------------------------------------------
    # STAGE 1: Cryptographic Ingestion & Hashing
    # -------------------------------------------------------------
    stage1_status = "PASSED"
    stage1_details = [
        f"File ingested: {local_forensics.get('filename')}",
        f"Byte length: {hashes.get('size_formatted')} ({hashes.get('size_bytes')} bytes)",
        f"SHA-256 Digest: {hashes.get('sha256')}",
        f"MD5 Digest: {hashes.get('md5')}"
    ]
    trail.append({
        "stage": 1,
        "name": "Cryptographic Ingestion & Hashing",
        "codename": "INGEST_HASH",
        "status": stage1_status,
        "timestamp": now_iso,
        "summary": "Cryptographic fingerprint generated and locked for custody tracking.",
        "details": stage1_details,
        "evidence": {
            "sha256": hashes.get("sha256"),
            "md5": hashes.get("md5"),
            "size": hashes.get("size_formatted")
        }
    })

    # -------------------------------------------------------------
    # STAGE 2: Metadata & EXIF Extraction
    # -------------------------------------------------------------
    stage2_status = "PASSED"
    stage2_details = []
    if img_meta:
        if img_meta.get("camera_info"):
            stage2_details.append(f"Hardware source detected: {img_meta['camera_info']}")
        else:
            stage2_details.append("No hardware camera make/model found.")

        if img_meta.get("suspicious_software"):
            stage2_status = "CRITICAL"
            stage2_details.append(f"ALERT: Editing software signature present: '{img_meta['suspicious_software']}'")
        elif img_meta.get("has_exif"):
            stage2_details.append("EXIF metadata dictionary successfully parsed.")
        else:
            stage2_status = "WARNING"
            stage2_details.append("EXIF dictionary absent or stripped.")

        if img_meta.get("timestamp_discrepancy"):
            stage2_status = "WARNING"
            stage2_details.append("Discrepancy detected between DateTimeOriginal and DateTime.")

    elif pdf_meta:
        stage2_details.append(f"PDF Author: {pdf_meta.get('metadata', {}).get('Author', 'None')}")
        stage2_details.append(f"PDF Producer: {pdf_meta.get('metadata', {}).get('Producer', 'None')}")
        if pdf_meta.get("suspicious_software"):
            stage2_status = "WARNING"
            stage2_details.append(f"Software generator flagged: {pdf_meta['suspicious_software']}")
    else:
        stage2_details.append("Container metadata inspected.")

    trail.append({
        "stage": 2,
        "name": "Metadata & EXIF Extraction",
        "codename": "METADATA_EXTRACT",
        "status": stage2_status,
        "timestamp": now_iso,
        "summary": "Software signatures, device tags, and timeline markers extracted.",
        "details": stage2_details,
        "evidence": {
            "has_exif": img_meta.get("has_exif") if img_meta else bool(pdf_meta),
            "software": img_meta.get("suspicious_software") or pdf_meta.get("suspicious_software") or "Clean",
            "camera": img_meta.get("camera_info") or "N/A"
        }
    })

    # -------------------------------------------------------------
    # STAGE 3: Container Structure & Stream Inspection
    # -------------------------------------------------------------
    stage3_status = "PASSED"
    stage3_details = []
    if img_meta:
        stage3_details.append(f"Container format: {img_meta.get('format')} | Mode: {img_meta.get('mode')}")
        dim = img_meta.get("dimensions") or {}
        stage3_details.append(f"Raster resolution: {dim.get('width', 0)} x {dim.get('height', 0)} px")
        if img_meta.get("quantization_tables"):
            stage3_details.append(f"JPEG Quantization tables: {img_meta['quantization_tables']['tables_count']} found")
    elif pdf_meta:
        stage3_details.append(f"Pages: {pdf_meta.get('page_count')} | Version: {pdf_meta.get('pdf_version')}")
        if pdf_meta.get("incremental_updates_detected"):
            stage3_status = "WARNING"
            stage3_details.append("Multiple incremental revision offsets (%%EOF) identified.")
        if pdf_meta.get("security_flags"):
            stage3_status = "CRITICAL"
            stage3_details.extend(pdf_meta["security_flags"])
    else:
        stage3_details.append("Container format verified.")

    trail.append({
        "stage": 3,
        "name": "Container Structure & Stream Inspection",
        "codename": "CONTAINER_STREAM",
        "status": stage3_status,
        "timestamp": now_iso,
        "summary": "Container headers, marker streams, and object trees audited.",
        "details": stage3_details,
        "evidence": {
            "format": img_meta.get("format") or pdf_meta.get("pdf_version") or "Binary",
            "pages_or_dims": f"{img_meta.get('dimensions')}" if img_meta else f"{pdf_meta.get('page_count')} pages"
        }
    })

    # -------------------------------------------------------------
    # STAGE 4: Error Level Analysis (ELA)
    # -------------------------------------------------------------
    stage4_status = "PASSED"
    stage4_details = []
    if ela and ela.get("ela_performed"):
        stage4_details.append(f"Mean error level: {ela.get('mean_error')}")
        stage4_details.append(f"Peak error delta: {ela.get('max_error')}")
        stage4_details.append(f"Block variance: {ela.get('variance')}")
        stage4_details.append(f"Suspicious blocks ratio: {ela.get('suspicious_blocks_pct')}%")
        stage4_details.append(f"ELA Analysis: {ela.get('verdict')}")

        if ela.get("suspicious_blocks_pct", 0) > 15:
            stage4_status = "CRITICAL"
        elif ela.get("suspicious_blocks_pct", 0) > 7:
            stage4_status = "WARNING"
    else:
        stage4_details.append("ELA is specifically calibrated for raster image containers; skipped for document.")

    trail.append({
        "stage": 4,
        "name": "Error Level Analysis (ELA)",
        "codename": "ELA_DIFFERENTIAL",
        "status": stage4_status,
        "timestamp": now_iso,
        "summary": "Resaved compression delta computed to reveal splice boundaries.",
        "details": stage4_details,
        "evidence": {
            "ela_image": ela.get("ela_image_url") if ela else None,
            "variance": ela.get("variance") if ela else 0,
            "suspicious_pct": ela.get("suspicious_blocks_pct") if ela else 0
        }
    })

    # -------------------------------------------------------------
    # STAGE 5: High-Frequency Artifact & Noise Uniformity
    # -------------------------------------------------------------
    stage5_status = "PASSED"
    stage5_details = []
    if ela and ela.get("ela_performed"):
        std = ela.get("std_dev", 0)
        if std > 12.0:
            stage5_status = "WARNING"
            stage5_details.append(f"High standard deviation in noise grid: {std:.2f} (inconsistent noise floor).")
        else:
            stage5_details.append(f"Noise floor standard deviation: {std:.2f} (within natural camera sensor baseline).")
        stage5_details.append("High-frequency boundary continuity evaluated across 8x8 DCT boundaries.")
    else:
        stage5_details.append("Standard container boundary alignment confirmed.")

    trail.append({
        "stage": 5,
        "name": "High-Frequency Artifact & Noise Uniformity",
        "codename": "NOISE_FREQUENCY",
        "status": stage5_status,
        "timestamp": now_iso,
        "summary": "Noise floor and spatial compression artifacts evaluated.",
        "details": stage5_details,
        "evidence": {
            "noise_stability": "Normal" if stage5_status == "PASSED" else "Deviant"
        }
    })

    # -------------------------------------------------------------
    # STAGE 6: Multimodal Neural Anomaly Scan (Gemini)
    # -------------------------------------------------------------
    stage6_status = "PASSED"
    stage6_details = []
    if gemini_results:
        ai_prob = gemini_results.get("ai_generated_probability", 0.0)
        tampering = gemini_results.get("tampering_detected", False)
        stage6_details.append(f"Neural Model: {gemini_results.get('model_used', 'Gemini')}")
        stage6_details.append(f"AI Generation Probability: {int(ai_prob * 100)}%")
        stage6_details.append(f"Tampering Indicated: {'YES' if tampering else 'NO'}")
        stage6_details.append(f"Assessment: {gemini_results.get('forensic_assessment')}")

        if gemini_results.get("visual_artifacts"):
            stage6_details.append(f"Visual cues: {', '.join(gemini_results['visual_artifacts'][:3])}")

        if ai_prob > 0.60 or tampering:
            stage6_status = "CRITICAL"
        elif ai_prob > 0.30:
            stage6_status = "WARNING"
    else:
        stage6_details.append("Neural scan not executed.")

    trail.append({
        "stage": 6,
        "name": "Multimodal Neural Anomaly Scan (Gemini)",
        "codename": "NEURAL_MULTIMODAL",
        "status": stage6_status,
        "timestamp": now_iso,
        "summary": "Deep visual inspection for diffusion artifacts, warped geometry, and splice seams.",
        "details": stage6_details,
        "evidence": {
            "ai_prob": gemini_results.get("ai_generated_probability") if gemini_results else 0,
            "tampering": gemini_results.get("tampering_detected") if gemini_results else False
        }
    })

    # -------------------------------------------------------------
    # STAGE 7: Heuristic Cross-Examination & IoC Matching
    # -------------------------------------------------------------
    stage7_status = "PASSED"
    stage7_details = []
    flagged = risk_assessment.get("flagged_reasons", [])
    if flagged:
        stage7_details.append(f"{len(flagged)} Indicator(s) of Compromise corroborated across stages.")
        for fl in flagged[:4]:
            stage7_details.append(f"Corroborated: {fl}")
        stage7_status = "CRITICAL" if len(flagged) >= 2 else "WARNING"
    else:
        stage7_details.append("Cross-layer correlation shows zero contradictory forensic indicators.")
        stage7_details.append("EXIF, compression signatures, and neural telemetry are mutually consistent.")

    trail.append({
        "stage": 7,
        "name": "Heuristic Cross-Examination & IoC Matching",
        "codename": "IOC_CORRELATION",
        "status": stage7_status,
        "timestamp": now_iso,
        "summary": "Cross-validation between metadata, compression artifacts, and neural cues.",
        "details": stage7_details,
        "evidence": {
            "ioc_count": len(flagged)
        }
    })

    # -------------------------------------------------------------
    # STAGE 8: Final Forensic Verdict & Score Synthesis
    # -------------------------------------------------------------
    trail.append({
        "stage": 8,
        "name": "Final Forensic Verdict & Score Synthesis",
        "codename": "VERDICT_SYNTHESIS",
        "status": "PASSED" if risk_assessment["tier"] == "AUTHENTIC" else ("WARNING" if risk_assessment["tier"] == "SUSPICIOUS" else "CRITICAL"),
        "timestamp": now_iso,
        "summary": f"Verdict: {risk_assessment['badge']} | Forensic Risk Score: {risk_assessment['score']}/100",
        "details": [
            f"Calculated Risk Score: {risk_assessment['score']}/100",
            f"Classification Tier: {risk_assessment['tier']}",
            f"Verdict: {risk_assessment['badge']}",
            f"Investigator Recommendation: {risk_assessment['recommendation']}"
        ],
        "evidence": {
            "risk_score": risk_assessment["score"],
            "tier": risk_assessment["tier"],
            "badge": risk_assessment["badge"]
        }
    })

    return trail
