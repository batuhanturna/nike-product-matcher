import os
import textwrap

import matplotlib.pyplot as plt
import networkx as nx

from database import create_table
from matcher import ProductMatcher
from matching_text import build_matching_text
from scraper import scrape_product_info


THRESHOLD = 0.70

# Direct matches from the query product.
FIRST_LEVEL_TOP_K = 3

# Matches of the direct matches.
SECOND_LEVEL_TOP_K = 5

OUTPUT_FILE = "similarity_graph.png"


def short_label(text, max_length=36):
    if not text:
        return "Unknown product"

    text = " ".join(text.split())

    if len(text) <= max_length:
        return text

    return text[:max_length] + "..."


def wrapped_label(text, width=20):
    return "\n".join(textwrap.wrap(short_label(text, 55), width=width))


def add_product_node(graph, node_id, product_name, node_type):
    if node_id not in graph:
        graph.add_node(
            node_id,
            label=wrapped_label(product_name),
            node_type=node_type
        )


def add_similarity_edge(graph, source_id, target_id, score):
    if source_id == target_id:
        return

    if graph.has_edge(source_id, target_id):
        old_score = graph[source_id][target_id]["score"]

        if score > old_score:
            graph[source_id][target_id]["score"] = score
    else:
        graph.add_edge(source_id, target_id, score=score)


def draw_graph(graph, output_file):
    if graph.number_of_nodes() == 0:
        print("Graph is empty.")
        return

    plt.figure(figsize=(16, 10))

    pos = nx.spring_layout(
        graph,
        seed=42,
        k=1.5,
        iterations=100
    )

    node_colors = []
    node_sizes = []

    for node_id in graph.nodes:
        node_type = graph.nodes[node_id].get("node_type")

        if node_type == "query":
            node_colors.append("#ffcc00")  # yellow
            node_sizes.append(2800)
        elif node_type == "first_level":
            node_colors.append("#66b3ff")  # blue
            node_sizes.append(2300)
        else:
            node_colors.append("#88dd88")  # green
            node_sizes.append(1900)

    edge_widths = []

    for source, target in graph.edges:
        score = graph[source][target]["score"]
        width = 1.5 + ((score - THRESHOLD) / (1 - THRESHOLD)) * 4
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
        node_id: graph.nodes[node_id]["label"]
        for node_id in graph.nodes
    }

    nx.draw_networkx_labels(
        graph,
        pos,
        labels=labels,
        font_size=8,
        font_weight="bold"
    )

    edge_labels = {
        (source, target): f"{graph[source][target]['score'] * 100:.0f}%"
        for source, target in graph.edges
    }

    nx.draw_networkx_edge_labels(
        graph,
        pos,
        edge_labels=edge_labels,
        font_size=8
    )

    plt.title(
        "Nike Product Similarity Graph\n"
        "Yellow = query product, Blue = direct matches, Green = matches of matches",
        fontsize=14
    )

    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_file, dpi=200)
    plt.close()

    print(f"\nGraph saved as: {output_file}")

    try:
        os.startfile(output_file)
    except Exception:
        pass


def main():
    create_table()

    print("Nike Similarity Graph Generator")
    print(f"Only products with similarity >= {THRESHOLD * 100:.0f}% will be shown.")
    print("Type 'q' to exit.")

    url = input("\nEnter Nike product URL: ").strip()

    if url.lower() == "q":
        return

    if not url.startswith("http"):
        print("Please enter a valid URL.")
        return

    matcher = ProductMatcher()

    print("\nScraping query product...")
    query_info = scrape_product_info(url)

    query_text = build_matching_text(
        name=query_info["name"],
        category=None,
        description=query_info["description"]
    )

    print("\nQuery product:")
    print(query_info["name"])

    print("\nFinding direct similar products...")

    first_level_results = matcher.find_similar_products(
        query_text=query_text,
        top_k=FIRST_LEVEL_TOP_K,
        exclude_url=url,
        min_score=THRESHOLD
    )

    if not first_level_results:
        print("\nNo products found above threshold.")
        return

    graph = nx.Graph()

    query_node_id = "query_product"

    add_product_node(
        graph=graph,
        node_id=query_node_id,
        product_name=query_info["name"],
        node_type="query"
    )

    first_level_ids = set()

    for product in first_level_results:
        product_node_id = f"product_{product['id']}"
        first_level_ids.add(product["id"])

        add_product_node(
            graph=graph,
            node_id=product_node_id,
            product_name=product["name"],
            node_type="first_level"
        )

        add_similarity_edge(
            graph=graph,
            source_id=query_node_id,
            target_id=product_node_id,
            score=product["score"]
        )

        print(f"Direct match: {product['name']} - {product['score'] * 100:.2f}%")

    print("\nFinding matches of matches...")

    second_level_count = 0

    for product in first_level_results:
        source_node_id = f"product_{product['id']}"

        product_text = build_matching_text(
            name=product["name"],
            category=product["category"],
            description=product["description"]
        )

        second_level_results = matcher.find_similar_products(
            query_text=product_text,
            top_k=SECOND_LEVEL_TOP_K,
            exclude_url=product["url"],
            min_score=THRESHOLD
        )

        for neighbor in second_level_results:
            # Do not connect back to the original query product.
            if neighbor["url"] == url:
                continue

            # Important:
            # If this product is already a direct blue match, do not make it green.
            # We only want new second-level products to become green.
            if neighbor["id"] in first_level_ids:
                continue

            neighbor_node_id = f"product_{neighbor['id']}"

            add_product_node(
                graph=graph,
                node_id=neighbor_node_id,
                product_name=neighbor["name"],
                node_type="second_level"
            )

            add_similarity_edge(
                graph=graph,
                source_id=source_node_id,
                target_id=neighbor_node_id,
                score=neighbor["score"]
            )

            second_level_count += 1

            print(
                f"Second-level match: {product['name']} -> "
                f"{neighbor['name']} - {neighbor['score'] * 100:.2f}%"
            )

    print("\nGraph summary:")
    print(f"Nodes: {graph.number_of_nodes()}")
    print(f"Edges: {graph.number_of_edges()}")
    print(f"Second-level green products: {second_level_count}")

    if second_level_count == 0:
        print("\nNo green nodes found.")
        print("This usually means all second-level matches were already direct blue matches.")
        print("To get green nodes, add more diverse products to the database or lower the threshold.")

    draw_graph(graph, OUTPUT_FILE)


if __name__ == "__main__":
    main()