import os
import json
import uuid
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse

from analyzer import perform_full_local_analysis
from gemini import analyze_with_gemini
from scoring import calculate_risk_score
from evidence_trail import build_evidence_trail
from writeup import generate_writeup
from report import generate_pdf_report

# Load environment
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

UPLOADS_DIR = BASE_DIR / "uploads"
CASES_FILE = BASE_DIR / "cases.json"
FRONTEND_DIR = ROOT_DIR / "frontend"
DEMO_DIR = BASE_DIR / "demo_files"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
DEMO_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="VERIFAI Digital Forensics API",
    description="Multimodal Forensics, ELA, EXIF, and AI Generation Analysis Engine",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount statics
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


def load_cases() -> List[Dict[str, Any]]:
    """Load all saved cases from JSON store."""
    if not CASES_FILE.exists():
        return []
    try:
        with open(CASES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_case_to_store(case_data: Dict[str, Any]):
    """Append or update a case in the JSON store."""
    cases = load_cases()
    cases = [c for c in cases if c.get("case_id") != case_data.get("case_id")]
    cases.insert(0, case_data)
    with open(CASES_FILE, "w", encoding="utf-8") as f:
        json.dump(cases, f, indent=2)


def execute_pipeline(file_path: Path, original_filename: str) -> Dict[str, Any]:
    """Execute complete 8-stage verification pipeline for any file on disk."""
    case_uuid = uuid.uuid4().hex[:8].upper()
    case_id = f"VERIFAI-{case_uuid}"
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Local forensics & ELA
    local_forensics = perform_full_local_analysis(file_path, UPLOADS_DIR)

    # Gemini neural multimodal analysis
    gemini_analysis = analyze_with_gemini(file_path, local_forensics)

    # Risk scoring
    risk_assessment = calculate_risk_score(local_forensics, gemini_analysis)

    # 8-Stage evidence trail
    evidence_trail = build_evidence_trail(local_forensics, gemini_analysis, risk_assessment)

    # Assemble case record
    file_url = f"/uploads/{file_path.name}"
    case_data = {
        "case_id": case_id,
        "filename": original_filename,
        "saved_filename": file_path.name,
        "file_url": file_url,
        "created_at": now_str,
        "local_forensics": local_forensics,
        "gemini_analysis": gemini_analysis,
        "risk_assessment": risk_assessment,
        "evidence_trail": evidence_trail,
        "writeup": ""
    }

    # Generate write-up
    writeup_text = generate_writeup(case_data)
    case_data["writeup"] = writeup_text

    # Persist
    save_case_to_store(case_data)

    return case_data


@app.get("/")
async def root():
    return RedirectResponse(url="/frontend/index.html")


@app.get("/api/health")
async def health_check():
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    return {
        "status": "operational",
        "app": "VERIFAI Forensics Engine",
        "version": "1.0.0",
        "gemini_configured": bool(gemini_key),
        "total_cases": len(load_cases())
    }


@app.post("/api/verify")
async def verify_evidence(file: UploadFile = File(...)):
    """Upload and execute forensic verification pipeline."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    case_uuid = uuid.uuid4().hex[:8].upper()
    orig_clean_name = Path(file.filename).name.replace(" ", "_")
    saved_filename = f"VERIFAI-{case_uuid}_{orig_clean_name}"
    dest_path = UPLOADS_DIR / saved_filename

    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {str(e)}")

    case_data = execute_pipeline(dest_path, orig_clean_name)
    return JSONResponse(status_code=200, content=case_data)


@app.get("/api/demo-samples")
async def list_demo_samples():
    """Return available pre-configured test demo samples."""
    return [
        {
            "id": "authentic",
            "name": "Authentic Camera Photo",
            "filename": "demo_authentic.jpg",
            "type": "JPEG Image",
            "description": "Natural landscape capture with genuine Canon EOS R5 EXIF metadata and uniform ELA."
        },
        {
            "id": "spliced",
            "name": "Edited & Spliced Photo",
            "filename": "demo_edited_spliced.jpg",
            "type": "JPEG Image",
            "description": "Image with spliced component, Photoshop software tags, and severe ELA compression variance."
        },
        {
            "id": "ai_generated",
            "name": "Synthetic AI Generated Image",
            "filename": "demo_ai_generated.png",
            "type": "PNG Image",
            "description": "Diffusion model rendering containing prompt parameters and absence of camera sensor signature."
        },
        {
            "id": "tampered_pdf",
            "name": "Tampered Legal Contract",
            "filename": "demo_tampered_document.pdf",
            "type": "PDF Document",
            "description": "Multi-revision PDF contract with incremental update tampering (multiple %%EOF layers)."
        }
    ]


@app.post("/api/verify-demo/{sample_id}")
async def verify_demo_sample(sample_id: str):
    """Run verification on one of the built-in demo files."""
    mapping = {
        "authentic": "demo_authentic.jpg",
        "spliced": "demo_edited_spliced.jpg",
        "ai_generated": "demo_ai_generated.png",
        "tampered_pdf": "demo_tampered_document.pdf"
    }

    filename = mapping.get(sample_id)
    if not filename:
        raise HTTPException(status_code=404, detail="Demo sample not found")

    src_path = DEMO_DIR / filename
    if not src_path.exists():
        raise HTTPException(status_code=404, detail=f"Demo file {filename} does not exist")

    case_uuid = uuid.uuid4().hex[:8].upper()
    dest_filename = f"VERIFAI-{case_uuid}_{filename}"
    dest_path = UPLOADS_DIR / dest_filename
    shutil.copyfile(src_path, dest_path)

    case_data = execute_pipeline(dest_path, filename)
    return JSONResponse(status_code=200, content=case_data)


@app.get("/api/cases")
async def get_all_cases():
    return load_cases()


@app.get("/api/cases/{case_id}")
async def get_case(case_id: str):
    cases = load_cases()
    for c in cases:
        if c.get("case_id") == case_id:
            return c
    raise HTTPException(status_code=404, detail="Case not found")


@app.delete("/api/cases/{case_id}")
async def delete_case(case_id: str):
    cases = load_cases()
    initial_len = len(cases)
    cases = [c for c in cases if c.get("case_id") != case_id]
    if len(cases) == initial_len:
        raise HTTPException(status_code=404, detail="Case not found")
    with open(CASES_FILE, "w", encoding="utf-8") as f:
        json.dump(cases, f, indent=2)
    return {"message": f"Case {case_id} deleted successfully"}


@app.get("/api/scoreboard")
async def get_scoreboard():
    cases = load_cases()
    ranked = sorted(cases, key=lambda x: x.get("risk_assessment", {}).get("score", 0), reverse=True)

    tier_counts = {
        "AUTHENTIC": 0,
        "SUSPICIOUS": 0,
        "HIGH_RISK": 0,
        "FABRICATED": 0
    }
    total_score = 0

    for c in cases:
        tier = c.get("risk_assessment", {}).get("tier", "AUTHENTIC")
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        total_score += c.get("risk_assessment", {}).get("score", 0)

    avg_score = round(total_score / len(cases), 1) if cases else 0

    return {
        "total_cases": len(cases),
        "tier_counts": tier_counts,
        "average_risk_score": avg_score,
        "leaderboard": ranked
    }


@app.get("/api/cases/{case_id}/report.pdf")
async def download_case_pdf(case_id: str):
    cases = load_cases()
    case = next((c for c in cases if c.get("case_id") == case_id), None)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    pdf_path = generate_pdf_report(case, UPLOADS_DIR)
    if not pdf_path.exists():
        raise HTTPException(status_code=500, detail="Failed to generate PDF report")

    return FileResponse(
        path=str(pdf_path),
        filename=f"{case_id}_Forensic_Report.pdf",
        media_type="application/pdf"
    )
