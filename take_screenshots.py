from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8000"
OUT_DIR = Path("screenshots")
OUT_DIR.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1366, "height": 900})
    page.goto(URL)

    # Wait until the table is filled with books
    page.wait_for_selector("#tableBody a")

    # 1) Light mode
    page.screenshot(path=str(OUT_DIR / "dashboard-light.png"))

    # 2) Search example
    page.fill("#searchInput", "love")
    page.wait_for_timeout(300)
    page.screenshot(path=str(OUT_DIR / "search.png"))

    # 3) Dark mode
    page.fill("#searchInput", "")
    page.click("#themeToggle")
    page.wait_for_timeout(500)
    page.screenshot(path=str(OUT_DIR / "dashboard-dark.png"))

    browser.close()

print("Saved 3 screenshots in the 'screenshots' folder.")