import time
from urllib.parse import urljoin

from sentence_transformers import SentenceTransformer
from playwright.sync_api import sync_playwright

from database import create_table, add_product, product_exists
from matching_text import build_matching_text
from scraper import scrape_product_info


MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def normalize_nike_url(url):
    if not url:
        return None

    if url.startswith("/"):
        return urljoin("https://www.nike.com", url)

    return url


def collect_product_links(category_url, limit=30):
    product_links = []
    seen = set()

    print("\nOpening category page...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            viewport={"width": 1366, "height": 900},
        )

        page = context.new_page()
        page.goto(category_url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4000)

        for scroll_index in range(12):
            links = page.eval_on_selector_all(
                "a[href]",
                """
                elements => elements
                    .map(element => element.href)
                    .filter(href => href && href.includes('/t/'))
                """
            )

            for link in links:
                normalized = normalize_nike_url(link)

                if not normalized:
                    continue

                clean_link = normalized.split("?")[0]

                if clean_link in seen:
                    continue

                seen.add(clean_link)
                product_links.append(clean_link)

                if len(product_links) >= limit:
                    browser.close()
                    return product_links

            page.mouse.wheel(0, 2500)
            page.wait_for_timeout(1200)

            print(f"Scroll {scroll_index + 1}: found {len(product_links)} product links")

        browser.close()

    return product_links


def main():
    create_table()

    category_url = input("Enter Nike category URL: ").strip()
    category = input("Enter category name, for example Shoes > Running: ").strip()

    limit_text = input("How many product links should be collected? Default 30: ").strip()

    if limit_text:
        limit = int(limit_text)
    else:
        limit = 30

    print("Loading model...")
    model = SentenceTransformer(MODEL_NAME)

    product_links = collect_product_links(category_url, limit=limit)

    print("\n" + "=" * 80)
    print(f"Collected {len(product_links)} product links.")

    added_count = 0
    skipped_count = 0
    failed_count = 0

    for index, product_url in enumerate(product_links, start=1):
        print("\n" + "=" * 80)
        print(f"[{index}/{len(product_links)}] {product_url}")

        if product_exists(product_url):
            print("Skipped because this product already exists.")
            skipped_count += 1
            continue

        try:
            print("Scraping product...")
            info = scrape_product_info(product_url)

            matching_text = build_matching_text(
                name=info.get("name"),
                category=category,
                description=info.get("description")
            )

            print("Creating embedding...")
            embedding = model.encode(matching_text).tolist()

            add_product(
                name=info.get("name"),
                description=info.get("description"),
                category=category,
                url=product_url,
                embedding=embedding,
                image_url=info.get("image_url")
            )

            print("Added successfully.")
            print(f"Name: {info.get('name')}")
            print(f"Image URL: {info.get('image_url')}")

            added_count += 1
            time.sleep(2)

        except Exception as error:
            print("Failed to add product.")
            print(f"Error: {error}")
            failed_count += 1

    print("\n" + "=" * 80)
    print("Bulk import finished.")
    print(f"Added: {added_count}")
    print(f"Skipped: {skipped_count}")
    print(f"Failed: {failed_count}")


if __name__ == "__main__":
    main()
