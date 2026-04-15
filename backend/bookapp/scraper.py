"""
Book Scraper Module
====================
Scrapes book data from books.toscrape.com using Selenium + BeautifulSoup.

Features:
  - Multi-page bulk scraping (up to 50 pages / ~1000 books)
  - Detail page scraping for description and genre
  - Polite rate limiting between requests
  - Context manager interface for clean driver lifecycle
"""

import logging
import re
import time
from typing import Optional

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
# Constants
# ---------------------------------------------------------------
BASE_URL = "http://books.toscrape.com"
CATALOGUE_BASE = f"{BASE_URL}/catalogue"

# Maps star-rating CSS class words to numeric values
RATING_MAP = {
    "Zero": 0.0,
    "One": 1.0,
    "Two": 2.0,
    "Three": 3.0,
    "Four": 4.0,
    "Five": 5.0,
}


# ---------------------------------------------------------------
# WebDriver Factory
# ---------------------------------------------------------------
def create_driver(headless: bool = True) -> webdriver.Chrome:
    """
    Create and return a configured Chrome WebDriver.

    Args:
        headless: Run Chrome without a visible window (default True).

    Returns:
        Configured webdriver.Chrome instance.
    """
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    # Suppress unnecessary log output
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver


# ---------------------------------------------------------------
# Page Parsers
# ---------------------------------------------------------------
def _build_cover_url(src: str) -> str:
    """Convert relative cover image path to absolute URL."""
    if not src:
        return ""
    # Remove leading ../ sequences (e.g., ../../media/ -> /media/)
    cleaned = re.sub(r"^(\.\./)+", "/", src)
    if cleaned.startswith("http"):
        return cleaned
    return f"{BASE_URL}{cleaned}"


def parse_listing_page(html: str) -> list[dict]:
    """
    Parse book listings from a catalogue page.

    Args:
        html: Raw HTML of the catalogue page.

    Returns:
        List of dicts with: title, book_url, rating, price, cover_image.
    """
    soup = BeautifulSoup(html, "html.parser")
    books = []

    for article in soup.find_all("article", class_="product_pod"):
        try:
            # Title and detail URL
            h3 = article.find("h3")
            a_tag = h3.find("a") if h3 else None
            if not a_tag:
                continue

            title = a_tag.get("title", a_tag.text.strip())
            href = a_tag.get("href", "")
            # The href is relative to /catalogue/, strip any leading ../
            href = re.sub(r"^(\.\./)+", "", href)
            book_url = f"{CATALOGUE_BASE}/{href}"

            # Star rating from CSS class (e.g., "star-rating Three")
            rating_tag = article.find("p", class_="star-rating")
            rating_classes = rating_tag.get("class", []) if rating_tag else []
            rating_word = rating_classes[1] if len(rating_classes) > 1 else "Zero"
            rating = RATING_MAP.get(rating_word, 0.0)

            # Price
            price_tag = article.find("p", class_="price_color")
            price = price_tag.text.strip() if price_tag else ""

            # Cover image
            img_tag = article.find("img")
            cover_image = _build_cover_url(img_tag.get("src", "")) if img_tag else ""

            books.append(
                {
                    "title": title,
                    "book_url": book_url,
                    "rating": rating,
                    "price": price,
                    "cover_image": cover_image,
                }
            )
        except Exception as exc:
            logger.warning(f"Error parsing book article: {exc}")
            continue

    return books


def parse_detail_page(html: str) -> dict:
    """
    Parse the detail page of a single book.

    Args:
        html: Raw HTML of the book detail page.

    Returns:
        Dict with: description, genre, author, num_reviews, availability.
    """
    soup = BeautifulSoup(html, "html.parser")
    result = {
        "description": "",
        "genre": "",
        "author": "Unknown",
        "num_reviews": 0,
        "availability": "",
    }

    # Description (paragraph after the #product_description header)
    desc_div = soup.find("div", id="product_description")
    if desc_div:
        desc_p = desc_div.find_next_sibling("p")
        if desc_p:
            result["description"] = desc_p.text.strip()

    # Genre from breadcrumb: Home > Genre > Book Title
    breadcrumb = soup.find("ul", class_="breadcrumb")
    if breadcrumb:
        crumbs = breadcrumb.find_all("li")
        # Index 2 is genre (0=Home, 1=Books, 2=Genre, 3=BookTitle)
        if len(crumbs) >= 3:
            result["genre"] = crumbs[2].text.strip()

    # Table data (availability, num_reviews)
    table = soup.find("table", class_="table-striped")
    if table:
        for row in table.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if not (th and td):
                continue
            label = th.text.strip()
            value = td.text.strip()
            if label == "Availability":
                result["availability"] = value
            elif label == "Number of reviews":
                try:
                    result["num_reviews"] = int(value)
                except ValueError:
                    result["num_reviews"] = 0

    return result


