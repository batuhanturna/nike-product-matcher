from scraper import scrape_product_info


def main():
    while True:
        url = input("Enter product URL or q to quit: ").strip()

        if url.lower() in ["q", "quit", "exit"]:
            print("Exiting...")
            break

        if not url:
            print("Please enter a product URL or q to quit.")
            continue

        try:
            product_info = scrape_product_info(url)

            print("\nProduct name:")
            print(product_info.get("name"))

            print("\nSource:")
            print(product_info.get("description_source"))

            print("\nImage URL:")
            print(product_info.get("image_url"))

            print("\nExtracted description:")
            print("-" * 80)
            print(product_info.get("description"))
            print("-" * 80)

            description = product_info.get("description") or ""
            print(f"Character count: {len(description)}")

        except Exception as error:
            print("\nCould not scrape product description.")
            print(f"Error: {error}")

        print("\n" + "=" * 80)


if __name__ == "__main__":
    main()