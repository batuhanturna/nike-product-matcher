import time

from sentence_transformers import SentenceTransformer

from database import create_table, get_all_products, update_product
from matching_text import build_matching_text
from scraper import scrape_product_info


MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def main():
    create_table()

    products = get_all_products()

    if not products:
        print("Database is empty.")
        return

    print("Loading model...")
    model = SentenceTransformer(MODEL_NAME)

    print(f"Found {len(products)} products in database.")

    updated_count = 0
    failed_count = 0
    skipped_count = 0

    for index, product in enumerate(products, start=1):
        product_id = product.get("id")
        url = product.get("url")
        category = product.get("category")

        print("\n" + "=" * 80)
        print(f"[{index}/{len(products)}] Product ID: {product_id}")
        print(f"URL: {url}")

        if not url:
            print("Skipped because this product has no URL.")
            skipped_count += 1
            continue

        try:
            print("Scraping latest product info...")
            info = scrape_product_info(url)

            matching_text = build_matching_text(
                name=info.get("name"),
                category=category,
                description=info.get("description")
            )

            print("Creating new embedding...")
            embedding = model.encode(matching_text).tolist()

            update_product(
                product_id=product_id,
                name=info.get("name"),
                description=info.get("description"),
                category=category,
                url=url,
                embedding=embedding,
                image_url=info.get("image_url")
            )

            print("Updated successfully.")
            print(f"Name: {info.get('name')}")
            print(f"Image URL: {info.get('image_url')}")

            updated_count += 1
            time.sleep(2)

        except Exception as error:
            print("Update failed.")
            print(f"Error: {error}")
            failed_count += 1

    print("\n" + "=" * 80)
    print("Refresh finished.")
    print(f"Updated: {updated_count}")
    print(f"Failed: {failed_count}")
    print(f"Skipped: {skipped_count}")


if __name__ == "__main__":
    main()
