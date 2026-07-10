import json
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

from database import DB_NAME, create_table, get_all_products, add_product, product_exists, get_connection, update_product
from matcher import ProductMatcher
from matching_text import build_matching_text
from scraper import scrape_product_info


st.set_page_config(
    page_title="Nike Product Matcher",
    page_icon="👟",
    layout="wide",
    initial_sidebar_state="expanded"
)


CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at top left, rgba(17, 17, 17, 0.08), transparent 28%),
        linear-gradient(180deg, #fafafa 0%, #f4f4f4 100%);
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1400px;
}

section[data-testid="stSidebar"] {
    background: #0f0f0f;
}

section[data-testid="stSidebar"] * {
    color: #f7f7f7;
}

section[data-testid="stSidebar"] div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    padding: 14px;
    border-radius: 16px;
}

.hero {
    background: linear-gradient(135deg, #111111 0%, #2a2a2a 55%, #555555 100%);
    color: #ffffff;
    border-radius: 28px;
    padding: 34px 38px;
    margin-bottom: 26px;
    box-shadow: 0 18px 42px rgba(0,0,0,0.18);
    position: relative;
    overflow: hidden;
}

.hero:after {
    content: "";
    position: absolute;
    width: 280px;
    height: 280px;
    right: -90px;
    top: -90px;
    background: rgba(255,255,255,0.08);
    border-radius: 50%;
}

.hero-kicker {
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    color: #d9d9d9;
    margin-bottom: 8px;
}

.hero-title {
    font-size: 48px;
    line-height: 1.03;
    font-weight: 900;
    letter-spacing: -1.4px;
    margin-bottom: 10px;
}

.hero-subtitle {
    max-width: 760px;
    color: #eeeeee;
    font-size: 17px;
    line-height: 1.55;
}

.hero-pill-row {
    margin-top: 22px;
}

.hero-pill {
    display: inline-block;
    padding: 8px 13px;
    border-radius: 999px;
    background: rgba(255,255,255,0.11);
    border: 1px solid rgba(255,255,255,0.18);
    color: #ffffff;
    font-size: 13px;
    font-weight: 700;
    margin-right: 8px;
    margin-bottom: 8px;
}

.section-card {
    background: #ffffff;
    border: 1px solid #e9e9e9;
    border-radius: 24px;
    padding: 22px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.055);
    margin-bottom: 20px;
}

.product-card {
    border: 1px solid #e8e8e8;
    border-radius: 24px;
    padding: 18px;
    margin-bottom: 18px;
    background: #ffffff;
    box-shadow: 0 10px 26px rgba(0,0,0,0.055);
    transition: transform 0.12s ease, box-shadow 0.12s ease, border-color 0.12s ease;
}

.product-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 16px 34px rgba(0,0,0,0.095);
    border-color: #d7d7d7;
}

.product-name {
    font-size: 20px;
    font-weight: 850;
    margin-bottom: 7px;
    line-height: 1.25;
    color: #111111;
}

.product-meta {
    color: #525252;
    font-size: 14px;
    margin-bottom: 6px;
}

