from sentence_transformers import SentenceTransformer

from database import create_table, add_product
from matching_text import build_matching_text
from scraper import scrape_product_info


MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def main():
    print("Add product from URL")
    print("Type 'q' to exit.")

    create_table()

    print("Loading model...")
    model = SentenceTransformer(MODEL_NAME)

    while True:
        print("\n" + "=" * 60)

        url = input("Enter product URL: ").strip()

        if url.lower() == "q":
            print("Program closed.")
            break

        if not url.startswith("http"):
            print("Please enter a valid URL.")
            continue

        category = input("Enter category, for example Shoes, T-Shirt, Hoodie: ").strip()

        try:
            print("\nScraping product info...")
            info = scrape_product_info(url)

            name = info["name"] or input("Could not detect name. Enter product name: ").strip()
            description = info["description"]

            print("\nExtracted info:")
            print(f"Name: {name}")
            print(f"Description source: {info['description_source']}")
            print(f"Description: {description}")

            matching_text = build_matching_text(
                name=name,
                category=category,
                description=description
            )

            print("\nCreating embedding from name + category + description...")
            embedding = model.encode(matching_text).tolist()

            add_product(
                name=name,
                description=description,
                category=category,
                url=url,
                embedding=embedding
            )

            print(f"\nProduct added to database: {name}")

        except Exception as error:
            print("\nCould not add product.")
            print(f"Error: {error}")


if __name__ == "__main__":
    main()
