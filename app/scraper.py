import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import re
import time
from .database import notice_collection

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

BLACKLIST = ["logo.png", "2025_04_20_10_08_35.jpg", "fa.png", "not.png"]

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)

async def scrape_site(base_url, site_label):
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Pop; Linux x86_64) AppleWebKit/537.36'} 
    new_count = 0
    
    try:
        response = requests.get(base_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for a_tag in soup.find_all('a', href=True):
            link = a_tag['href']
            title = a_tag.get_text(strip=True)

            if "/notices/" in link or "/notice/" in link:
                if link.startswith("http"):
                    full_url = link
                else:
                    domain = "https://fohss.tu.edu.np" if "fohss" in base_url else "https://tu.edu.np"
                    full_url = f"{domain}{link}"
                
                result = await notice_collection.update_one(
                    {"link": full_url}, 
                    {"$setOnInsert": {
                        "main_page_title": title,
                        "link": full_url,
                        "category": site_label,
                        "date_scraped": datetime.now(),
                    }},
                    upsert=True
                )
                
                if result.upserted_id:
                    new_count += 1
                    try:
                        time.sleep(1)
                        inner_res = requests.get(full_url, headers=headers, timeout=15)
                        inner_soup = BeautifulSoup(inner_res.text, 'html.parser')
                        
                        area = inner_soup.find('section', class_='post-detail') or \
                               inner_soup.find('div', class_='ck-table') or \
                               inner_soup.find('div', class_='content')
                        
                        msg = area.get_text(separator="\n", strip=True) if area else ""
                        msg = msg.replace("Notice Content", "")
                        for kill in ["About Tribhuvan University", "Files\nS.N", "More Notices"]:
                            if kill in msg: msg = msg.split(kill)[0]

                        # --- NEW LOGIC: Save URL directly ---
                        found = []
                        potential = (area or inner_soup).find_all(['img', 'a'])
                        for item in potential:
                            f_url = item.get('src') or item.get('href')
                            if not f_url: continue
                            
                            full_f_url = f_url if f_url.startswith("http") else f"{base_url.split('/notices')[0]}{f_url}"
                            clean = full_f_url.split('?')[0].lower()

                            if any(b in clean for b in BLACKLIST): continue

                            is_img = any(clean.endswith(ex) for ex in ['.jpg', '.jpeg', '.png'])
                            is_pdf = clean.endswith('.pdf')

                            if is_img or is_pdf:
                                ext = "pdf" if is_pdf else "jpg"
                                # We store the REMOTE URL directly instead of a local filename
                                if not any(x['url'] == full_f_url for x in found):
                                    found.append({"type": ext, "url": full_f_url})

                        await notice_collection.update_one(
                            {"link": full_url},
                            {"$set": {"main_message": msg.strip(), "attachments": found, "has_attachments": len(found) > 0}}
                        )
                    except: continue
        return new_count
    except: return 0

async def run_scraper():
    tu = await scrape_site("https://tu.edu.np/notices", "TU_CENTRAL")
    hum = await scrape_site("https://fohss.tu.edu.np/notices", "HUMANITIES")
    return {"status": "Success", "scraped_count": tu + hum}