.score-badge {
    display: inline-block;
    padding: 8px 13px;
    border-radius: 999px;
    background: linear-gradient(135deg, #111111, #3a3a3a);
    color: white;
    font-weight: 850;
    font-size: 14px;
    margin-top: 8px;
    margin-bottom: 8px;
}

.role-badge {
    display: inline-block;
    padding: 6px 11px;
    border-radius: 999px;
    background: #f0f0f0;
    color: #111111;
    font-weight: 800;
    font-size: 12px;
    margin-bottom: 8px;
    letter-spacing: 0.2px;
}

.query-badge {
    background: #ffe082;
    color: #111111;
}

.similar-badge {
    background: #e8f0ff;
    color: #1d4ed8;
}

.warning-card {
    background: #fff7ed;
    border: 1px solid #fed7aa;
    border-radius: 18px;
    padding: 16px;
    color: #7c2d12;
}

.danger-zone {
    background: #fff5f5;
    border: 1px solid #fecaca;
    border-radius: 22px;
    padding: 20px;
    margin-top: 20px;
}

.success-zone {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 22px;
    padding: 20px;
    margin-top: 20px;
}

.small-muted {
    color: #777;
    font-size: 13px;
}

div[data-testid="stTabs"] button {
    font-weight: 800;
    font-size: 15px;
}

.stButton > button {
    border-radius: 999px;
    font-weight: 850;
    min-height: 44px;
    border: 1px solid #111111;
}

.stDownloadButton > button {
    border-radius: 999px;
    font-weight: 800;
}

input, textarea {
    border-radius: 14px !important;
}

a {
    color: #111111;
    font-weight: 700;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

.footer-note {
    color: #777;
    font-size: 13px;
    margin-top: 20px;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_resource
def load_matcher():
    return ProductMatcher()


def valid_image_url(product):
    image_url = product.get("image_url")

    if image_url and isinstance(image_url, str) and image_url.startswith("http"):
        return image_url

    return None


def truncate_text(text, limit=220):
    if not text:
        return ""

    if len(text) <= limit:
        return text

    return text[:limit].strip() + "..."


def render_hero():
    st.markdown(
        """
        <div class="hero">
            <div class="hero-kicker">Semantic product recommendation demo</div>
            <div class="hero-title">Nike Product Matcher</div>
            <div class="hero-subtitle">
                Search Nike products by URL, compare semantic similarity with embeddings,
                display product images, manage the local catalog and export reusable graph JSON.
            </div>
            <div class="hero-pill-row">
                <span class="hero-pill">Sentence Transformers</span>
                <span class="hero-pill">Cosine Similarity</span>
                <span class="hero-pill">Image URL Extraction</span>
                <span class="hero-pill">Admin Panel</span>
                <span class="hero-pill">Interactive Graph</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def show_product_card(product, score=None, role=None, show_description=False):
    image_url = valid_image_url(product)

    with st.container():
        st.markdown('<div class="product-card">', unsafe_allow_html=True)

        col_image, col_info = st.columns([1, 4], vertical_alignment="center")

        with col_image:
            if image_url:
                st.image(image_url, use_container_width=True)
            else:
                st.info("No image")

        with col_info:
            name = product.get("name") or "Unknown product"
            category = product.get("category") or "No category"
            url = product.get("url") or ""

            if role:
                css_class = "query-badge" if "Query" in role else "similar-badge" if "Similar" in role else ""
                st.markdown(
                    f'<div class="role-badge {css_class}">{role}</div>',
                    unsafe_allow_html=True
                )

            st.markdown(
                f'<div class="product-name">{name}</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<div class="product-meta"><b>Category:</b> {category}</div>',
                unsafe_allow_html=True
            )

            if score is not None:
                st.markdown(
                    f'<span class="score-badge">{score * 100:.2f}% Similar</span>',
                    unsafe_allow_html=True
                )

            if show_description:
                description = truncate_text(product.get("description"), limit=320)
                if description:
                    st.write(description)

            if url:
                st.markdown(f"[Open product page]({url})")

        st.markdown("</div>", unsafe_allow_html=True)


def products_to_dataframe(products):
    rows = []

    for product in products:
        rows.append({
            "id": product.get("id"),
            "name": product.get("name"),
            "category": product.get("category"),
            "url": product.get("url"),
            "image_url": product.get("image_url"),
        })

    return pd.DataFrame(rows)


def get_category_report(products):
    counts = {}

    for product in products:
        category = product.get("category") or "No category"
        counts[category] = counts.get(category, 0) + 1

    rows = [
        {"category": category, "product_count": count}
        for category, count in sorted(counts.items(), key=lambda item: item[0].lower())
    ]

    return pd.DataFrame(rows)


def create_database_backup():
    db_path = Path(DB_NAME)

    if not db_path.exists():
        raise FileNotFoundError(f"{DB_NAME} could not be found.")

    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"products_backup_{timestamp}.db"

    shutil.copy2(db_path, backup_path)

    return backup_path


def delete_products_by_ids(product_ids):
    if not product_ids:
        return 0

    conn = get_connection()
    cursor = conn.cursor()

    placeholders = ",".join(["?"] * len(product_ids))

    cursor.execute(
        f"DELETE FROM products WHERE id IN ({placeholders})",
        product_ids
    )

    deleted_count = cursor.rowcount

    conn.commit()
    conn.close()

    return deleted_count


def delete_category_exact(category):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM products WHERE TRIM(category) = ?",
        (category.strip(),)
    )

    deleted_count = cursor.rowcount

    conn.commit()
    conn.close()

    return deleted_count


def rebuild_embeddings_locally():
    products = get_all_products()

    if not products:
        return 0

    matcher = load_matcher()

    updated_count = 0

    for product in products:
        matching_text = build_matching_text(
            name=product.get("name"),
            category=product.get("category"),
            description=product.get("description")
        )

        embedding = matcher.model.encode(matching_text).tolist()

        update_product(
            product_id=product.get("id"),
            name=product.get("name"),
            description=product.get("description"),
            category=product.get("category"),
            url=product.get("url"),
            embedding=embedding,
            image_url=product.get("image_url")
        )

        updated_count += 1

    return updated_count


def bulk_add_urls(urls, category, delay_seconds=1.0):
    matcher = load_matcher()

    logs = []
    added_count = 0
    skipped_count = 0
    failed_count = 0

    unique_urls = []
    seen = set()

    for url in urls:
        clean_url = url.strip()

        if not clean_url:
            continue

        clean_url = clean_url.split("?")[0]

        if clean_url in seen:
            continue

        seen.add(clean_url)
        unique_urls.append(clean_url)

    if not unique_urls:
        return {
            "logs": ["No valid URLs were provided."],
            "added": 0,
            "skipped": 0,
            "failed": 0
        }

    progress = st.progress(0)

    for index, url in enumerate(unique_urls, start=1):
        progress.progress(index / len(unique_urls))

        if product_exists(url):
            logs.append(f"[SKIP] Already exists: {url}")
            skipped_count += 1
            continue

        try:
            logs.append(f"[SCRAPE] {url}")
            info = scrape_product_info(url)

            matching_text = build_matching_text(
                name=info.get("name"),
                category=category,
                description=info.get("description")
            )

            embedding = matcher.model.encode(matching_text).tolist()

            add_product(
                name=info.get("name"),
                description=info.get("description"),
                category=category,
                url=url,
                embedding=embedding,
                image_url=info.get("image_url")
            )

            logs.append(f"[ADD] {info.get('name')}")
            added_count += 1

            if delay_seconds > 0:
                time.sleep(delay_seconds)

        except Exception as error:
            logs.append(f"[FAIL] {url} | Error: {error}")
            failed_count += 1

    return {
        "logs": logs,
        "added": added_count,
        "skipped": skipped_count,
        "failed": failed_count
    }


def build_product_graph_json(query_product, results):
    nodes = []
    edges = []

    query_node_id = "query"

    nodes.append({
        "id": query_node_id,
        "label": query_product.get("name"),
        "category": query_product.get("category"),
        "url": query_product.get("url"),
        "image_url": query_product.get("image_url"),
        "role": "query"
    })

    for product in results:
        product_id = str(product.get("id"))

        nodes.append({
            "id": product_id,
            "label": product.get("name"),
            "category": product.get("category"),
            "url": product.get("url"),
            "image_url": product.get("image_url"),
            "role": "similar_product",
            "score": product.get("score")
        })

        edges.append({
            "source": query_node_id,
            "target": product_id,
            "score": product.get("score"),
            "label": f"{product.get('score') * 100:.2f}%"
        })

    return {
        "nodes": nodes,
        "edges": edges
    }


def build_catalog_graph_json(products, threshold=0.70, max_edges_per_product=3):
    import torch
    from sentence_transformers import util

    nodes = []
    edges = []

    products_with_embeddings = [
        product for product in products
        if product.get("embedding") is not None
    ]

    for product in products_with_embeddings:
        nodes.append({
            "id": str(product.get("id")),
            "label": product.get("name"),
            "category": product.get("category"),
            "url": product.get("url"),
            "image_url": product.get("image_url"),
            "role": "catalog_product"
        })

    edge_candidates_by_product = {}

    for i in range(len(products_with_embeddings)):
        product_a = products_with_embeddings[i]
        embedding_a = torch.tensor(product_a["embedding"])

        for j in range(i + 1, len(products_with_embeddings)):
            product_b = products_with_embeddings[j]
            embedding_b = torch.tensor(product_b["embedding"])

            score = util.cos_sim(embedding_a, embedding_b)[0][0].item()

            if score < threshold:
                continue

            id_a = str(product_a.get("id"))
            id_b = str(product_b.get("id"))

            edge = {
                "source": id_a,
                "target": id_b,
                "score": score,
                "label": f"{score * 100:.2f}%"
            }

            edge_candidates_by_product.setdefault(id_a, []).append(edge)
            edge_candidates_by_product.setdefault(id_b, []).append(edge)

    selected_edge_keys = set()
    selected_edges = []

    for product_id, candidate_edges in edge_candidates_by_product.items():
        sorted_edges = sorted(
            candidate_edges,
            key=lambda item: item["score"],
            reverse=True
        )

        for edge in sorted_edges[:max_edges_per_product]:
            edge_key = tuple(sorted([edge["source"], edge["target"]]))

            if edge_key in selected_edge_keys:
                continue

            selected_edge_keys.add(edge_key)
            selected_edges.append(edge)

    return {
        "nodes": nodes,
        "edges": selected_edges
    }


def graph_json_to_pyvis_html(graph_json, height="680px"):
    network = Network(
        height=height,
        width="100%",
        bgcolor="#ffffff",
        font_color="#111111",
        directed=False
    )

    network.barnes_hut(
        gravity=-36000,
        central_gravity=0.25,
        spring_length=190,
        spring_strength=0.025,
        damping=0.85
    )

    for node in graph_json.get("nodes", []):
        node_id = node.get("id")
        label = node.get("label") or "Unknown"
        category = node.get("category") or "No category"
        role = node.get("role") or "product"
        image_url = node.get("image_url")
        url = node.get("url") or ""
        score = node.get("score")

        title_parts = [
            f"<b>{label}</b>",
            f"Category: {category}",
            f"Role: {role}"
        ]

        if score is not None:
            title_parts.append(f"Similarity: {score * 100:.2f}%")

        if url:
            title_parts.append(f"<a href='{url}' target='_blank'>Open product</a>")

        title = "<br>".join(title_parts)

        if image_url:
            network.add_node(
                node_id,
                label=truncate_text(label, 34),
                title=title,
                shape="image",
                image=image_url,
                size=36
            )
        else:
            network.add_node(
                node_id,
                label=truncate_text(label, 34),
                title=title,
                color="#90caf9",
                size=24
            )

    for edge in graph_json.get("edges", []):
        score = edge.get("score") or 0
        width = 1.2 + (score * 4.5)

        network.add_edge(
            edge.get("source"),
            edge.get("target"),
            value=score,
            title=edge.get("label"),
            label=edge.get("label"),
            width=width,
            color="#7a7a7a"
        )

    network.set_options("""
    const options = {
      "nodes": {
        "font": {
          "size": 14,
          "face": "Inter, Arial"
        },
        "borderWidth": 2
      },
      "edges": {
        "font": {
          "size": 12,
          "align": "top",
          "face": "Inter, Arial"
        },
        "smooth": {
          "type": "continuous"
        }
      },
      "interaction": {
        "hover": true,
        "navigationButtons": true,
        "keyboard": true
      },
      "physics": {
        "enabled": true,
        "stabilization": {
          "iterations": 140
        }
      }
    }
    """)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as temp_file:
        temp_path = temp_file.name

    network.save_graph(temp_path)
    html = Path(temp_path).read_text(encoding="utf-8")
    return html


def main():
    create_table()

    products = get_all_products()
    product_count = len(products)
    image_count = len([product for product in products if valid_image_url(product)])
    category_count = len(set([product.get("category") for product in products if product.get("category")]))

    st.sidebar.markdown("## 👟 Nike Matcher")
    st.sidebar.caption("Semantic similarity demo")

    st.sidebar.metric("Products", product_count)
    st.sidebar.metric("With images", image_count)
    st.sidebar.metric("Categories", category_count)

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        **Demo flow**

        1. Enter a Nike product URL  
        2. Scrape product data  
        3. Create embedding  
        4. Compare with database  
        5. Manage catalog in Admin Panel  
        """
    )

    render_hero()

    tab_search, tab_catalog, tab_add, tab_graph, tab_admin = st.tabs([
        "🔎 Similarity Search",
        "📦 Catalog",
        "➕ Add Product",
        "🕸️ Graph",
        "⚙️ Admin Panel"
    ])

    with tab_search:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Find Similar Products")
        st.caption("Enter a Nike product URL and search for semantically similar products in your local catalog.")

        col_url, col_settings = st.columns([3, 1])

        with col_url:
            product_url = st.text_input(
                "Nike product URL",
                placeholder="https://www.nike.com/...",
                key="search_url"
            )

        with col_settings:
            threshold = st.slider(
                "Threshold",
                min_value=0.50,
                max_value=0.95,
                value=0.70,
                step=0.01
            )

            top_k = st.slider(
                "Top K",
                min_value=1,
                max_value=20,
                value=5,
                step=1
            )

        search_clicked = st.button("Find Similar Products", type="primary")
        st.markdown("</div>", unsafe_allow_html=True)

        if search_clicked:
            if not product_url:
                st.warning("Please enter a Nike product URL.")
            else:
                with st.spinner("Loading model, scraping product and searching similar products..."):
                    try:
                        matcher = load_matcher()
                        query_info = scrape_product_info(product_url)

                        query_text = build_matching_text(
                            name=query_info.get("name"),
                            category=None,
                            description=query_info.get("description")
                        )

                        results = matcher.find_similar_products(
                            query_text=query_text,
                            top_k=top_k,
                            exclude_url=product_url,
                            min_score=threshold
                        )

                        st.session_state["last_query_product"] = query_info
                        st.session_state["last_results"] = results
                        st.session_state["last_graph_json"] = build_product_graph_json(query_info, results)

                    except Exception as error:
                        st.error(f"Error: {error}")
                        results = None
                        query_info = None

                if query_info:
                    st.subheader("Query Product")
                    show_product_card(query_info, role="Query Product", show_description=True)

                if results is not None:
                    st.subheader("Similar Products")

                    if not results:
                        st.warning("No similar products found above the selected threshold.")
                    else:
                        for product in results:
                            show_product_card(
                                product,
                                score=product.get("score"),
                                role="Similar Product"
                            )

                        graph_json = st.session_state["last_graph_json"]

                        col_download_1, col_download_2 = st.columns(2)

                        with col_download_1:
                            st.download_button(
                                label="Download Graph JSON",
                                data=json.dumps(graph_json, indent=2, ensure_ascii=False),
                                file_name="product_similarity_graph.json",
                                mime="application/json"
                            )

                        with col_download_2:
                            st.download_button(
                                label="Download Results JSON",
                                data=json.dumps(results, indent=2, ensure_ascii=False),
                                file_name="similar_products.json",
                                mime="application/json"
                            )

                        st.subheader("Interactive Product Graph")
                        graph_html = graph_json_to_pyvis_html(graph_json)
                        components.html(graph_html, height=720, scrolling=True)

    with tab_catalog:
        st.subheader("Product Catalog")
        st.caption("Browse saved products with images, categories and product links.")

        products = get_all_products()

        if not products:
            st.warning("Database is empty.")
        else:
            df = products_to_dataframe(products)

            categories = sorted([
                category for category in df["category"].dropna().unique()
                if category
            ])

            col_search, col_category, col_view = st.columns([2, 1, 1])

            with col_search:
                search_text = st.text_input(
                    "Search product name",
                    placeholder="Air Max, Vomero, Pegasus..."
                )

            with col_category:
                selected_category = st.selectbox(
                    "Category",
                    options=["All"] + categories
                )

            with col_view:
                view_mode = st.radio(
                    "View",
                    options=["Cards", "Table"],
                    horizontal=True
                )

            filtered_products = products

            if search_text:
                filtered_products = [
                    product for product in filtered_products
                    if search_text.lower() in (product.get("name") or "").lower()
                ]

            if selected_category != "All":
                filtered_products = [
                    product for product in filtered_products
                    if product.get("category") == selected_category
                ]

            st.info(f"Showing {len(filtered_products)} products.")

            if view_mode == "Cards":
                for product in filtered_products:
                    show_product_card(product)
            else:
                st.dataframe(products_to_dataframe(filtered_products), use_container_width=True)

    with tab_add:
        st.subheader("Add Product from URL")
        st.caption("Scrape a new Nike product, generate embedding and save it to the database.")

        add_url = st.text_input(
            "Nike product URL",
            placeholder="https://www.nike.com/...",
            key="add_url"
        )

        add_category = st.text_input(
            "Category",
            placeholder="Shoes > Running"
        )

        if st.button("Scrape and Add Product"):
            if not add_url:
                st.warning("Please enter a product URL.")
            elif product_exists(add_url):
                st.info("This product already exists in the database.")
            else:
                with st.spinner("Loading model, scraping product and creating embedding..."):
                    try:
                        matcher = load_matcher()
                        info = scrape_product_info(add_url)

                        matching_text = build_matching_text(
                            name=info.get("name"),
                            category=add_category,
                            description=info.get("description")
                        )

                        embedding = matcher.model.encode(matching_text).tolist()

                        add_product(
                            name=info.get("name"),
                            description=info.get("description"),
                            category=add_category,
                            url=add_url,
                            embedding=embedding,
                            image_url=info.get("image_url")
                        )

                        st.success("Product added successfully.")

                        added_product = {
                            "name": info.get("name"),
                            "description": info.get("description"),
                            "category": add_category,
                            "url": add_url,
                            "image_url": info.get("image_url")
                        }

                        show_product_card(
                            added_product,
                            role="New Product",
                            show_description=True
                        )

                    except Exception as error:
                        st.error(f"Error: {error}")

    with tab_graph:
        st.subheader("Graph JSON and Interactive Visualization")
        st.caption("Export graph data as JSON or preview it as an interactive network.")

        graph_mode = st.radio(
            "Graph mode",
            options=["Last product search", "Catalog graph"],
            horizontal=True
        )

        if graph_mode == "Last product search":
            graph_json = st.session_state.get("last_graph_json")

            if not graph_json:
                st.info("First search for a product in the Similarity Search tab.")
            else:
                col_json, col_download = st.columns([3, 1])

                with col_json:
                    st.json(graph_json)

                with col_download:
                    st.download_button(
                        label="Download Product Graph JSON",
                        data=json.dumps(graph_json, indent=2, ensure_ascii=False),
                        file_name="latest_product_similarity_graph.json",
                        mime="application/json"
                    )

                st.subheader("Interactive Graph")
                graph_html = graph_json_to_pyvis_html(graph_json)
                components.html(graph_html, height=720, scrolling=True)

        else:
            products = get_all_products()

            col_threshold, col_edges = st.columns(2)

            with col_threshold:
                catalog_threshold = st.slider(
                    "Catalog graph threshold",
                    min_value=0.50,
                    max_value=0.95,
                    value=0.75,
                    step=0.01
                )

            with col_edges:
                max_edges = st.slider(
                    "Max edges per product",
                    min_value=1,
                    max_value=6,
                    value=2,
                    step=1
                )

            if st.button("Build Catalog Graph"):
                with st.spinner("Building catalog graph..."):
                    graph_json = build_catalog_graph_json(
                        products,
                        threshold=catalog_threshold,
                        max_edges_per_product=max_edges
                    )

                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Nodes", len(graph_json["nodes"]))
                col_b.metric("Edges", len(graph_json["edges"]))
                col_c.metric("Threshold", f"{catalog_threshold:.2f}")

                st.download_button(
                    label="Download Catalog Graph JSON",
                    data=json.dumps(graph_json, indent=2, ensure_ascii=False),
                    file_name="catalog_similarity_graph.json",
                    mime="application/json"
                )

                st.subheader("Interactive Catalog Graph")
                graph_html = graph_json_to_pyvis_html(graph_json)
                components.html(graph_html, height=720, scrolling=True)

    with tab_admin:
        st.subheader("Admin Panel")
        st.caption("Manage the local SQLite catalog directly from the interface.")

        products = get_all_products()
        category_df = get_category_report(products)

        admin_report, admin_bulk, admin_delete, admin_maintenance = st.tabs([
            "Category Report",
            "Bulk Add URLs",
            "Delete Data",
            "Maintenance"
        ])

        with admin_report:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.write("Category summary")
            st.dataframe(category_df, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with admin_bulk:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.write("Add multiple products from Nike URLs")

            bulk_category = st.text_input(
                "Category for all URLs",
                placeholder="Shoes > Running",
                key="bulk_category"
            )

            bulk_urls_text = st.text_area(
                "Nike product URLs, one URL per line",
                height=220,
                placeholder="https://www.nike.com/...\nhttps://www.nike.com/...",
                key="bulk_urls"
            )

            delay_seconds = st.slider(
                "Delay between products",
                min_value=0.0,
                max_value=5.0,
                value=1.0,
                step=0.5
            )

            if st.button("Add All Products", type="primary"):
                if not bulk_category:
                    st.warning("Please enter a category.")
                elif not bulk_urls_text.strip():
                    st.warning("Please enter at least one URL.")
                else:
                    urls = bulk_urls_text.splitlines()

                    with st.spinner("Bulk adding products..."):
                        result = bulk_add_urls(
                            urls=urls,
                            category=bulk_category,
                            delay_seconds=delay_seconds
                        )

                    col_added, col_skipped, col_failed = st.columns(3)
                    col_added.metric("Added", result["added"])
                    col_skipped.metric("Skipped", result["skipped"])
                    col_failed.metric("Failed", result["failed"])

                    st.text_area(
                        "Bulk add log",
                        value="\n".join(result["logs"]),
                        height=260
                    )

            st.markdown("</div>", unsafe_allow_html=True)

        with admin_delete:
            st.markdown('<div class="danger-zone">', unsafe_allow_html=True)
            st.write("Delete by exact category")
            st.caption("This uses exact match. Deleting 'shoes' will not delete 'Shoes > Running'.")

            category_options = category_df["category"].tolist() if not category_df.empty else []

            selected_delete_category = st.selectbox(
                "Category to delete",
                options=category_options,
                key="delete_category_select"
            )

            confirm_category = st.text_input(
                "Type DELETE_CATEGORY to confirm",
                key="confirm_category_delete"
            )

            if st.button("Delete Selected Category"):
                if not selected_delete_category:
                    st.warning("Please select a category.")
                elif confirm_category != "DELETE_CATEGORY":
                    st.warning("Confirmation text is incorrect.")
                else:
                    deleted_count = delete_category_exact(selected_delete_category)
                    st.success(f"Deleted {deleted_count} product(s) from category: {selected_delete_category}")
                    st.rerun()

            st.markdown("---")

            st.write("Delete selected products")

            product_options = {
                f"{product.get('id')} | {product.get('name')} | {product.get('category')}": product.get("id")
                for product in products
            }

            selected_product_labels = st.multiselect(
                "Products to delete",
                options=list(product_options.keys())
            )

            confirm_products = st.text_input(
                "Type DELETE_PRODUCTS to confirm",
                key="confirm_product_delete"
            )

            if st.button("Delete Selected Products"):
                if not selected_product_labels:
                    st.warning("Please select at least one product.")
                elif confirm_products != "DELETE_PRODUCTS":
                    st.warning("Confirmation text is incorrect.")
                else:
                    selected_ids = [product_options[label] for label in selected_product_labels]
                    deleted_count = delete_products_by_ids(selected_ids)
                    st.success(f"Deleted {deleted_count} selected product(s).")
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        with admin_maintenance:
            st.markdown('<div class="success-zone">', unsafe_allow_html=True)
            st.write("Database backup")

            if st.button("Create Database Backup"):
                try:
                    backup_path = create_database_backup()
                    st.success(f"Backup created: {backup_path}")
                except Exception as error:
                    st.error(f"Backup failed: {error}")

            st.markdown("---")
            st.write("Rebuild embeddings locally")
            st.caption("This does not scrape Nike again. It only rebuilds embeddings from existing local database text.")

            confirm_rebuild = st.text_input(
                "Type REBUILD to confirm",
                key="confirm_rebuild_embeddings"
            )

            if st.button("Rebuild Local Embeddings"):
                if confirm_rebuild != "REBUILD":
                    st.warning("Confirmation text is incorrect.")
                else:
                    with st.spinner("Rebuilding embeddings locally..."):
                        updated_count = rebuild_embeddings_locally()

                    st.success(f"Rebuilt embeddings for {updated_count} product(s).")

            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="footer-note">Nike Product Matcher demo · Built with Streamlit, SQLite, Sentence Transformers and PyVis.</div>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
