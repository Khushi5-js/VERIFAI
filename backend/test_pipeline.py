import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List

# Ensure backend directory is in path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from analyzer import perform_full_local_analysis
from gemini import analyze_with_gemini
from scoring import calculate_risk_score

def run_test_pipeline(test_dir: Path, output_dir: Path):
    print("=" * 80)
    print("VERIFAI FORENSIC PIPELINE DIAGNOSTIC SUITE")
    print(f"Target Directory: {test_dir}")
    print("=" * 80)

    files = sorted([f for f in test_dir.iterdir() if f.is_file() and not f.name.startswith(".")])
    if not files:
        print("ERROR: No test files found in directory!")
        return

    results = []

    for f in files:
        print(f"\n[ANALYZING] {f.name} ({f.stat().st_size} bytes)")
        
        # 1. Local Forensics
        local = perform_full_local_analysis(f, output_dir)
        sha256 = local.get("hashes", {}).get("sha256", "UNKNOWN")
        md5 = local.get("hashes", {}).get("md5", "UNKNOWN")
        
        # EXIF / Container
        img_f = local.get("image_forensics") or {}
        pdf_f = local.get("pdf_forensics") or {}
        ela = local.get("ela") or {}
        
        exif_fields = list(img_f.get("exif_data", {}).keys())
        exif_count = len(exif_fields)
        suspicious_soft = img_f.get("suspicious_software") or pdf_f.get("suspicious_software")
        ai_meta = img_f.get("ai_metadata_detected", False)
        
        # ELA values
        ela_mean = ela.get("mean_error")
        ela_max = ela.get("max_error")
        ela_var = ela.get("variance")
        ela_std = ela.get("std_dev")
        ela_susp = ela.get("suspicious_blocks_pct")
        
        # 2. Gemini Analysis
        gemini = analyze_with_gemini(f, local)
        is_mock = gemini.get("is_mock", True)
        mock_reason = gemini.get("mock_reason", "None")
        gemini_ai_prob = gemini.get("ai_generated_probability")
        gemini_tamper = gemini.get("tampering_detected")
        gemini_conf = gemini.get("confidence_score")
        gemini_summary = gemini.get("forensic_assessment")
        gemini_artifacts = gemini.get("visual_artifacts", [])
        raw_model = gemini.get("model_used")
        raw_response = gemini.get("raw_response_text", None)
        
        # 3. Scoring
        risk = calculate_risk_score(local, gemini)
        total_score = risk.get("score")
        tier = risk.get("tier")
        badge = risk.get("badge")
        factors = risk.get("factors", {})
        reasons = risk.get("flagged_reasons", [])
        
        record = {
            "filename": f.name,
            "sha256": sha256,
            "md5": md5,
            "exif_count": exif_count,
            "exif_fields": exif_fields,
            "suspicious_software": suspicious_soft,
            "ai_metadata_detected": ai_meta,
            "ela_mean": ela_mean,
            "ela_max": ela_max,
            "ela_var": ela_var,
            "ela_std": ela_std,
            "ela_susp": ela_susp,
            "gemini_is_mock": is_mock,
            "gemini_mock_reason": mock_reason,
            "gemini_ai_prob": gemini_ai_prob,
            "gemini_tamper": gemini_tamper,
            "gemini_conf": gemini_conf,
            "gemini_summary": gemini_summary,
            "gemini_artifacts": gemini_artifacts,
            "gemini_model": raw_model,
            "raw_gemini_response": raw_response,
            "factor_meta": factors.get("metadata_risk"),
            "factor_ela": factors.get("ela_compression_risk"),
            "factor_struct": factors.get("container_structure_risk"),
            "factor_neural": factors.get("neural_ai_risk"),
            "total_score": total_score,
            "tier": tier,
            "badge": badge,
            "flagged_reasons": reasons
        }
        results.append(record)
        
        print(f"  SHA-256:              {sha256}")
        print(f"  EXIF Fields Count:    {exif_count} -> {exif_fields[:5]}")
        print(f"  Suspicious Software:  {suspicious_soft}")
        print(f"  AI Metadata Flag:     {ai_meta}")
        print(f"  ELA Metrics:          mean={ela_mean}, max={ela_max}, variance={ela_var}, std_dev={ela_std}, susp_blocks={ela_susp}%")
        print(f"  Gemini Invocation:    is_mock={is_mock} | model={raw_model} | reason={mock_reason}")
        print(f"  Gemini AI Prob:       {gemini_ai_prob} | tamper={gemini_tamper} | conf={gemini_conf}")
        print(f"  Gemini Assessment:    {gemini_summary}")
        if raw_response:
            print(f"  Raw Gemini Response:  {raw_response}")
        print(f"  Category Factors:     Meta={factors.get('metadata_risk')}/30, ELA={factors.get('ela_compression_risk')}/25, Struct={factors.get('container_structure_risk')}/20, Neural={factors.get('neural_ai_risk')}/25")
        print(f"  FINAL SCORE:          {total_score}/100 [{tier} - {badge}]")
        print(f"  Flagged Reasons:      {reasons}")

    # Cross-file comparison to detect identical values
    print("\n" + "=" * 80)
    print("CROSS-FILE VALUE COMPARISON & STUCK STAGE DETECTION")
    print("=" * 80)
    
    fields_to_check = [
        ("sha256", "SHA256 Hash"),
        ("ela_var", "ELA Variance"),
        ("ela_mean", "ELA Mean"),
        ("gemini_summary", "Gemini Assessment Text"),
        ("gemini_ai_prob", "Gemini AI Probability"),
        ("factor_meta", "Category: Metadata Risk"),
        ("factor_ela", "Category: ELA Risk"),
        ("factor_struct", "Category: Container Risk"),
        ("factor_neural", "Category: Neural Risk"),
        ("total_score", "Total Risk Score")
    ]
    
    identical_flags = []
    
    for key, label in fields_to_check:
        seen = {}
        for r in results:
            val = r.get(key)
            if val is not None:
                if val in seen:
                    identical_flags.append((label, val, seen[val], r["filename"]))
                else:
                    seen[val] = r["filename"]

    if identical_flags:
        print("⚠️  WARNING: IDENTICAL VALUES DETECTED ACROSS DIFFERENT FILES:")
        for label, val, file1, file2 in identical_flags:
            val_str = str(val)
            if len(val_str) > 60:
                val_str = val_str[:57] + "..."
            print(f"  [IDENTICAL {label}]")
            print(f"    Value:    {val_str}")
            print(f"    Between:  '{file1}' and '{file2}'")
    else:
        print("✅ SUCCESS: All evaluated intermediate and final values vary uniquely per file.")

    return results

if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else (BASE_DIR / "demo_files")
    output_dir = BASE_DIR / "uploads"
    run_test_pipeline(target, output_dir)
