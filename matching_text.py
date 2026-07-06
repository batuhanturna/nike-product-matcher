def build_matching_text(name=None, category=None, description=None):
    """
    Builds the text that will be converted into an embedding.

    Why not only use description?
    Some product descriptions are short marketing sentences.
    Product name and category help the model understand what the product is.
    """

    parts = []

    if name:
        parts.append(f"Product name: {name}")

    if category:
        parts.append(f"Category: {category}")

    if description:
        parts.append(f"Description: {description}")

    return "\n".join(parts).strip()
