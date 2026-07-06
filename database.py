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
        url TEXT,
        embedding TEXT
    )
    """)

    conn.commit()
    conn.close()


def add_product(name, description, category=None, url=None, embedding=None):
    conn = get_connection()
    cursor = conn.cursor()

    embedding_json = json.dumps(embedding) if embedding is not None else None

    cursor.execute("""
    INSERT INTO products (name, description, category, url, embedding)
    VALUES (?, ?, ?, ?, ?)
    """, (name, description, category, url, embedding_json))

    conn.commit()
    conn.close()


def update_product(product_id, name=None, description=None, category=None, url=None, embedding=None):
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
    SELECT id, name, description, category, url, embedding
    FROM products
    """)

    rows = cursor.fetchall()
    conn.close()

    products = []

    for row in rows:
        product_id, name, description, category, url, embedding_json = row

        embedding = json.loads(embedding_json) if embedding_json else None

        products.append({
            "id": product_id,
            "name": name,
            "description": description,
            "category": category,
            "url": url,
            "embedding": embedding
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
