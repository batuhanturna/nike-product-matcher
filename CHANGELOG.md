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