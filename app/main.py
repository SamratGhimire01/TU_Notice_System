from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .database import notice_collection
from .scraper import run_scraper
import os
import asyncio

# ── Background scraper loop ───────────────────────────────────────────────────
SCRAPE_INTERVAL_HOURS = 2


async def auto_scrape_loop():
    """
    Runs the scraper once immediately on startup,
    then repeats every SCRAPE_INTERVAL_HOURS hours automatically.
    """
    while True:
        print("[Auto-Scraper] Running scheduled scrape...")
        try:
            result = await run_scraper()
            print(f"[Auto-Scraper] Done: {result}")
        except Exception as exc:
            print(f"[Auto-Scraper] Error during scrape: {exc}")
        print(f"[Auto-Scraper] Next auto-scrape in {SCRAPE_INTERVAL_HOURS} hours.")
        await asyncio.sleep(SCRAPE_INTERVAL_HOURS * 60 * 60)


# ── Lifespan (startup + shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("downloads", exist_ok=True)

    # Launch the background scraper task when the server starts
    task = asyncio.create_task(auto_scrape_loop())
    print("[Lifespan] Auto-scraper background task started.")

    yield  # App runs here

    # Clean shutdown — cancel the loop gracefully
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("[Lifespan] Auto-scraper task cancelled cleanly on shutdown.")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="TU Notice Hub",
    description="Tribhuvan University Notice Aggregator — auto-scrapes every 2 hours",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files & templates ──────────────────────────────────────────────────
os.makedirs("downloads", exist_ok=True)
app.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")
templates = Jinja2Templates(directory="templates")


# ── Helpers ───────────────────────────────────────────────────────────────────
def clean_data(notices: list) -> list:
    """Make MongoDB documents JSON-serialisable and fill safe defaults."""
    for n in notices:
        n["_id"] = str(n["_id"])
        n.setdefault("attachments", [])
        n.setdefault("main_message", "")
        n.setdefault("main_page_title", "No Title")
    return notices


# ── HTML route ────────────────────────────────────────────────────────────────
@app.get("/")
async def read_root(request: Request):
    all_data = await notice_collection.find().sort("date_scraped", -1).to_list(200)
    clean_data(all_data)

    tu_list  = [n for n in all_data if n.get("category") == "TU_CENTRAL"]
    hum_list = [n for n in all_data if n.get("category") == "HUMANITIES"]

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"tu_notices": tu_list, "humanities_notices": hum_list},
    )


# ── API endpoints ─────────────────────────────────────────────────────────────
@app.get("/api/notices")
async def get_all_notices():
    """All notices from both sources."""
    notices = await notice_collection.find().sort("date_scraped", -1).to_list(200)
    return clean_data(notices)


@app.get("/api/notices/tu")
async def get_tu_notices():
    """TU Central notices only."""
    notices = (
        await notice_collection
        .find({"category": "TU_CENTRAL"})
        .sort("date_scraped", -1)
        .to_list(100)
    )
    return clean_data(notices)


@app.get("/api/notices/humanities")
async def get_hum_notices():
    """FoHSS / Humanities notices only."""
    notices = (
        await notice_collection
        .find({"category": "HUMANITIES"})
        .sort("date_scraped", -1)
        .to_list(100)
    )
    return clean_data(notices)


@app.get("/api/health")
async def health_check():
    """Health check — used by Hugging Face and uptime monitors."""
    return {"status": "ok"}


# ── Manual scraper trigger ────────────────────────────────────────────────────
@app.post("/scrape")
async def trigger_scrape():
    """
    Manually trigger the scraper on demand.
    This is what the SYNC NOTICES button calls.
    The auto-scraper runs separately every 2 hours regardless.
    """
    try:
        result = await run_scraper()
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))