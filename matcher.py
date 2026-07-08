import torch
from sentence_transformers import SentenceTransformer, util

from database import get_all_products


MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Minimum similarity threshold.
# 0.70 means 70%.
MIN_SIMILARITY_SCORE = 0.70


class ProductMatcher:
    def __init__(self):
        print("Loading model...")
        self.model = SentenceTransformer(MODEL_NAME)

    def find_similar_products(self, query_text, top_k=5, exclude_url=None, min_score=MIN_SIMILARITY_SCORE):
        products = get_all_products()

        if not products:
            print("Database is empty.")
            return []

        query_embedding = self.model.encode(query_text, convert_to_tensor=True)

        results = []

        for product in products:
            if exclude_url and product["url"] == exclude_url:
                continue

            product_embedding = product["embedding"]

            if product_embedding is None:
                continue

            product_embedding = torch.tensor(
                product_embedding,
                dtype=query_embedding.dtype,
                device=query_embedding.device
            )

            score = util.cos_sim(query_embedding, product_embedding)[0][0].item()

            # Only keep products with similarity score >= 70%
            if score < min_score:
                continue

            results.append({
                "id": product["id"],
                "name": product["name"],
                "description": product["description"],
                "category": product["category"],
                "url": product["url"],
                "score": score
            })

        results = sorted(results, key=lambda item: item["score"], reverse=True)

        return results[:top_k]