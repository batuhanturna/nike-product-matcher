# Changelog

## Latest Update

### Added

- Added similarity threshold filtering.
  - Products below 0.70 cosine similarity are no longer shown as matches.

- Added product-based graph visualization.
  - The graph starts from a single Nike product URL.
  - Direct matches are shown.
  - Matches of those matches are also shown.

- Added catalog-based graph visualization.
  - All products in the database can be compared with each other.
  - Products above the similarity threshold are connected in a graph.
  - This helps identify product clusters.

- Added multi-category bulk import.
  - Products can now be collected from multiple Nike categories.
  - Category labels can include subcategories such as:
    - Shoes > Running
    - Shoes > Basketball
    - Clothing > T-Shirts

### Improved

- Improved Nike scraper.
  - The scraper now reads Nike's detailed product modal.
  - It extracts richer product information from product details and benefit sections.

- Improved matching text generation.
  - The system now removes low-value text before creating embeddings.
  - Style codes, size-only details and legal warnings are filtered.
  - Important product features are kept.
  - Color information is preserved for better Nike product similarity.

### Notes

- The database file `products.db` is not included in the repository.
- Generated graph images are not required to be committed.
- The virtual environment folder `venv` is not included in the repository.

## Web Interface and Admin Panel Update

### Added

- Added a professional Streamlit web interface.
  - Similar products can now be searched from a browser.
  - Results are displayed as product cards with images, categories, scores and links.

- Added product image support.
  - The scraper extracts image URLs from Nike product pages.
  - Image URLs are stored in the SQLite database.
  - Product images are displayed in the UI.

- Added Admin Panel.
  - Category report
  - Bulk product adding from URL list
  - Exact category deletion
  - Selected product deletion
  - Database backup creation
  - Local embedding rebuild

- Added graph JSON export.
  - Product similarity graphs can now be exported as JSON.
  - Nodes include product name, category, URL and image URL.
  - Edges include similarity score and label.

- Added interactive graph visualization.
  - PyVis is used to display product graphs in the browser.
  - Product images can be used as graph nodes.

### Improved

- Improved database schema.
  - Added `image_url` column.
  - Existing databases can be upgraded automatically without deleting products.

- Improved scraper.
  - The scraper now extracts product image URLs from `og:image`, `twitter:image`, JSON-LD and Nike static image links.

- Improved matching workflow.
  - Product size information is removed from matching text.
  - Embeddings can be rebuilt locally without scraping all products again.

- Improved catalog management.
  - Products and categories can now be managed from the web interface instead of only using terminal scripts.

### Notes

- The database file `products.db` is still ignored by Git.
- Generated backups are not required to be committed.
- Generated graph JSON files are outputs and should not be committed unless needed for documentation.