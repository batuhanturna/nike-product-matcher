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