def get_total_pages(driver: webdriver.Chrome) -> int:
    """Get the total number of catalogue pages from the pager widget."""
    try:
        driver.get(f"{CATALOGUE_BASE}/page-1.html")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article.product_pod"))
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")
        pager = soup.find("li", class_="current")
        if pager:
            match = re.search(r"of\s+(\d+)", pager.text)
            if match:
                return int(match.group(1))
    except Exception as exc:
        logger.warning(f"Could not determine total pages: {exc}")
    return 50  # books.toscrape.com has 50 pages


# ---------------------------------------------------------------
# Main Scraper Class
# ---------------------------------------------------------------
class BookScraper:
    """
    Context-manager scraper for books.toscrape.com.

    Usage:
        with BookScraper(headless=True) as scraper:
            books = scraper.scrape_all_books(max_pages=5)
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None

    def __enter__(self) -> "BookScraper":
        self.driver = create_driver(self.headless)
        logger.info("Selenium WebDriver started.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            self.driver.quit()
            logger.info("Selenium WebDriver closed.")

    def _load_page(self, url: str, wait_selector: str = "article.product_pod") -> str:
        """Load a URL and wait for a CSS selector to be present. Returns page HTML."""
        self.driver.get(url)
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
            )
        except TimeoutException:
            logger.warning(f"Timeout waiting for {wait_selector} on {url}")
        return self.driver.page_source

    def scrape_all_books(self, max_pages: Optional[int] = None) -> list[dict]:
        """
        Full bulk scraping pipeline:
        Phase 1 — Scrape all listing pages to collect book URLs and metadata.
        Phase 2 — Visit each book's detail page to get description and genre.

        Args:
            max_pages: Limit the number of catalogue pages to scrape.
                       None means scrape all pages (up to 50).

        Returns:
            List of complete book dicts ready for DB insertion.
        """
        if not self.driver:
            raise RuntimeError("Use BookScraper as a context manager.")

        total_pages = get_total_pages(self.driver)
        if max_pages:
            total_pages = min(max_pages, total_pages)

        logger.info(f"=== Phase 1: Scraping {total_pages} listing pages ===")
        all_books = []

        for page_num in range(1, total_pages + 1):
            page_url = f"{CATALOGUE_BASE}/page-{page_num}.html"
            logger.info(f"Listing page {page_num}/{total_pages}: {page_url}")
            try:
                html = self._load_page(page_url)
                books = parse_listing_page(html)
                all_books.extend(books)
                logger.debug(f"  → {len(books)} books found on page {page_num}")
                time.sleep(0.4)  # Polite delay between listing pages
            except WebDriverException as exc:
                logger.error(f"Driver error on page {page_num}: {exc}")
                continue

        logger.info(f"Phase 1 complete. Total books collected: {len(all_books)}")
        logger.info(f"=== Phase 2: Fetching {len(all_books)} detail pages ===")

        for i, book in enumerate(all_books):
            try:
                logger.info(f"Detail {i + 1}/{len(all_books)}: {book['title']}")
                html = self._load_page(book["book_url"], wait_selector=".product_main")
                detail = parse_detail_page(html)
                book.update(detail)
                time.sleep(0.3)  # Polite delay between detail pages
            except Exception as exc:
                logger.error(f"Detail scrape failed for '{book.get('title')}': {exc}")
                book.update(
                    {
                        "description": "",
                        "genre": "",
                        "author": "Unknown",
                        "num_reviews": 0,
                        "availability": "",
                    }
                )

        logger.info(f"=== Scraping complete. {len(all_books)} books ready. ===")
        return all_books
