import time
from urllib.parse import urljoin

from sentence_transformers import SentenceTransformer
from playwright.sync_api import sync_playwright

from database import create_table, add_product, product_exists, get_all_products
from matching_text import build_matching_text
from scraper import scrape_product_info


MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_TARGET_DATABASE_TOTAL = 200
DEFAULT_CATEGORY_LIMIT = 60


def normalize_nike_url(url):
    if not url:
        return None

    if url.startswith("/"):
        return urljoin("https://www.nike.com", url)

    return url


def collect_product_links(category_url, limit=60):
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

        for scroll_index in range(14):
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


def ask_categories():
    categories = []

    category_count_text = input("How many categories will you enter? ").strip()
    category_count = int(category_count_text)

    for index in range(category_count):
        print("\n" + "=" * 80)
        print(f"Category {index + 1}/{category_count}")

        category_name = input("Category name, for example Shoes > Running: ").strip()
        category_url = input("Nike category URL: ").strip()
        limit_text = input(f"Product link limit for this category. Default {DEFAULT_CATEGORY_LIMIT}: ").strip()

        if limit_text:
            limit = int(limit_text)
        else:
            limit = DEFAULT_CATEGORY_LIMIT

        categories.append({
            "name": category_name,
            "url": category_url,
            "limit": limit
        })

    return categories


def main():
    create_table()

    target_text = input(f"Target total products in database. Default {DEFAULT_TARGET_DATABASE_TOTAL}: ").strip()

    if target_text:
        target_total = int(target_text)
    else:
        target_total = DEFAULT_TARGET_DATABASE_TOTAL

    categories = ask_categories()

    print("\nLoading model...")
    model = SentenceTransformer(MODEL_NAME)

    added_count = 0
    skipped_count = 0
    failed_count = 0

    for category in categories:
        current_total = len(get_all_products())

        if current_total >= target_total:
            print(f"\nTarget reached. Current database total: {current_total}")
            break

        category_name = category["name"]
        category_url = category["url"]
        category_limit = category["limit"]

        print("\n" + "#" * 80)
        print(f"Collecting category: {category_name}")
        print(f"URL: {category_url}")

        product_links = collect_product_links(category_url, limit=category_limit)

        print(f"Collected {len(product_links)} links for {category_name}")

        for index, product_url in enumerate(product_links, start=1):
            current_total = len(get_all_products())

            if current_total >= target_total:
                print(f"\nTarget reached. Current database total: {current_total}")
                break

            print("\n" + "=" * 80)
            print(f"Category: {category_name}")
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
                    category=category_name,
                    description=info.get("description")
                )

                print("Creating embedding...")
                embedding = model.encode(matching_text).tolist()

                add_product(
                    name=info.get("name"),
                    description=info.get("description"),
                    category=category_name,
                    url=product_url,
                    embedding=embedding,
                    image_url=info.get("image_url")
                )

                print("Added successfully.")
                print(f"Name: {info.get('name')}")
                print(f"Image URL: {info.get('image_url')}")
                print(f"Current database total: {len(get_all_products())}")

                added_count += 1
                time.sleep(2)

            except Exception as error:
                print("Failed to add product.")
                print(f"Error: {error}")
                failed_count += 1

    print("\n" + "=" * 80)
    print("Multi-category import finished.")
    print(f"Added: {added_count}")
    print(f"Skipped: {skipped_count}")
    print(f"Failed: {failed_count}")
    print(f"Current database total: {len(get_all_products())}")


if __name__ == "__main__":
    main()
