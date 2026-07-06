import json
import re
import requests
from bs4 import BeautifulSoup


def clean_text(text):
    if not text:
        return None

    return " ".join(text.split())


def clean_product_name(name):
    name = clean_text(name)

    if not name:
        return None

    # Remove common website suffixes from page titles.
    replacements = [
        " | Nike",
        " | Nike TR",
        " | Nike Türkiye",
        ". Nike TR",
        ". Nike Türkiye",
        ". Nike.com",
    ]

    for replacement in replacements:
        name = name.replace(replacement, "")

    name = re.sub(r"\s+", " ", name).strip()

    return name or None


def is_product_type(item):
    item_type = item.get("@type")

    if item_type == "Product":
        return True

    if isinstance(item_type, list) and "Product" in item_type:
        return True

    return False


def extract_product_name(soup):
    """
    Tries to extract the product name/title from the product page.
    """

    selectors = [
        "[data-testid='product-title']",
        "#pdp_product_title",
        "[id*='product-title']",
        "[class*='product-title']",
        "h1",
    ]

    for selector in selectors:
        element = soup.select_one(selector)

        if element:
            name = clean_product_name(element.get_text(" ", strip=True))

            if name and len(name) > 2:
                return name

    meta_selectors = [
        {"property": "og:title"},
        {"name": "twitter:title"},
    ]

    for attrs in meta_selectors:
        tag = soup.find("meta", attrs=attrs)

        if tag and tag.get("content"):
            name = clean_product_name(tag.get("content"))

            if name and len(name) > 2:
                return name

    if soup.title and soup.title.string:
        name = clean_product_name(soup.title.string)

        if name and len(name) > 2:
            return name

    return None


def extract_from_product_description_testid(soup):
    """
    This function tries to extract the exact product description area
    shown in the browser Inspect panel.

    Example target element:
    <p data-testid="product-description">...</p>
    """

    selectors = [
        "#product-description-container [data-testid='product-description']",
        "[data-testid='product-description']",
        "div[data-testid='product-description-container'] p",
        "#product-description-container p",
    ]

    for selector in selectors:
        elements = soup.select(selector)

        for element in elements:
            text = clean_text(element.get_text(" ", strip=True))

            if text and len(text) > 20:
                return text

    return None


def extract_from_json_ld(soup):
    """
    Tries to extract product description from structured JSON-LD data.
    Some e-commerce websites store Product information inside:
    <script type="application/ld+json">
    """

    scripts = soup.find_all("script", type="application/ld+json")

    for script in scripts:
        try:
            if not script.string:
                continue

            data = json.loads(script.string)
        except Exception:
            continue

        items = data if isinstance(data, list) else [data]

        for item in items:
            if not isinstance(item, dict):
                continue

            if is_product_type(item):
                description = item.get("description")
                if description:
                    return clean_text(description)

            if "@graph" in item:
                for graph_item in item["@graph"]:
                    if isinstance(graph_item, dict) and is_product_type(graph_item):
                        description = graph_item.get("description")
                        if description:
                            return clean_text(description)

    return None


def extract_from_meta_tags(soup):
    """
    Tries to extract product description from meta tags.
    These are often used for SEO and social previews.
    """

    meta_selectors = [
        {"name": "description"},
        {"property": "og:description"},
        {"name": "twitter:description"},
    ]

    for attrs in meta_selectors:
        tag = soup.find("meta", attrs=attrs)

        if tag and tag.get("content"):
            text = clean_text(tag.get("content"))

            if text and len(text) > 20:
                return text

    return None


def extract_from_common_html(soup):
    """
    Generic fallback.
    Tries common class/id names that usually contain product descriptions.
    """

    selectors = [
        "[class*='description']",
        "[id*='description']",
        "[class*='Description']",
        "[id*='Description']",
        "[class*='product-detail']",
        "[class*='product-description']",
        "[data-testid*='description']",
        "[data-test*='description']",
    ]

    for selector in selectors:
        elements = soup.select(selector)

        for element in elements:
            text = clean_text(element.get_text(" ", strip=True))

            if text and len(text) > 50:
                return text

    return None


def fetch_soup(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers, timeout=15)

    if response.status_code != 200:
        raise Exception(f"Could not fetch page. Status code: {response.status_code}")

    return BeautifulSoup(response.text, "lxml")


def scrape_product_description(url):
    """
    Returns only the extracted product description text.
    """

    info = scrape_product_info(url)
    return info["description"]


def scrape_product_info(url):
    """
    Returns product information from a URL.

    The important part is description_source.
    If possible, description is taken from:
    <p data-testid="product-description">
    """

    soup = fetch_soup(url)

    name = extract_product_name(soup)

    description = extract_from_product_description_testid(soup)
    if description:
        return {
            "name": name,
            "description": description,
            "description_source": "HTML element: [data-testid='product-description']"
        }

    description = extract_from_json_ld(soup)
    if description:
        return {
            "name": name,
            "description": description,
            "description_source": "JSON-LD Product description"
        }

    description = extract_from_meta_tags(soup)
    if description:
        return {
            "name": name,
            "description": description,
            "description_source": "Meta description / og:description / twitter:description"
        }

    description = extract_from_common_html(soup)
    if description:
        return {
            "name": name,
            "description": description,
            "description_source": "HTML element with description-related class/id"
        }

    raise Exception("Product description could not be found on this page.")


def scrape_product_description_with_source(url):
    """
    Debug version.
    Keeps compatibility with debug_scraper.py.
    """

    info = scrape_product_info(url)

    return {
        "description": info["description"],
        "source": info["description_source"],
        "name": info["name"]
    }
