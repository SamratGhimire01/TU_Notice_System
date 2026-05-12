---
title: TU Notice Hub
emoji: 🎓
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# 🎓 TU Notice Hub

A live notice aggregator for **Tribhuvan University (TU Central)** and **Faculty of Humanities and Social Sciences (FoHSS)**. It automatically scrapes both websites every **2 hours** and stores notices in a database — accessible via a clean web UI and a fully open REST API.

**Live App:** [https://samratghimire01-tu-notice-hub.hf.space](https://samratghimire01-tu-notice-hub.hf.space)  
**Interactive API Docs (Swagger):** [https://samratghimire01-tu-notice-hub.hf.space/docs](https://samratghimire01-tu-notice-hub.hf.space/docs)  
**API Docs (ReDoc):** [https://samratghimire01-tu-notice-hub.hf.space/redoc](https://samratghimire01-tu-notice-hub.hf.space/redoc)

---

## 📦 What This Provides

| Feature | Details |
|---|---|
| Auto-scraping | Every 2 hours from tu.edu.np and fohss.tu.edu.np |
| Manual sync | POST /scrape endpoint or SYNC button in UI |
| REST API | JSON endpoints for all notices, TU only, or FoHSS only |
| Attachments | PDFs and images extracted from each notice |
| Free to use | No API key required |

---

## 🌐 API Reference

**Base URL:**
```
https://samratghimire01-tu-notice-hub.hf.space
```

All endpoints return **JSON**. No authentication required.

---

### 1. Health Check

Check if the API is online.

```
GET /api/health
```

**Response:**
```json
{
  "status": "ok"
}
```

**Example:**
```bash
curl https://samratghimire01-tu-notice-hub.hf.space/api/health
```

---

### 2. Get All Notices

Returns the latest 200 notices from both TU Central and FoHSS combined, sorted by newest first.

```
GET /api/notices
```

**Response:**
```json
[
  {
    "_id": "6830a1f2e4b0c123456789ab",
    "main_page_title": "BCA IV, BCA VII and MA II Semester Results",
    "link": "https://fohss.tu.edu.np/notices/12793",
    "category": "HUMANITIES",
    "main_message": "Results have been published...",
    "attachments": [
      {
        "type": "pdf",
        "url": "https://portal.tu.edu.np/notice/12793/1778504295.pdf",
        "name": "BCA 4th Semester (2023 Batch)"
      }
    ],
    "has_attachments": true,
    "date_scraped": "2026-05-12T14:30:00.000Z"
  }
]
```

**Example:**
```bash
curl https://samratghimire01-tu-notice-hub.hf.space/api/notices
```

---

### 3. Get TU Central Notices Only

Returns up to 100 notices from TU Central Office only.

```
GET /api/notices/tu
```

**Response:** Same structure as above, all with `"category": "TU_CENTRAL"`

**Example:**
```bash
curl https://samratghimire01-tu-notice-hub.hf.space/api/notices/tu
```

---

### 4. Get Humanities (FoHSS) Notices Only

Returns up to 100 notices from the Faculty of Humanities and Social Sciences only.

```
GET /api/notices/humanities
```

**Response:** Same structure as above, all with `"category": "HUMANITIES"`

**Example:**
```bash
curl https://samratghimire01-tu-notice-hub.hf.space/api/notices/humanities
```

---

### 5. Trigger Manual Scrape

Forces the scraper to run immediately regardless of the 2-hour schedule. Useful if you need the latest data right now.

```
POST /scrape
```

**Response:**
```json
{
  "status": "success",
  "new_notices": 5,
  "tu": 3,
  "humanities": 2
}
```

**Example:**
```bash
curl -X POST https://samratghimire01-tu-notice-hub.hf.space/scrape
```

---

## 📋 Response Field Reference

| Field | Type | Description |
|---|---|---|
| `_id` | string | Unique notice ID (MongoDB ObjectId as string) |
| `main_page_title` | string | Title of the notice as shown on the listing page |
| `link` | string | Direct URL to the original notice on the TU/FoHSS website |
| `category` | string | Either `TU_CENTRAL` or `HUMANITIES` |
| `main_message` | string | Full text content of the notice |
| `attachments` | array | List of files attached to the notice (PDFs and images) |
| `attachments[].type` | string | Either `pdf` or `jpg` |
| `attachments[].url` | string | Direct download URL of the file |
| `attachments[].name` | string | Human-readable name of the file |
| `has_attachments` | boolean | `true` if notice has any attachments |
| `date_scraped` | string | ISO 8601 datetime when this notice was first scraped |

---

## 💻 Usage Examples

### JavaScript / Fetch

```javascript
// Get all notices
const response = await fetch('https://samratghimire01-tu-notice-hub.hf.space/api/notices');
const notices = await response.json();

// Display titles
notices.forEach(notice => {
  console.log(notice.main_page_title);
  console.log(notice.category);
  console.log(notice.date_scraped);
});
```

```javascript
// Get only TU Central notices
const res = await fetch('https://samratghimire01-tu-notice-hub.hf.space/api/notices/tu');
const tuNotices = await res.json();
```

```javascript
// Get notices with PDFs only
const res = await fetch('https://samratghimire01-tu-notice-hub.hf.space/api/notices');
const all = await res.json();
const withPDFs = all.filter(n => n.has_attachments);
```

---

### Python

```python
import requests

BASE = "https://samratghimire01-tu-notice-hub.hf.space"

# Get all notices
response = requests.get(f"{BASE}/api/notices")
notices = response.json()

for notice in notices:
    print(notice["main_page_title"])
    print(notice["category"])
    for att in notice["attachments"]:
        print(f"  {att['name']} → {att['url']}")
```

```python
# Filter by category
hu_notices = [n for n in notices if n["category"] == "HUMANITIES"]
tu_notices  = [n for n in notices if n["category"] == "TU_CENTRAL"]

# Get notices that have attachments
with_files = [n for n in notices if n["has_attachments"]]
```

---

### React

```jsx
import { useEffect, useState } from "react";

const BASE = "https://samratghimire01-tu-notice-hub.hf.space";

export default function TUNotices() {
  const [notices, setNotices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${BASE}/api/notices`)
      .then(res => res.json())
      .then(data => {
        setNotices(data);
        setLoading(false);
      });
  }, []);

  if (loading) return <p>Loading notices...</p>;

  return (
    <div>
      {notices.map(notice => (
        <div key={notice._id} style={{ marginBottom: 24 }}>
          <h3>{notice.main_page_title}</h3>
          <p>{notice.category} — {new Date(notice.date_scraped).toLocaleDateString()}</p>
          <p>{notice.main_message}</p>

          {notice.attachments.length > 0 && (
            <table border="1" cellPadding="8">
              <thead>
                <tr><th>S.N</th><th>Name</th><th>Type</th><th>Download</th></tr>
              </thead>
              <tbody>
                {notice.attachments.map((file, i) => (
                  <tr key={i}>
                    <td>{i + 1}</td>
                    <td>{file.name}</td>
                    <td>{file.type.toUpperCase()}</td>
                    <td><a href={file.url} target="_blank" rel="noopener">Open</a></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      ))}
    </div>
  );
}
```

---

### PHP

```php
<?php
$base = "https://samratghimire01-tu-notice-hub.hf.space";

$response = file_get_contents("$base/api/notices");
$notices  = json_decode($response, true);

foreach ($notices as $notice) {
    echo $notice["main_page_title"] . "\n";
    echo $notice["category"] . "\n";

    foreach ($notice["attachments"] as $i => $file) {
        echo ($i + 1) . ". " . $file["name"] . " → " . $file["url"] . "\n";
    }
    echo "\n";
}
?>
```

---

## 🔄 Scraping Schedule

| Source | URL | Schedule |
|---|---|---|
| TU Central | tu.edu.np/notices | Every 2 hours (auto) |
| FoHSS | fohss.tu.edu.np/notices | Every 2 hours (auto) |

The scraper also runs **once immediately** when the server starts. You can trigger a manual scrape anytime via `POST /scrape`.

New notices are **only added** — existing notices are never deleted or overwritten. The scraper uses upsert logic so running it multiple times is safe.

---

## 🚫 Rate Limiting

There is currently no rate limiting on the API. Please be respectful:
- Do not poll more than once every 10 minutes
- Use the `/api/health` endpoint to check uptime instead of hitting `/api/notices` repeatedly
- Cache responses on your end where possible

---

## 🛠️ Running Locally

```bash
# 1. Clone this repo
git clone https://huggingface.co/spaces/samratghimire01/tu-notice-hub
cd tu-notice-hub

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
echo 'MONGO_DETAILS="your_mongodb_connection_string"' > .env

# 5. Run the server
uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000` for the UI and `http://localhost:8000/docs` for Swagger.

---

## 🐳 Running with Docker

```bash
docker build -t tu-notice-hub .
docker run -p 7860:7860 -e MONGO_DETAILS="your_connection_string" tu-notice-hub
```

---

## 📁 Project Structure

```
tu-notice-hub/
├── app/
│   ├── __init__.py
│   ├── main.py        # FastAPI app, routes, auto-scraper loop
│   ├── database.py    # MongoDB connection
│   └── scraper.py     # Web scraper for TU and FoHSS
├── templates/
│   └── index.html     # Web UI
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 🤝 Built With

- [FastAPI](https://fastapi.tiangolo.com/) — API framework
- [Motor](https://motor.readthedocs.io/) — Async MongoDB driver
- [MongoDB Atlas](https://www.mongodb.com/atlas) — Database
- [httpx](https://www.python-httpx.org/) — Async HTTP client
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) — HTML parser
- [Hugging Face Spaces](https://huggingface.co/spaces) — Hosting

---

*Built by [samratghimire01](https://huggingface.co/samratghimire01) — data sourced from [tu.edu.np](https://tu.edu.np) and [fohss.tu.edu.np](https://fohss.tu.edu.np)*