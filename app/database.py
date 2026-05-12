import motor.motor_asyncio
import os
import certifi
from dotenv import load_dotenv

load_dotenv()

MONGO_DETAILS = os.getenv("MONGO_DETAILS")

if not MONGO_DETAILS:
    raise ValueError("MONGO_DETAILS is not set.")

client = motor.motor_asyncio.AsyncIOMotorClient(
    MONGO_DETAILS,
    tlsCAFile=certifi.where()   # ← fixes the SSL error on Linux
)

database = client.tu_notices
notice_collection = database.get_collection("notices_collection")

def notice_helper(notice) -> dict:
    return {
        "id": str(notice["_id"]),
        "title": notice.get("main_page_title", "No Title"),
        "link": notice.get("link"),
        "message": notice.get("main_message", "No content"),
        "attachments": notice.get("attachments", []),
        "date_scraped": notice.get("date_scraped"),
        "category": notice.get("category", ""),
    }