import csv
import io
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from openpyxl import Workbook

from app.database import get_all_books, init_db, save_books
from app.scraper import scrape_books

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the server starts: make sure the database tables exist
    init_db()
    yield


app = FastAPI(title="Scraper Dashboard", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Simple in-memory status so the UI can show progress
scrape_status = {"running": False, "message": "Idle", "count": 0}

EXPORT_COLUMNS = ["Title", "Price", "Rating", "Availability", "URL", "Scraped At"]


def run_scrape_job() -> None:
    """Scrape all pages and save them. Runs in the background."""
    scrape_status.update(running=True, message="Scraping in progress...", count=0)
    try:
        books = scrape_books()
        saved = save_books(books)
        scrape_status.update(message=f"Done. Saved {saved} books.", count=saved)
    except Exception as exc:
        scrape_status.update(message=f"Error: {exc}")
    finally:
        scrape_status["running"] = False


def books_as_rows() -> list[list]:
    return [
        [
            b["title"],
            b["price"],
            b["rating"],
            b["availability"],
            b["url"],
            b["scraped_at"],
        ]
        for b in get_all_books()
    ]


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/scrape")
def start_scrape(background_tasks: BackgroundTasks):
    if scrape_status["running"]:
        raise HTTPException(status_code=409, detail="A scrape is already running")
    background_tasks.add_task(run_scrape_job)
    return {"message": "Scraping started"}


@app.get("/api/status")
def get_status():
    return scrape_status


@app.get("/api/books")
def list_books():
    return get_all_books()


@app.get("/api/export/csv")
def export_csv():
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(EXPORT_COLUMNS)
    writer.writerows(books_as_rows())

    # utf-8-sig so Excel opens the file with the correct characters
    content = buffer.getvalue().encode("utf-8-sig")
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=books.csv"},
    )


@app.get("/api/export/excel")
def export_excel():
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Books"
    sheet.append(EXPORT_COLUMNS)
    for row in books_as_rows():
        sheet.append(row)

    buffer = io.BytesIO()
    workbook.save(buffer)
    return Response(
        content=buffer.getvalue(),
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers={"Content-Disposition": "attachment; filename=books.xlsx"},
    )