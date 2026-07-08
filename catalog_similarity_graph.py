import os
import textwrap

import matplotlib.pyplot as plt
import networkx as nx
import torch
from sentence_transformers import util

from database import create_table, get_all_products


THRESHOLD = 0.70
MAX_EDGES_PER_PRODUCT = 2
OUTPUT_FILE = "catalog_similarity_graph.png"


def short_label(text, max_length=35):
    if not text:
        return "Unknown"

    text = " ".join(text.split())

    if len(text) <= max_length:
        return text

    return text[:max_length] + "..."


def wrapped_label(text, width=18):
    return "\n".join(textwrap.wrap(short_label(text, 50), width=width))


def calculate_similarity(embedding_a, embedding_b):
    tensor_a = torch.tensor(embedding_a, dtype=torch.float32)
    tensor_b = torch.tensor(embedding_b, dtype=torch.float32)

    score = util.cos_sim(tensor_a, tensor_b)[0][0].item()
    return score


def build_catalog_graph(products):
    graph = nx.Graph()

    products_with_embeddings = [
        product for product in products
        if product["embedding"] is not None
    ]

    candidate_edges = []

    for i in range(len(products_with_embeddings)):
        for j in range(i + 1, len(products_with_embeddings)):
            product_a = products_with_embeddings[i]
            product_b = products_with_embeddings[j]

            score = calculate_similarity(
                product_a["embedding"],
                product_b["embedding"]
            )

            if score >= THRESHOLD:
                candidate_edges.append({
                    "source": product_a,
                    "target": product_b,
                    "score": score
                })

    candidate_edges = sorted(
        candidate_edges,
        key=lambda item: item["score"],
        reverse=True
    )

    node_degrees = {}

    for edge in candidate_edges:
        source = edge["source"]
        target = edge["target"]
        score = edge["score"]

        source_id = f"product_{source['id']}"
        target_id = f"product_{target['id']}"

        source_degree = node_degrees.get(source_id, 0)
        target_degree = node_degrees.get(target_id, 0)

        if source_degree >= MAX_EDGES_PER_PRODUCT:
            continue

        if target_degree >= MAX_EDGES_PER_PRODUCT:
            continue

        if source_id not in graph:
            graph.add_node(
                source_id,
                label=wrapped_label(source["name"]),
                category=source["category"] or "Unknown"
            )

        if target_id not in graph:
            graph.add_node(
                target_id,
                label=wrapped_label(target["name"]),
                category=target["category"] or "Unknown"
            )

        graph.add_edge(
            source_id,
            target_id,
            score=score
        )

        node_degrees[source_id] = source_degree + 1
        node_degrees[target_id] = target_degree + 1

    return graph


def draw_graph(graph):
    if graph.number_of_nodes() == 0:
        print("No graph could be created.")
        print("There may be no products above the threshold.")
        return

    plt.figure(figsize=(18, 11))

    pos = nx.spring_layout(
        graph,
        seed=42,
        k=1.4,
        iterations=100
    )

    categories = sorted({
        graph.nodes[node].get("category", "Unknown")
        for node in graph.nodes
    })

    color_palette = [
        "#66b3ff",
        "#88dd88",
        "#ffcc66",
        "#ff9999",
        "#c299ff",
        "#99dddd",
        "#dddd99",
    ]

    category_colors = {}

    for index, category in enumerate(categories):
        category_colors[category] = color_palette[index % len(color_palette)]

    node_colors = [
        category_colors[graph.nodes[node].get("category", "Unknown")]
        for node in graph.nodes
    ]

    node_sizes = [
        1700 + graph.degree[node] * 250
        for node in graph.nodes
    ]

    edge_widths = []

    for source, target in graph.edges:
        score = graph[source][target]["score"]
        width = 1.2 + ((score - THRESHOLD) / (1 - THRESHOLD)) * 4
        edge_widths.append(width)

    nx.draw_networkx_nodes(
        graph,
        pos,
        node_color=node_colors,
        node_size=node_sizes,
        edgecolors="black",
        linewidths=1
    )

    nx.draw_networkx_edges(
        graph,
        pos,
        width=edge_widths,
        alpha=0.65
    )

    labels = {
        node: graph.nodes[node]["label"]
        for node in graph.nodes
    }

    nx.draw_networkx_labels(
        graph,
        pos,
        labels=labels,
        font_size=8,
        font_weight="bold"
    )

    if graph.number_of_edges() <= 35:
        edge_labels = {
            (source, target): f"{graph[source][target]['score'] * 100:.0f}%"
            for source, target in graph.edges
        }

        nx.draw_networkx_edge_labels(
            graph,
            pos,
            edge_labels=edge_labels,
            font_size=7
        )

    plt.title(
        "Nike Catalog Similarity Graph\n"
        "Nodes = products, edges = similarity above 70%",
        fontsize=15
    )

    plt.axis("off")
    plt.tight_layout()
    plt.savefig(OUTPUT_FILE, dpi=200)
    plt.close()

    print(f"\nCatalog graph saved as: {OUTPUT_FILE}")

    try:
        os.startfile(OUTPUT_FILE)
    except Exception:
        pass


def main():
    create_table()

    products = get_all_products()

    print("Nike Catalog Similarity Graph")
    print(f"Products in database: {len(products)}")
    print(f"Similarity threshold: {THRESHOLD * 100:.0f}%")
    print(f"Max edges per product: {MAX_EDGES_PER_PRODUCT}")

    if not products:
        print("Database is empty.")
        return

    graph = build_catalog_graph(products)

    print("\nGraph summary:")
    print(f"Nodes: {graph.number_of_nodes()}")
    print(f"Edges: {graph.number_of_edges()}")

    draw_graph(graph)


if __name__ == "__main__":
    main()