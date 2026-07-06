import time
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright
from sentence_transformers import SentenceTransformer

from database import create_table, add_product, product_exists
from matching_text import build_matching_text
from scraper import scrape_product_info


MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def clean_url(url):
    parsed = urlparse(url)
    return parsed._replace(query="", fragment="").geturl()


def is_nike_product_url(url):
    parsed = urlparse(url)
    path = parsed.path.lower()

    return "nike.com" in parsed.netloc and "/t/" in path


def collect_product_links(category_url, limit=50):
    product_links = []
    seen_links = set()

    print("Opening category page with Playwright...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(category_url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000)

        print("Collecting product links...")

        previous_count = 0

        for scroll_index in range(30):
            hrefs = page.locator("a").evaluate_all(
                """elements => elements.map(element => element.href).filter(Boolean)"""
            )

            for href in hrefs:
                url = clean_url(urljoin(category_url, href))

                if is_nike_product_url(url) and url not in seen_links:
                    seen_links.add(url)
                    product_links.append(url)

                    print(f"Found product link: {url}")

                    if len(product_links) >= limit:
                        browser.close()
                        return product_links

            page.mouse.wheel(0, 3500)
            page.wait_for_timeout(1500)

            if len(product_links) == previous_count:
                print(f"Scroll {scroll_index + 1}: no new links found.")
            else:
                print(f"Scroll {scroll_index + 1}: total links found = {len(product_links)}")

            previous_count = len(product_links)

        browser.close()

    return product_links[:limit]


def add_products_to_database(product_links, category):
    create_table()

    print("Loading model...")
    model = SentenceTransformer(MODEL_NAME)

    added_count = 0
    skipped_count = 0
    failed_count = 0

    for index, url in enumerate(product_links, start=1):
        print("\n" + "=" * 80)
        print(f"[{index}/{len(product_links)}] Processing:")
        print(url)

        if product_exists(url):
            print("Already exists in database. Skipping.")
            skipped_count += 1
            continue

        try:
            info = scrape_product_info(url)

            name = info["name"]
            description = info["description"]

            if not description or len(description) < 20:
                print("Description is too short or empty. Skipping.")
                failed_count += 1
                continue

            matching_text = build_matching_text(
                name=name,
                category=category,
                description=description
            )

            embedding = model.encode(matching_text).tolist()

            add_product(
                name=name,
                description=description,
                category=category,
                url=url,
                embedding=embedding
            )

            print(f"Added: {name}")
            print(f"Description source: {info['description_source']}")
            print(f"Description: {description[:250]}...")

            added_count += 1
            time.sleep(2)

        except Exception as error:
            print("Could not process this product.")
            print(f"Error: {error}")
            failed_count += 1
            time.sleep(2)

    print("\n" + "=" * 80)
    print("Bulk import finished.")
    print(f"Added: {added_count}")
    print(f"Skipped existing: {skipped_count}")
    print(f"Failed: {failed_count}")


def main():
    print("Nike Bulk Product Import From Category Page")
    print("This script collects product links from a Nike category page and adds them to the database.")

    category_url = input("Enter Nike category page URL: ").strip()
    category = input("Enter category name, for example Shoes, T-Shirt, Hoodie: ").strip()
    limit_input = input("How many products should be collected? Default is 50: ").strip()

    if not category_url.startswith("http"):
        print("Please enter a valid category URL.")
        return

    if not category:
        category = "Unknown"

    if limit_input:
        try:
            limit = int(limit_input)
        except ValueError:
            limit = 50
    else:
        limit = 50

    product_links = collect_product_links(category_url, limit=limit)

    print("\nCollected product links:")
    for link in product_links:
        print(link)

    print(f"\nTotal collected links: {len(product_links)}")

    if not product_links:
        print("No product links found. The website structure may require a different selector.")
        return

    add_products_to_database(product_links, category)


if __name__ == "__main__":
    main()
