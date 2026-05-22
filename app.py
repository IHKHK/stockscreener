from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="HK Breadth Site MVP")
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "breadth.json"
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

@app.get("/")
def index():
    return FileResponse(BASE_DIR / "static" / "index.html")

@app.get("/api/breadth")
def breadth():
    if not DATA_FILE.exists():
        raise HTTPException(status_code=404, detail="breadth.json not found. Run: python update_data.py")
    return FileResponse(DATA_FILE)
