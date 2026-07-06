from scraper import scrape_product_description_with_source


def main():
    print("Nike Product Description Debug Tool")
    print("Type 'q' to exit.")

    while True:
        print("\n" + "=" * 80)
        url = input("Enter product URL: ").strip()

        if url.lower() == "q":
            print("Program closed.")
            break

        if not url.startswith("http"):
            print("Please enter a valid URL.")
            continue

        try:
            result = scrape_product_description_with_source(url)

            print("\nProduct name:")
            print(result.get("name"))

            print("\nSource:")
            print(result["source"])

            print("\nExtracted description:")
            print("-" * 80)
            print(result["description"])
            print("-" * 80)
            print(f"Character count: {len(result['description'])}")

        except Exception as error:
            print("Could not scrape product description.")
            print(f"Error: {error}")


if __name__ == "__main__":
    main()
