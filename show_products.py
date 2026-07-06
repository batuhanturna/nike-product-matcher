from database import get_all_products


def main():
    products = get_all_products()

    print(f"Total products in database: {len(products)}")

    for product in products:
        print("-" * 60)
        print(f"ID: {product['id']}")
        print(f"Name: {product['name']}")
        print(f"Category: {product['category']}")
        print(f"URL: {product['url']}")


if __name__ == "__main__":
    main()