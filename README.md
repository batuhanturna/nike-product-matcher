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

## Latest Update: Web Interface and Admin Panel

The project was upgraded from a terminal-based prototype into a more user-friendly web demo using Streamlit.

### New Features

- Added a professional Streamlit web interface.
  - Users can search similar Nike products directly from the browser.
  - Product results are displayed as visual product cards.
  - Product images, categories, similarity scores and product links are shown together.

- Added product image support.
  - The Nike scraper now extracts product image URLs from product pages.
  - The image URL is stored in the local SQLite database.
  - Product images are displayed in the catalog, similarity results and graph nodes.

- Added interactive similarity search.
  - Users can enter a Nike product URL.
  - The system scrapes the product data.
  - A semantic embedding is created for the query product.
  - Similar products are listed with similarity scores and images.

- Added graph JSON export.
  - Product similarity graphs can now be exported as structured JSON.
  - The JSON contains nodes, edges, product labels, categories, URLs, image URLs and similarity scores.
  - This makes the graph data reusable for frontend visualizations.

- Added interactive graph visualization.
  - Graphs are displayed inside the web interface using PyVis.
  - Product images can be shown as graph nodes.
  - Users can inspect product relationships visually.

- Added an Admin Panel.
  - Category reports can be viewed from the browser.
  - Multiple products can be added by pasting Nike product URLs.
  - Products can be deleted individually.
  - Categories can be deleted with exact category matching.
  - Database backups can be created from the interface.
  - Embeddings can be rebuilt locally without scraping Nike again.

### Admin Panel Features

The Admin Panel includes:

- Category Report
- Bulk Add URLs
- Delete Selected Products
- Delete Exact Category
- Create Database Backup
- Rebuild Local Embeddings

This makes the project easier to manage without using separate terminal scripts for every operation.

### Product Image Extraction

The scraper now extracts images mainly from:

```text
og:image
twitter:image
JSON-LD Product image
static.nike.com image links