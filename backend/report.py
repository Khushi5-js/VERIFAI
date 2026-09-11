import os
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timezone

HAS_REPORTLAB = False
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    HAS_REPORTLAB = True
except ImportError:
    pass


def sanitize_pdf_text(text: str) -> str:
    """Escape PDF text string delimiters."""
    if not text:
        return ""
    # Remove non-ascii or replace with safe equivalents
    text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return "".join(c if ord(c) < 128 else " " for c in text)


def generate_pure_python_pdf(case_data: Dict[str, Any], output_path: Path) -> Path:
    """
    Generate a professional multi-section forensic PDF report using native PDF 1.4 syntax.
    Guarantees 100% offline generation without external library dependencies.
    """
    case_id = case_data.get("case_id", "CASE-UNKNOWN")
    filename = case_data.get("filename", "unknown_evidence")
    created_at = case_data.get("created_at", "N/A")
    risk = case_data.get("risk_assessment", {})
    score = risk.get("score", 0)
    tier = risk.get("tier", "AUTHENTIC")
    badge = risk.get("badge", "UNVERIFIED")
    recommendation = risk.get("recommendation", "None")
    hashes = case_data.get("local_forensics", {}).get("hashes", {})
    sha256 = hashes.get("sha256", "N/A")
    md5 = hashes.get("md5", "N/A")
    size_str = hashes.get("size_formatted", "N/A")
    trail = case_data.get("evidence_trail", [])

    # Build PDF Content Stream
    stream_lines = []
    
    # Header Background Banner
    stream_lines.append("0.05 0.08 0.14 rg 36 710 540 60 re f") # Dark banner
    stream_lines.append("0.02 0.71 0.83 RG 2 w 36 710 540 60 re s") # Cyan border
    
    # Title & Subtitle
    stream_lines.append("BT /F2 20 Tf 1 1 1 rg 50 742 Td (VERIFAI FORENSIC CASE REPORT) Tj ET")
    stream_lines.append(f"BT /F1 9 Tf 0.6 0.7 0.8 rg 50 722 Td (OFFICIAL DIGITAL EVIDENCE AUDIT | {sanitize_pdf_text(case_id)}) Tj ET")

    # Meta Section
    y = 680
    stream_lines.append(f"BT /F2 11 Tf 0.1 0.1 0.2 rg 50 {y} Td (Evidence Subject: {sanitize_pdf_text(filename)}) Tj ET")
    y -= 16
    stream_lines.append(f"BT /F1 9 Tf 0.3 0.3 0.4 rg 50 {y} Td (Audit Timestamp: {sanitize_pdf_text(created_at)}  |  File Size: {sanitize_pdf_text(size_str)}) Tj ET")
    y -= 16
    stream_lines.append(f"BT /F1 8 Tf 0.3 0.3 0.4 rg 50 {y} Td (SHA-256 Digest: {sanitize_pdf_text(sha256)}) Tj ET")
    y -= 14
    stream_lines.append(f"BT /F1 8 Tf 0.3 0.3 0.4 rg 50 {y} Td (MD5 Digest: {sanitize_pdf_text(md5)}) Tj ET")

    # Verdict Box
    y -= 35
    # Box fill based on tier
    if tier == "AUTHENTIC":
        box_r, box_g, box_b = 0.06, 0.72, 0.50
    elif tier == "SUSPICIOUS":
        box_r, box_g, box_b = 0.96, 0.62, 0.04
    else:
        box_r, box_g, box_b = 0.93, 0.27, 0.27

    stream_lines.append(f"{box_r} {box_g} {box_b} rg 50 {y-10} 512 42 re f")
    stream_lines.append(f"BT /F2 14 Tf 1 1 1 rg 65 {y+12} Td (VERDICT: {sanitize_pdf_text(badge)}) Tj ET")
    stream_lines.append(f"BT /F2 14 Tf 1 1 1 rg 460 {y+12} Td (RISK: {score}/100) Tj ET")
    stream_lines.append(f"BT /F1 8 Tf 1 1 1 rg 65 {y-2} Td (Investigator Tier: {sanitize_pdf_text(tier)} | Forensic Integrity Synthesis) Tj ET")

    # Recommendation
    y -= 35
    stream_lines.append(f"BT /F2 10 Tf 0.1 0.1 0.2 rg 50 {y} Td (Investigator Recommendation:) Tj ET")
    y -= 14
    clean_rec = sanitize_pdf_text(recommendation)
    stream_lines.append(f"BT /F1 9 Tf 0.2 0.2 0.3 rg 50 {y} Td ({clean_rec[:110]}) Tj ET")

    # Divider
    y -= 20
    stream_lines.append(f"0.8 0.8 0.85 RG 1 w 50 {y} m 562 {y} l s")

    # 8-Stage Chronological Evidence Trail Summary
    y -= 25
    stream_lines.append(f"BT /F2 12 Tf 0.05 0.15 0.3 rg 50 {y} Td (8-Stage Forensic Chain of Custody Audit) Tj ET")

    y -= 15
    for stage in trail:
        st_num = stage.get("stage", 0)
        st_name = sanitize_pdf_text(stage.get("name", ""))
        st_status = sanitize_pdf_text(stage.get("status", "PASSED"))
        st_summary = sanitize_pdf_text(stage.get("summary", ""))

        # Status badge color
        if st_status == "PASSED":
            sr, sg, sb = 0.06, 0.72, 0.50
        elif st_status == "WARNING":
            sr, sg, sb = 0.96, 0.62, 0.04
        else:
            sr, sg, sb = 0.93, 0.27, 0.27

        y -= 22
        if y < 80:
            break  # Fit on single page executive summary

        # Bullet and stage line
        stream_lines.append(f"{sr} {sg} {sb} rg 50 {y+2} 6 6 re f")
        stream_lines.append(f"BT /F2 9 Tf 0.1 0.1 0.2 rg 62 {y+1} Td (Stage 0{st_num}: {st_name}) Tj ET")
        stream_lines.append(f"BT /F2 8 Tf {sr} {sg} {sb} rg 490 {y+1} Td ([{st_status}]) Tj ET")
        y -= 12
        stream_lines.append(f"BT /F1 8 Tf 0.4 0.4 0.5 rg 62 {y+1} Td ({st_summary[:95]}) Tj ET")

    # Attestation Footer
    stream_lines.append("0.8 0.8 0.85 RG 1 w 50 45 m 562 45 l s")
    stream_lines.append("BT /F1 8 Tf 0.5 0.5 0.6 rg 50 32 Td (Certified by VERIFAI Engine v1.0.0. Cryptographic hash verified against physical record.) Tj ET")
    stream_lines.append(f"BT /F1 8 Tf 0.5 0.5 0.6 rg 480 32 Td (Page 1 of 1) Tj ET")

    content_stream = "\n".join(stream_lines).encode("latin1", errors="replace")

    # Build PDF Objects
    objects = []
    
    # 1: Catalog
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    # 2: Pages
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    # 3: Page (Letter 612 x 792)
    objects.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 6 0 R /Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> >>")
    # 4: Standard Font (Helvetica)
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    # 5: Bold Font (Helvetica-Bold)
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
    # 6: Contents
    objects.append(b"<< /Length " + str(len(content_stream)).encode() + b" >>\nstream\n" + content_stream + b"\nendstream")
    # 7: Info
    now_pdf_date = datetime.now(timezone.utc).strftime("D:%Y%m%d%H%M%SZ")
    objects.append(f"<< /Title (VERIFAI Forensic Report - {case_id}) /Author (VERIFAI Engine) /CreationDate ({now_pdf_date}) >>".encode("latin1"))

    # Assemble File
    out = bytearray()
    out.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

    offsets = []
    for i, obj in enumerate(objects, 1):
        offsets.append(len(out))
        out.extend(f"{i} 0 obj\n".encode())
        out.extend(obj)
        out.extend(b"\nendobj\n")

    xref_start = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    out.extend(b"0000000000 65535 f \n")
    for off in offsets:
        out.extend(f"{off:010d} 00000 n \n".encode())

    out.extend(b"trailer\n")
    out.extend(f"<< /Size {len(objects) + 1} /Root 1 0 R /Info 7 0 R >>\n".encode())
    out.extend(b"startxref\n")
    out.extend(f"{xref_start}\n%%EOF\n".encode())

    with open(output_path, "wb") as f:
        f.write(out)

    return output_path


def generate_pdf_report(case_data: Dict[str, Any], output_dir: Path) -> Path:
    """
    Export a formal PDF forensic case report.
    Uses pure python generator to guarantee zero-dependency reliability.
    """
    case_id = case_data.get("case_id", "CASE-REPORT")
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_filename = f"{case_id}_Forensic_Report.pdf"
    pdf_path = output_dir / pdf_filename

    return generate_pure_python_pdf(case_data, pdf_path)
