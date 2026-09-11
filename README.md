# VERIFAI

VERIFAI is a digital forensics and media authentication platform that combines local forensic analysis, metadata inspection, PDF stream auditing, and multimodal AI assessment to help detect tampering, splicing, and synthetic media.

## Features

- Local image and document analysis
- Error Level Analysis (ELA) for altered media
- EXIF / metadata extraction and suspicious software detection
- PDF stream and revision inspection
- Gemini-powered multimodal analysis
- Risk scoring and case history tracking
- HTML frontend for workshop, scoreboard, and case history interfaces
- PDF report generation for investigation results

## Project Structure

```text
VERIFAI/
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
├── frontend/
│   ├── app.js
│   ├── history.html
│   ├── history.js
│   ├── index.html
│   ├── scoreboard.html
│   ├── scoreboard.js
│   ├── style.css
│   └── workshop.html
├── .gitignore
├── README.md
└── .venv/
```

## Tech Stack

- Python 3.14+
- FastAPI
- Uvicorn
- Pillow
- OpenCV
- NumPy
- python-dotenv
- httpx
- HTML / CSS / JavaScript
- SHA-256 fingerprint
- PyMuPDF
- CTF writeup

## Prerequisites

- Python 3.10 or newer
- A working Gemini API key in `backend/.env`
- Access to the required Python packages

## Setup

1. Open a terminal in the project root.
2. Activate the virtual environment if you want to use the bundled one:

```powershell
.\.venv\Scripts\Activate.ps1
```

3. Install the required Python packages if they are not already available:

```powershell
pip install fastapi uvicorn python-dotenv pillow numpy opencv-python httpx
```

4. Make sure `backend/.env` exists and contains values similar to:

```env
GEMINI_API_KEY=your_key_here
HOST=127.0.0.1
PORT=8000
```

## Running the App

From the project root, start the backend from the `backend` directory so local imports resolve correctly:

```powershell
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Then open the app in your browser:

- http://127.0.0.1:8000/

The FastAPI app serves the frontend via the mounted static directory and exposes API routes such as:

- `/api/health`
- `/api/verify`
- `/api/demo-samples`
- `/api/cases`
- `/api/scoreboard`

## Demo Workflow

The project includes built-in demo samples in `backend/demo_files/`.

You can use the web interface or call the demo verification endpoint directly.

### Available demo samples

- `demo_authentic.jpg`
- `demo_edited_spliced.jpg`
- `demo_ai_generated.png`
- `demo_tampered_document.pdf`

## Useful Scripts

### Generate demo files

```powershell
cd backend
python generate_demo_files.py
```

### Run the pipeline diagnostics on a folder

```powershell
cd backend
python test_pipeline.py test_images
```

## Notes

- `backend/uploads/` contains uploaded files and analysis outputs generated at runtime.
- `backend/cases.json` stores saved case data and is excluded from Git by the project `.gitignore`.
- `backend/.env` is also excluded from Git and should remain local to your machine.

## License

This project does not currently include a license file. If you plan to publish it publicly, you should add a license such as MIT or Apache 2.0.
