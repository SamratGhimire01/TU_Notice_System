import httpx
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime
import re
from .database import notice_collection

BLACKLIST = ["logo.png", "2025_04_20_10_08_35.jpg", "fa.png", "not.png"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _get_domain(base_url: str) -> str:
    from urllib.parse import urlparse
    parsed = urlparse(base_url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _clean_message(msg: str) -> str:
    msg = msg.replace("Notice Content", "").strip()
    for kill in ["About Tribhuvan University", "Files\nS.N", "More Notices"]:
        if kill in msg:
            msg = msg.split(kill)[0]
    return msg.strip()


def _extract_tu_central(soup: BeautifulSoup, base_domain: str) -> tuple:
    """
    Parser for TU Central (tu.edu.np).
    Content: section.post-detail or div.ck-table or div.content
    Files: img[src] and a[href] ending in .pdf/.jpg
    """
    area = (
        soup.find("section", class_="post-detail")
        or soup.find("div", class_="ck-table")
        or soup.find("div", class_="content")
    )

    msg = _clean_message(
        area.get_text(separator="\n", strip=True) if area else ""
    )

    attachments = []
    seen = set()
    search_area = area or soup

    for item in search_area.find_all(["img", "a"]):
        f_url = item.get("src") or item.get("href")
        if not f_url:
            continue

        full_url = (
            f_url if f_url.startswith("http")
            else f"{base_domain}{f_url}"
        )
        clean = full_url.split("?")[0].lower()

        if any(b in clean for b in BLACKLIST):
            continue

        is_img = any(clean.endswith(ex) for ex in [".jpg", ".jpeg", ".png"])
        is_pdf = clean.endswith(".pdf")

        if (is_img or is_pdf) and full_url not in seen:
            seen.add(full_url)
            attachments.append({
                "type": "pdf" if is_pdf else "jpg",
                "url": full_url,
                "name": full_url.split("/")[-1],
            })

    return msg, attachments


def _extract_fohss(soup: BeautifulSoup, base_domain: str) -> tuple:
    """
    Parser for FoHSS (fohss.tu.edu.np).
    Content:  section.detail-page > div.detail-page-inner > div.ck-table
    Files:    section.inner-downloads table a[href] ending in .pdf
    Also picks up any img inside detail-page-inner.
    """
    # ── Message ──────────────────────────────────────────────────────────────
    detail = soup.find("section", class_="detail-page")
    inner  = detail.find("div", class_="detail-page-inner") if detail else None
    ck     = inner.find("div", class_="ck-table") if inner else None

    msg = _clean_message(
        ck.get_text(separator="\n", strip=True) if ck
        else (inner.get_text(separator="\n", strip=True) if inner else "")
    )

    # ── Attachments ───────────────────────────────────────────────────────────
    attachments = []
    seen = set()

    # 1. PDFs from the downloads table (primary source for FoHSS)
    downloads_section = soup.find("section", class_="inner-downloads")
    if downloads_section:
        for a in downloads_section.find_all("a", href=True):
            href = a["href"]
            full_url = href if href.startswith("http") else f"{base_domain}{href}"
            clean = full_url.split("?")[0].lower()

            if clean.endswith(".pdf") and full_url not in seen:
                # Try to get a human-readable name from the table row
                row = a.find_parent("tr")
                name = ""
                if row:
                    cells = row.find_all("td")
                    if cells:
                        name = cells[0].get_text(strip=True)
                seen.add(full_url)
                attachments.append({
                    "type": "pdf",
                    "url": full_url,
                    "name": name or full_url.split("/")[-1],
                })

    # 2. Images inside the detail inner area
    if inner:
        for img in inner.find_all("img", src=True):
            src = img["src"]
            full_url = src if src.startswith("http") else f"{base_domain}{src}"
            clean = full_url.split("?")[0].lower()

            if any(b in clean for b in BLACKLIST):
                continue
            if any(clean.endswith(ex) for ex in [".jpg", ".jpeg", ".png"]) and full_url not in seen:
                seen.add(full_url)
                attachments.append({
                    "type": "jpg",
                    "url": full_url,
                    "name": full_url.split("/")[-1],
                })

    return msg, attachments


async def _scrape_inner_page(
    client: httpx.AsyncClient,
    full_url: str,
    site_label: str,
    base_domain: str,
) -> tuple:
    """Fetch and parse an individual notice page. Returns (msg, attachments)."""
    try:
        res = await client.get(full_url)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        if site_label == "HUMANITIES":
            return _extract_fohss(soup, base_domain)
        else:
            return _extract_tu_central(soup, base_domain)

    except Exception as exc:
        print(f"[{site_label}] Inner page error for {full_url}: {exc}")
        return "", []


async def scrape_site(base_url: str, site_label: str) -> int:
    new_count = 0
    base_domain = _get_domain(base_url)

    async with httpx.AsyncClient(
        headers=HEADERS, timeout=20, follow_redirects=True
    ) as client:
        # ── Fetch listing page ────────────────────────────────────────────────
        try:
            response = await client.get(base_url)
            response.raise_for_status()
        except Exception as exc:
            print(f"[{site_label}] Failed to fetch listing page: {exc}")
            return 0

        soup = BeautifulSoup(response.text, "html.parser")

        # ── Collect notice links ──────────────────────────────────────────────
        links_to_process = []
        for a_tag in soup.find_all("a", href=True):
            href  = a_tag["href"]
            title = a_tag.get_text(strip=True)
            if "/notices/" in href or "/notice/" in href:
                full_url = href if href.startswith("http") else f"{base_domain}{href}"
                links_to_process.append((full_url, title))

        print(f"[{site_label}] Found {len(links_to_process)} notice links on listing page.")

        # ── Process each notice ───────────────────────────────────────────────
        for full_url, title in links_to_process:
            try:
                result = await notice_collection.update_one(
                    {"link": full_url},
                    {
                        "$setOnInsert": {
                            "main_page_title": title,
                            "link": full_url,
                            "category": site_label,
                            "date_scraped": datetime.now(),
                        }
                    },
                    upsert=True,
                )

                if not result.upserted_id:
                    continue  # Already in DB

                new_count += 1
                await asyncio.sleep(1)  # Polite delay

                msg, attachments = await _scrape_inner_page(
                    client, full_url, site_label, base_domain
                )

                await notice_collection.update_one(
                    {"link": full_url},
                    {
                        "$set": {
                            "main_message": msg,
                            "attachments": attachments,
                            "has_attachments": len(attachments) > 0,
                        }
                    },
                )

                print(f"[{site_label}] Saved: {title[:50]} | attachments: {len(attachments)}")

            except Exception as exc:
                print(f"[{site_label}] DB error for {full_url}: {exc}")

    return new_count


async def run_scraper() -> dict:
    tu_count  = await scrape_site("https://tu.edu.np/notices", "TU_CENTRAL")
    hum_count = await scrape_site("https://fohss.tu.edu.np/notices", "HUMANITIES")
    total = tu_count + hum_count
    print(f"[Scraper] Complete. TU={tu_count} | HUM={hum_count} | Total new={total}")
    return {
        "status": "success",
        "new_notices": total,
        "tu": tu_count,
        "humanities": hum_count,
    }