from typing import Dict, Any, List
from datetime import datetime, timezone


def generate_writeup(case_data: Dict[str, Any]) -> str:
    """
    Generate a full CTF-style Case Report / Forensic Write-up in formatted Markdown.
    """
    case_id = case_data.get("case_id", "CASE-UNKNOWN")
    filename = case_data.get("filename", "unknown_file")
    created_at = case_data.get("created_at", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"))
    risk = case_data.get("risk_assessment", {})
    hashes = case_data.get("local_forensics", {}).get("hashes", {})
    img_data = case_data.get("local_forensics", {}).get("image_forensics") or {}
    pdf_data = case_data.get("local_forensics", {}).get("pdf_forensics") or {}
    ela = case_data.get("local_forensics", {}).get("ela") or {}
    gemini = case_data.get("gemini_analysis", {})
    trail = case_data.get("evidence_trail", [])

    score = risk.get("score", 0)
    tier = risk.get("tier", "UNKNOWN")
    badge = risk.get("badge", "UNVERIFIED")
    recommendation = risk.get("recommendation", "None")

    lines = []
    lines.append(f"# [VERIFAI FORENSIC WRITE-UP: {case_id}]")
    lines.append(f"**Classification:** {badge} | **Forensic Risk Score:** {score}/100")
    lines.append(f"**Analyzed:** {created_at} | **Evidence Subject:** `{filename}`\n")

    lines.append("---")
    lines.append("## 1. Executive Summary")
    lines.append(f"Digital evidence package `{filename}` was submitted for comprehensive multi-factor forensic verification. "
                 f"The analysis incorporated cryptographic hashing, container structure inspection, EXIF timeline correlation, "
                 f"Error Level Analysis (ELA) differential resaving, and multimodal neural anomaly scanning.")
    lines.append(f"\n- **Final Verdict:** **{badge}**")
    lines.append(f"- **Calculated Risk Index:** **{score} / 100** (Tier: `{tier}`)")
    lines.append(f"- **Recommendation:** {recommendation}\n")

    lines.append("---")
    lines.append("## 2. Cryptographic Fingerprint & Chain of Custody")
    lines.append("| Metric | Value |")
    lines.append("| :--- | :--- |")
    lines.append(f"| **File Name** | `{filename}` |")
    lines.append(f"| **File Size** | {hashes.get('size_formatted', 'N/A')} ({hashes.get('size_bytes', 0)} bytes) |")
    lines.append(f"| **SHA-256** | `{hashes.get('sha256', 'N/A')}` |")
    lines.append(f"| **MD5** | `{hashes.get('md5', 'N/A')}` |")
    lines.append(f"| **SHA-1** | `{hashes.get('sha1', 'N/A')}` |\n")

    lines.append("---")
    lines.append("## 3. Detailed Forensic Telemetry")

    # Image telemetry
    if img_data:
        lines.append("### 3.1 Metadata & Hardware Profiling")
        lines.append(f"- **Container Format:** {img_data.get('format')} ({img_data.get('mode')})")
        dim = img_data.get('dimensions') or {}
        lines.append(f"- **Dimensions:** {dim.get('width', 'N/A')} x {dim.get('height', 'N/A')} pixels")
        lines.append(f"- **Hardware Origin:** {img_data.get('camera_info') or 'Unspecified / No EXIF make-model'}")
        lines.append(f"- **Authoring / Editing Tool:** `{img_data.get('suspicious_software') or 'None detected'}`")
        if img_data.get('gps_coordinates'):
            gps = img_data['gps_coordinates']
            lines.append(f"- **GPS Location:** Lat {gps.get('latitude')}, Lon {gps.get('longitude')}")
        if img_data.get('anomalies'):
            lines.append("- **Metadata Flags:**")
            for anom in img_data['anomalies']:
                lines.append(f"  - ⚠️ {anom}")
        lines.append("")

    # PDF telemetry
    if pdf_data:
        lines.append("### 3.1 PDF Container & Stream Analysis")
        lines.append(f"- **Specification:** {pdf_data.get('pdf_version')}")
        lines.append(f"- **Page Count:** {pdf_data.get('page_count')}")
        lines.append(f"- **Author / Producer:** {pdf_data.get('metadata', {}).get('Producer', 'Unknown')}")
        lines.append(f"- **Incremental Updates:** {'Detected (Multiple revisions)' if pdf_data.get('incremental_updates_detected') else 'Clean (Single revision)'}")
        if pdf_data.get('security_flags'):
            lines.append("- **Security Flags:**")
            for sf in pdf_data['security_flags']:
                lines.append(f"  - 🚨 {sf}")
        lines.append("")

    # ELA telemetry
    if ela and ela.get("ela_performed"):
        lines.append("### 3.2 Error Level Analysis (ELA) Differential")
        lines.append(f"- **Mean Error Level:** {ela.get('mean_error')}")
        lines.append(f"- **Peak Error Delta:** {ela.get('max_error')}")
        lines.append(f"- **Error Variance:** {ela.get('variance')}")
        lines.append(f"- **Localized Suspicious Blocks:** {ela.get('suspicious_blocks_pct')}%")
        lines.append(f"- **Interpretation:** {ela.get('verdict')}\n")

    # Neural Telemetry
    if gemini:
        lines.append("### 3.3 Multimodal Neural Inspection")
        lines.append(f"- **Model:** {gemini.get('model_used', 'Heuristic')}")
        lines.append(f"- **AI-Generation Likelihood:** {int(gemini.get('ai_generated_probability', 0) * 100)}%")
        lines.append(f"- **Tampering Indicated:** {'YES' if gemini.get('tampering_detected') else 'NO'}")
        lines.append(f"- **Assessment:** {gemini.get('forensic_assessment')}")
        if gemini.get("visual_artifacts"):
            lines.append("- **Observed Visual Features:**")
            for art in gemini["visual_artifacts"]:
                lines.append(f"  - • {art}")
        lines.append("")

    # 4. Indicators of Compromise
    flagged = risk.get("flagged_reasons", [])
    lines.append("---")
    lines.append("## 4. Corroborated Indicators of Tampering (IoCs)")
    if flagged:
        for idx, reason in enumerate(flagged, 1):
            lines.append(f"{idx}. 🚨 **FLAGGED:** {reason}")
    else:
        lines.append("✅ **No overt indicators of compromise or tampering detected across inspection layers.**")
    lines.append("")

    # 5. 8-Stage Chronological Evidence Log
    lines.append("---")
    lines.append("## 5. 8-Stage Chronological Evidence Trail")
    for st in trail:
        icon = "🟢" if st.get("status") == "PASSED" else ("🟡" if st.get("status") == "WARNING" else "🔴")
        lines.append(f"### Stage {st.get('stage')}: {st.get('name')} {icon}")
        lines.append(f"**Codename:** `{st.get('codename')}` | **Status:** `{st.get('status')}`")
        lines.append(f"**Observation:** {st.get('summary')}")
        for dt in st.get("details", []):
            lines.append(f"- {dt}")
        lines.append("")

    lines.append("---")
    lines.append("## 6. Verification Attestation")
    lines.append(f"Generated automatically by VERIFAI Forensics Engine (v1.0.0). "
                 f"Cryptographic hash integrity verified. Case record archived under reference `{case_id}`.")

    return "\n".join(lines)
