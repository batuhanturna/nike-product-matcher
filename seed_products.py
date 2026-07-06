print("seed_products.py started")

from sentence_transformers import SentenceTransformer

from database import create_table, add_product, clear_products


MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def main():
    print("Loading model...")
    model = SentenceTransformer(MODEL_NAME)

    create_table()
    clear_products()

    products = [
        {
            "name": "Black Oversize T-Shirt",
            "description": "A black oversize cotton t-shirt suitable for daily casual use.",
            "category": "T-Shirt",
            "url": "https://example.com/black-oversize-tshirt"
        },
        {
            "name": "Black Jogger Pants",
            "description": "Comfortable black jogger pants with an elastic waist and relaxed fit.",
            "category": "Pants",
            "url": "https://example.com/black-jogger-pants"
        },
        {
            "name": "White Sneakers",
            "description": "Simple white sneakers suitable for everyday casual outfits.",
            "category": "Shoes",
            "url": "https://example.com/white-sneakers"
        },
        {
            "name": "Blue Denim Jacket",
            "description": "An oversize blue denim jacket made for casual daily combinations.",
            "category": "Jacket",
            "url": "https://example.com/blue-denim-jacket"
        },
        {
            "name": "Red Evening Dress",
            "description": "An elegant red evening dress designed for special occasions and formal events.",
            "category": "Dress",
            "url": "https://example.com/red-evening-dress"
        },
        {
            "name": "Beige Trench Coat",
            "description": "A classic beige trench coat suitable for seasonal transitions.",
            "category": "Outerwear",
            "url": "https://example.com/beige-trench-coat"
        },
        {
            "name": "Gray Hoodie",
            "description": "A soft gray hoodie with a comfortable fit and casual streetwear style.",
            "category": "Hoodie",
            "url": "https://example.com/gray-hoodie"
        }
    ]

    for product in products:
        embedding = model.encode(product["description"]).tolist()

        add_product(
            name=product["name"],
            description=product["description"],
            category=product["category"],
            url=product["url"],
            embedding=embedding
        )

        print(f"Added: {product['name']}")

    print("All products were added to the database.")


if __name__ == "__main__":
    main()