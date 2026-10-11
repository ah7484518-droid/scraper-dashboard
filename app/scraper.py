from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BASE_URL = "https://books.toscrape.com/catalogue/page-{}.html"

RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def parse_books(html: str, page_url: str) -> list[dict]:
    """Read one page of HTML and return a list of books."""
    soup = BeautifulSoup(html, "html.parser")
    books = []

    for item in soup.select("article.product_pod"):
        link = item.select_one("h3 a")
        price_text = item.select_one("p.price_color").get_text(strip=True)
        rating_word = item.select_one("p.star-rating")["class"][1]
        availability = item.select_one("p.availability").get_text(strip=True)

        books.append(
            {
                "title": link["title"],
                "price": float(price_text.replace("£", "").replace("Â", "")),
                "rating": RATING_MAP.get(rating_word, 0),
                "availability": availability,
                "url": urljoin(page_url, link["href"]),
            }
        )

    return books


def scrape_books(max_pages: int = 50) -> list[dict]:
    """Open a real browser, visit each page, and collect all books."""
    all_books = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for page_number in range(1, max_pages + 1):
            url = BASE_URL.format(page_number)
            print(f"Scraping page {page_number} ...")
            response = page.goto(url)

            if response is None or response.status != 200:
                print("No more pages, stopping.")
                break

            all_books.extend(parse_books(page.content(), url))

        browser.close()

    return all_books


if __name__ == "__main__":
    # Quick test: scrape only 2 pages
    results = scrape_books(max_pages=2)
    print(f"Total books: {len(results)}")
    for book in results[:3]:
        print(book)