import time
from sentence_transformers import SentenceTransformer

from database import get_all_products, update_product
from matching_text import build_matching_text
from scraper import scrape_product_info


MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def main():
    products = get_all_products()

    print(f"Products found in database: {len(products)}")

    if not products:
        print("Database is empty.")
        return

    print("Loading model...")
    model = SentenceTransformer(MODEL_NAME)

    updated_count = 0
    failed_count = 0

    for index, product in enumerate(products, start=1):
        print("\n" + "=" * 80)
        print(f"[{index}/{len(products)}] Refreshing:")
        print(product["url"])

        if not product["url"] or not product["url"].startswith("http"):
            print("No valid URL. Skipping.")
            failed_count += 1
            continue

        try:
            info = scrape_product_info(product["url"])

            name = info["name"] or product["name"]
            category = product["category"]
            description = info["description"]

            matching_text = build_matching_text(
                name=name,
                category=category,
                description=description
            )

            embedding = model.encode(matching_text).tolist()

            update_product(
                product_id=product["id"],
                name=name,
                description=description,
                category=category,
                url=product["url"],
                embedding=embedding
            )

            print(f"Updated: {name}")
            print(f"Description source: {info['description_source']}")
            print(f"Description: {description[:250]}...")

            updated_count += 1
            time.sleep(1.5)

        except Exception as error:
            print("Could not refresh this product.")
            print(f"Error: {error}")
            failed_count += 1
            time.sleep(1.5)

    print("\n" + "=" * 80)
    print("Refresh finished.")
    print(f"Updated: {updated_count}")
    print(f"Failed: {failed_count}")


if __name__ == "__main__":
    main()
