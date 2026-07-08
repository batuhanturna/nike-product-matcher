import time
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from sentence_transformers import SentenceTransformer

from database import create_table, add_product, product_exists, get_all_products
from matching_text import build_matching_text
from scraper import scrape_product_info


MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

DEFAULT_TARGET_DATABASE_TOTAL = 200
DEFAULT_CATEGORY_LIMIT = 60


def clean_url(url):
    parsed = urlparse(url)
    return parsed._replace(query="", fragment="").geturl()


def is_nike_product_url(url):
    parsed = urlparse(url)
    path = parsed.path.lower()

    return "nike.com" in parsed.netloc and "/t/" in path


def safe_goto(page, url):
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=70000)
        return
    except PlaywrightTimeoutError:
        print("Page load timed out. Trying lighter load mode...")

    try:
        page.goto(url, wait_until="commit", timeout=70000)
        return
    except PlaywrightTimeoutError:
        print("Page still timed out. Continuing with current page content...")


def accept_cookies_if_visible(page):
    possible_texts = [
        "Accept All",
        "Accept all",
        "Tümünü kabul et",
        "Kabul et",
        "Allow All",
        "Agree",
    ]

    for text in possible_texts:
        try:
            button = page.get_by_text(text, exact=False).first

            if button.is_visible(timeout=2000):
                button.click(timeout=3000)
                page.wait_for_timeout(1000)
                return
        except Exception:
            pass


def collect_product_links(category_url, limit):
    product_links = []
    seen_links = set()

    print("\nOpening category page:")
    print(category_url)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="tr-TR",
            viewport={"width": 1366, "height": 900},
        )

        page = context.new_page()

        safe_goto(page, category_url)
        page.wait_for_timeout(4000)

        accept_cookies_if_visible(page)

        previous_count = -1
        no_new_scroll_count = 0

        print("Collecting product links...")

        for scroll_index in range(50):
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

            print(f"Scroll {scroll_index + 1}: total links found = {len(product_links)}")

            if len(product_links) == previous_count:
                no_new_scroll_count += 1
            else:
                no_new_scroll_count = 0

            if no_new_scroll_count >= 8 and len(product_links) > 0:
                print("No new links after several scrolls. Stopping this category.")
                break

            previous_count = len(product_links)

            page.mouse.wheel(0, 3500)
            page.wait_for_timeout(1500)

        browser.close()

    return product_links[:limit]


def add_products_to_database(product_links, category, model, target_database_total):
    added_count = 0
    skipped_count = 0
    failed_count = 0

    for index, url in enumerate(product_links, start=1):
        current_total = len(get_all_products())

        if current_total >= target_database_total:
            print("\nTarget database total reached.")
            break

        print("\n" + "=" * 90)
        print(f"[{index}/{len(product_links)}] Processing:")
        print(url)
        print(f"Current database total: {current_total}/{target_database_total}")

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
            print(f"Category: {category}")
            print(f"Description source: {info['description_source']}")
            print(f"Description: {description[:250]}...")

            added_count += 1
            time.sleep(1.5)

        except Exception as error:
            print("Could not process this product.")
            print(f"Error: {error}")
            failed_count += 1
            time.sleep(1.5)

    return added_count, skipped_count, failed_count


def ask_categories():
    categories = []

    print("\nYou will enter Nike category URLs.")
    print("Example categories: Shoes, Running, Football, Jordan, Clothing, Accessories")
    print("Paste the real category URL from Nike website.")

    category_count_text = input("\nHow many categories will you enter? Example 4 or 5: ").strip()

    try:
        category_count = int(category_count_text)
    except ValueError:
        category_count = 4

    for index in range(1, category_count + 1):
        print("\n" + "-" * 70)
        print(f"Category {index}")

        category_name = input("Category name, example Shoes, Running, Football: ").strip()
        category_url = input("Nike category URL: ").strip()
        limit_text = input(f"Product link limit for this category. Default {DEFAULT_CATEGORY_LIMIT}: ").strip()

        if not category_name:
            category_name = "Unknown"

        if not category_url.startswith("http"):
            print("Invalid category URL. This category will be skipped.")
            continue

        if limit_text:
            try:
                limit = int(limit_text)
            except ValueError:
                limit = DEFAULT_CATEGORY_LIMIT
        else:
            limit = DEFAULT_CATEGORY_LIMIT

        categories.append({
            "name": category_name,
            "url": category_url,
            "limit": limit
        })

    return categories


def print_database_summary():
    products = get_all_products()

    category_counts = {}

    for product in products:
        category = product["category"] or "Unknown"
        category_counts[category] = category_counts.get(category, 0) + 1

    print("\n" + "=" * 90)
    print("Database summary")
    print(f"Total products: {len(products)}")

    for category, count in sorted(category_counts.items()):
        print(f"{category}: {count}")


def main():
    create_table()

    print("Nike Multi-Category Bulk Import")
    print("This script adds products from multiple Nike categories into products.db.")

    current_total = len(get_all_products())

    print(f"\nCurrent database total: {current_total}")

    target_text = input(
        f"Target total product count in database. Default {DEFAULT_TARGET_DATABASE_TOTAL}: "
    ).strip()

    if target_text:
        try:
            target_database_total = int(target_text)
        except ValueError:
            target_database_total = DEFAULT_TARGET_DATABASE_TOTAL
    else:
        target_database_total = DEFAULT_TARGET_DATABASE_TOTAL

    if current_total >= target_database_total:
        print("Database already reached the target total.")
        print_database_summary()
        return

    categories = ask_categories()

    if not categories:
        print("No valid categories entered.")
        return

    print("\nLoading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    total_added = 0
    total_skipped = 0
    total_failed = 0

    for category in categories:
        current_total = len(get_all_products())

        if current_total >= target_database_total:
            print("\nTarget database total reached. Stopping.")
            break

        print("\n" + "#" * 90)
        print(f"Starting category: {category['name']}")
        print(f"URL: {category['url']}")
        print(f"Limit: {category['limit']}")
        print("#" * 90)

        product_links = collect_product_links(
            category_url=category["url"],
            limit=category["limit"]
        )

        print(f"\nCollected links for {category['name']}: {len(product_links)}")

        if not product_links:
            print("No product links found for this category.")
            continue

        added, skipped, failed = add_products_to_database(
            product_links=product_links,
            category=category["name"],
            model=model,
            target_database_total=target_database_total
        )

        total_added += added
        total_skipped += skipped
        total_failed += failed

    print("\n" + "=" * 90)
    print("Multi-category import finished.")
    print(f"Added: {total_added}")
    print(f"Skipped existing: {total_skipped}")
    print(f"Failed: {total_failed}")

    print_database_summary()


if __name__ == "__main__":
    main()