print("main.py started")

from database import create_table
from matcher import ProductMatcher
from matching_text import build_matching_text
from scraper import scrape_product_info


def print_product(product, index):
    print("-" * 60)
    print(f"{index}. {product['name']}")
    print(f"Category: {product['category']}")
    print(f"Similarity score: {product['score']:.4f}")
    print(f"Description: {product['description']}")
    print(f"URL: {product['url']}")


def print_results(results):
    print("\nSimilar products:")

    if not results:
        print("No similar products found.")
        return

    for index, product in enumerate(results, start=1):
        print_product(product, index)


def main():
    create_table()

    matcher = ProductMatcher()

    print("\nProduct Similarity System")
    print("Type 'q' to exit.")

    while True:
        print("\n" + "=" * 60)
        print("1 - Enter product description manually")
        print("2 - Enter product URL")
        print("q - Exit")

        choice = input("Choose an option: ").strip().lower()

        if choice == "q":
            print("Program closed.")
            break

        if choice == "1":
            query = input("Enter product description: ")

            if len(query.strip()) < 10:
                print("Please enter a longer product description.")
                continue

            results = matcher.find_similar_products(query, top_k=5)
            print_results(results)

        elif choice == "2":
            url = input("Enter product URL: ").strip()

            if not url.startswith("http"):
                print("Please enter a valid URL.")
                continue

            try:
                info = scrape_product_info(url)

                print("\nExtracted product info:")
                print("-" * 60)
                print(f"Name: {info['name']}")
                print(f"Description source: {info['description_source']}")
                print(f"Description: {info['description']}")
                print("-" * 60)

                query_text = build_matching_text(
                    name=info["name"],
                    category=None,
                    description=info["description"]
                )

                results = matcher.find_similar_products(
                    query_text,
                    top_k=5,
                    exclude_url=url
                )

                print_results(results)

            except Exception as error:
                print("\nCould not scrape product description.")
                print(f"Error: {error}")

        else:
            print("Invalid option. Please choose 1, 2, or q.")


if __name__ == "__main__":
    main()
