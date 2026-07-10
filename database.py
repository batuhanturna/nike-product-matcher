import sqlite3
import json


DB_NAME = "products.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT,
        url TEXT UNIQUE,
        embedding TEXT
    )
    """)

    cursor.execute("PRAGMA table_info(products)")
    columns = [column[1] for column in cursor.fetchall()]

    if "image_url" not in columns:
        cursor.execute("ALTER TABLE products ADD COLUMN image_url TEXT")

    conn.commit()
    conn.close()


def add_product(name, description, category=None, url=None, embedding=None, image_url=None):
    conn = get_connection()
    cursor = conn.cursor()

    embedding_json = json.dumps(embedding) if embedding is not None else None

    cursor.execute("""
    INSERT OR IGNORE INTO products
    (name, description, category, url, embedding, image_url)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (name, description, category, url, embedding_json, image_url))

    conn.commit()
    conn.close()


def update_product(
    product_id,
    name=None,
    description=None,
    category=None,
    url=None,
    embedding=None,
    image_url=None
):
    conn = get_connection()
    cursor = conn.cursor()

    fields = []
    values = []

    if name is not None:
        fields.append("name = ?")
        values.append(name)

    if description is not None:
        fields.append("description = ?")
        values.append(description)

    if category is not None:
        fields.append("category = ?")
        values.append(category)

    if url is not None:
        fields.append("url = ?")
        values.append(url)

    if embedding is not None:
        fields.append("embedding = ?")
        values.append(json.dumps(embedding))

    if image_url is not None:
        fields.append("image_url = ?")
        values.append(image_url)

    if not fields:
        conn.close()
        return

    values.append(product_id)

    query = f"UPDATE products SET {', '.join(fields)} WHERE id = ?"
    cursor.execute(query, values)

    conn.commit()
    conn.close()


def get_all_products():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, name, description, category, url, embedding, image_url
    FROM products
    """)

    rows = cursor.fetchall()
    conn.close()

    products = []

    for row in rows:
        product_id, name, description, category, url, embedding_json, image_url = row

        embedding = json.loads(embedding_json) if embedding_json else None

        products.append({
            "id": product_id,
            "name": name,
            "description": description,
            "category": category,
            "url": url,
            "embedding": embedding,
            "image_url": image_url
        })

    return products


def product_exists(url):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM products WHERE url = ?", (url,))
    row = cursor.fetchone()

    conn.close()

    return row is not None


def clear_products():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM products")

    conn.commit()
    conn.close()