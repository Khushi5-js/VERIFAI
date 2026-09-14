# VERIFAI 🔍

### AI-Assisted Digital Evidence Verification Platform

VERIFAI is a digital forensics and media authentication platform that combines
local forensic analysis, metadata inspection, PDF structure analysis, and
multimodal AI assessment to identify suspicious indicators in digital evidence.

It is designed to assist investigators, researchers, and users in examining
images, documents, screenshots, and other digital media through a structured
multi-stage forensic workflow.

> **VERIFAI identifies and correlates suspicious indicators and produces an
> explainable risk assessment for human review.**

---
## 🚀 Live Demo

🌐 **[Open VERIFAI →](https://verifai-psg7.onrender.com/frontend/index.html)**

Experience the complete VERIFAI forensic analysis workflow directly in your browser.

---

## 🚨 Problem

Digital evidence such as images, screenshots, certificates, and PDFs can be
manipulated, edited, spliced, or generated using AI. Traditional verification
often depends on manual inspection or a single forensic technique, which can
miss important inconsistencies.

VERIFAI addresses this by combining multiple independent forensic signals into
one investigation pipeline rather than relying on a single detection method.

---

## 💡 Solution

VERIFAI performs a multi-stage analysis of uploaded evidence and correlates
the findings to generate an explainable risk assessment.

The platform does not simply return a "real" or "fake" result. Instead, it
shows the indicators found during the investigation and explains how they
contribute to the final assessment.

---

## 🔬 8-Stage Forensic Pipeline

### 1. Cryptographic Hashing
Generates SHA-256 fingerprints to uniquely identify the exact digital file
being analyzed and provide an integrity reference.

### 2. EXIF / Metadata Analysis
Extracts available metadata such as timestamps, camera information, software,
image properties, and other metadata that may reveal inconsistencies.

### 3. Container & Structural Analysis
Examines the internal structure and properties of the evidence.

For documents such as PDFs, the system can inspect metadata, pages, embedded
objects, fonts, streams, and suspicious structural elements.

### 4. Error Level Analysis (ELA)
Performs recompression-based analysis to highlight areas with unusual
compression differences that may indicate possible editing.

ELA is treated as an indicator and not as standalone proof of manipulation.

### 5. Noise Analysis
Examines image noise and high-frequency patterns to identify regions with
unusual or inconsistent characteristics.

### 6. Neural AI / Multimodal Analysis
Uses Gemini multimodal AI to inspect visual content for possible manipulation
and AI-generation indicators.

AI analysis is treated as one signal in the forensic pipeline rather than
the sole decision-maker.

### 7. Evidence Correlation
Correlates findings from hashing, metadata, structural analysis, ELA,
noise analysis, and AI assessment.

This helps reduce dependence on any single forensic technique.

### 8. Risk Assessment
The collected evidence is processed by the scoring engine to produce a
0–100 risk assessment along with supporting findings.

The score represents detected risk and should not be interpreted as a
percentage probability that a file is fake.

---

## ✨ Features

- 🔐 SHA-256 cryptographic fingerprinting
- 📋 EXIF and metadata extraction
- 📦 File and document structure inspection
- 🖼️ Error Level Analysis (ELA)
- 🔬 Noise and artifact analysis
- 🤖 Gemini multimodal AI assessment
- 🔗 Multi-signal evidence correlation
- 📊 Explainable risk scoring
- 🧾 Evidence trail
- 📝 Automated forensic case write-up
- 📄 Investigation report generation
- 📁 Case history and re-analysis
- 🏆 Investigation scoreboard
- 🧩 CTF-style investigation workflow
- 🌐 Web-based interface

---

## 🏗️ Architecture

```text
                    ┌─────────────────────┐
                    │     Web Frontend    │
                    │ HTML / CSS / JS     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     FastAPI API     │
                    │     Backend         │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        ┌──────────┐     ┌──────────┐    ┌────────────┐
        │ Metadata │     │  Image   │    │    PDF     │
        │ Analysis │     │ Forensics│    │  Analysis  │
        └──────────┘     └──────────┘    └────────────┘
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │   Gemini Multimodal │
                    │         AI          │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Evidence Correlation│
                    │ & Scoring Engine    │
                    └──────────┬──────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
          ┌──────────┐   ┌──────────┐   ┌──────────┐
          │   Risk   │   │ Evidence │   │ Forensic │
          │Assessment│   │   Trail  │   │  Report  │
          └──────────┘   └──────────┘   └──────────┘


                    
```

---

## 🛠️ Tech Stack
### Frontend
- HTML5
- CSS3
- JavaScript
### Backend
- Python
- FastAPI
- Uvicorn
### Forensic Analysis
- Pillow
- OpenCV
- NumPy
- PyMuPDF
- EXIF / Metadata Analysis
- Error Level Analysis (ELA)
- SHA-256 Hashing
### AI
- Google Gemini Multimodal AI
### Supporting Technologies
- python-dotenv
- HTTPX
- JSON
- Git
- GitHub

---

## 📂 Project Structure
```text
VERIFAI/
│
├── backend/
│   ├── analyzer.py
│   ├── cases.json
│   ├── demo_files/
│   ├── evidence_trail.py
│   ├── gemini.py
│   ├── generate_demo_files.py
│   ├── generate_rigorous_test_set.py
│   ├── main.py
│   ├── report.py
│   ├── scoring.py
│   ├── test_images/
│   ├── test_pipeline.py
│   ├── uploads/
│   ├── writeup.py
│   ├── .env
│   └── __init__.py
│
├── frontend/
│   ├── app.js
│   ├── history.html
│   ├── history.js
│   ├── index.html
│   ├── scoreboard.html
│   ├── scoreboard.js
│   ├── style.css
│   └── workshop.html
│
├── .gitignore
└── README.md
```
---

## ⚙️ Prerequisites
- Python 3.10 or newer
- A working Gemini API key
- Required Python packages
- A modern web browser
