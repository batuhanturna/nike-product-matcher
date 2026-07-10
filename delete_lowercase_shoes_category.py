from database import create_table, get_connection


def main():
    create_table()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, name, category, url
    FROM products
    WHERE TRIM(category) = 'shoes'
    ORDER BY id ASC
    """)

    products = cursor.fetchall()

    if not products:
        print("No products found with category exactly equal to: shoes")
        conn.close()
        return

    print("\nProducts with category exactly 'shoes':")
    print("=" * 80)

    for product in products:
        product_id, name, category, url = product

        print(f"ID: {product_id}")
        print(f"Name: {name}")
        print(f"Category: {category}")
        print(f"URL: {url}")
        print("-" * 80)

    confirm = input("\nType DELETE to delete only these products: ").strip()

    if confirm != "DELETE":
        print("Cancelled. No products were deleted.")
        conn.close()
        return

    cursor.execute("""
    DELETE FROM products
    WHERE TRIM(category) = 'shoes'
    """)

    deleted_count = cursor.rowcount

    conn.commit()
    conn.close()

    print(f"\nDeleted {deleted_count} product(s) with category exactly 'shoes'.")


if __name__ == "__main__":
    main()