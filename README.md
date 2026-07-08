# Nike Product Matcher

This is a terminal-based product similarity prototype for Nike products.

The system can:

- collect product links from Nike category pages
- scrape product names and descriptions
- create text embeddings using Sentence Transformers
- store products in a local SQLite database
- compare a new product URL with stored products using cosine similarity
- show similar products in the terminal

## Setup

First create and activate a virtual environment:

py -m venv venv
.\venv\Scripts\Activate.ps1

Then install the required packages:

pip install -r requirements.txt
python -m playwright install chromium

## Add products from a Nike category page

python bulk_add_from_category.py

## Add one product from a URL

python add_product_from_url.py

## Run similarity search

python main.py

## Show products in database

python show_products.py

## Notes

The local database file products.db is not included in the repository.
It is created automatically when the program runs.

The venv folder is also not included in the repository.
Users should create their own virtual environment after cloning the project.

## Latest Updates

### Recent Improvements

The project was updated with several new features and improvements:

- Added a similarity threshold system.
  - The matcher now only returns products with a cosine similarity score of 0.70 or higher.
  - Lower-quality matches are filtered out.

- Added product-based similarity graph visualization.
  - A user can enter a Nike product URL.
  - The system finds direct similar products.
  - It also finds the similar products of those similar products.
  - The result is visualized as a graph using NetworkX and Matplotlib.

- Added catalog-based similarity graph visualization.
  - The system can compare all products in the local database.
  - Products with similarity above the threshold are connected in a graph.
  - This helps visualize product clusters inside the catalog.

- Improved Nike product scraping.
  - The scraper now supports Nike's detailed product modal.
  - It can extract text from:
    - product description
    - product details
    - benefit sections
    - technical/product feature sections
  - This gives the embedding model richer product information.

- Improved matching text preparation.
  - The system now cleans product descriptions before creating embeddings.
  - Low-value details such as style codes, size-only information and legal text are removed.
  - Important product features such as cushioning, foam, upper material, outsole, traction, comfort and support are kept.
  - Color information is preserved because it is useful for Nike product similarity.

- Added support for larger and more diverse product databases.
  - A multi-category bulk import script was added.
  - It can collect products from multiple Nike categories and subcategories.
  - Category names can be stored hierarchically, such as:
    - Shoes > Running
    - Shoes > Basketball
    - Clothing > Hoodies
    - Accessories > Bags

## Graph Visualization

The project now supports two graph modes:

### 1. Product-based graph

The user enters one Nike product URL.  
The system shows:

- the query product
- direct similar products
- similar products of the direct matches

This is useful for recommendation-style exploration.

### 2. Catalog-based graph

The system compares all products stored in the database.  
Each product becomes a node, and each similarity relationship above the threshold becomes an edge.

This is useful for understanding how the product catalog clusters internally.

## Similarity Logic

The system uses:

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2