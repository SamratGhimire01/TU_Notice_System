import motor.motor_asyncio
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_DETAILS = os.getenv("MONGO_DETAILS")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client.tu_notices
notice_collection = database.get_collection("notices_collection")

def notice_helper(notice) -> dict:
    return {
        "id": str(notice["_id"]),
        "title": notice.get("main_page_title", "No Title"),
        "link": notice.get("link"),
        "message": notice.get("main_message", "No content"),
        "attachments": notice.get("attachments", []), # This prevents the crash
        "date_scraped": notice.get("date_scraped")
    }