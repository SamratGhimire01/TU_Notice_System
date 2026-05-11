from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .database import notice_collection
from .scraper import run_scraper
import os

app = FastAPI()

app.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")
templates = Jinja2Templates(directory="templates")

# Helper to make MongoDB data JSON friendly
def clean_data(notices):
    for n in notices:
        n["_id"] = str(n["_id"])
    return notices

@app.get("/")
async def read_root(request: Request):
    all_data = await notice_collection.find().sort("date_scraped", -1).to_list(200)
    
    tu_list = [n for n in all_data if n.get("category") == "TU_CENTRAL"]
    hum_list = [n for n in all_data if n.get("category") == "HUMANITIES"]
    
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"tu_notices": tu_list, "humanities_notices": hum_list}
    )

# --- NEW API ENDPOINTS ---

@app.get("/api/notices")
async def get_all_notices():
    """Returns all notices from both sources as JSON"""
    notices = await notice_collection.find().sort("date_scraped", -1).to_list(200)
    return clean_data(notices)

@app.get("/api/notices/tu")
async def get_tu_notices():
    """Returns only TU Central notices"""
    notices = await notice_collection.find({"category": "TU_CENTRAL"}).sort("date_scraped", -1).to_list(100)
    return clean_data(notices)

@app.get("/api/notices/humanities")
async def get_hum_notices():
    """Returns only Humanities (FoHSS) notices"""
    notices = await notice_collection.find({"category": "HUMANITIES"}).sort("date_scraped", -1).to_list(100)
    return clean_data(notices)

# --- SCRAPER TRIGGER ---

@app.post("/scrape")
async def trigger_scrape():
    return await run_scraper()