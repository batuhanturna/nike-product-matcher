from sentence_transformers import SentenceTransformer

from database import create_table, add_product, product_exists
from matching_text import build_matching_text
from scraper import scrape_product_info


MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def main():
    create_table()

    print("Loading model...")
    model = SentenceTransformer(MODEL_NAME)

    while True:
        url = input("\nEnter Nike product URL or q to quit: ").strip()

        if url.lower() in ["q", "quit", "exit"]:
            print("Exiting...")
            break

        if not url:
            print("Please enter a product URL.")
            continue

        if product_exists(url):
            print("This product already exists in the database.")
            continue

        category = input("Enter category, for example Shoes > Running: ").strip()

        try:
            print("\nScraping product...")
            info = scrape_product_info(url)

            print("\nProduct name:")
            print(info.get("name"))

            print("\nImage URL:")
            print(info.get("image_url"))

            print("\nDescription source:")
            print(info.get("description_source"))

            matching_text = build_matching_text(
                name=info.get("name"),
                category=category,
                description=info.get("description")
            )

            print("\nCreating embedding...")
            embedding = model.encode(matching_text).tolist()

            add_product(
                name=info.get("name"),
                description=info.get("description"),
                category=category,
                url=url,
                embedding=embedding,
                image_url=info.get("image_url")
            )

            print("\nProduct added successfully.")

        except Exception as error:
            print("\nCould not add product.")
            print(f"Error: {error}")


if __name__ == "__main__":
    main()
