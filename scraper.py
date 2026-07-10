import json
import re

import requests
from bs4 import BeautifulSoup


def clean_text(text):
    if not text:
        return None

    return " ".join(text.split()).strip() or None


def clean_product_name(name):
    name = clean_text(name)

    if not name:
        return None

    suffixes = [
        " | Nike",
        " | Nike TR",
        " | Nike Türkiye",
        ". Nike TR",
        ". Nike Türkiye",
        ". Nike.com",
        " | Nike.com",
    ]

    for suffix in suffixes:
        name = name.replace(suffix, "")

    name = re.sub(r"\s+", " ", name).strip()
    return name or None


def fetch_html_requests(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    response = requests.get(url, headers=headers, timeout=30)

    if response.status_code != 200:
        raise Exception(f"Could not fetch page. Status code: {response.status_code}")

    return response.text


def click_product_details_if_possible(page):
    """
    Nike sometimes puts the full detailed description inside a modal opened by
    a Product Details / View Product Details button.

    This function tries to open that modal. It scrolls the page and looks for
    buttons/role-buttons whose text contains details-related words.
    """

    # If details are already in the DOM, no need to click anything.
    try:
        if page.locator("[data-testid='view-product-details']").count() > 0:
            return
    except Exception:
        pass

    detail_words = [
        "view product details",
        "product details",
        "details",
        "ürün detay",
        "ürün ayrınt",
        "detayları gör",
    ]

    js_click_details = """
    (detailWords) => {
        const words = detailWords.map(word => word.toLowerCase());

        const elements = Array.from(
            document.querySelectorAll("button, [role='button'], a")
        );

        for (const element of elements) {
            const text = (element.innerText || element.textContent || "").toLowerCase();

            if (!text) {
                continue;
            }

            const matched = words.some(word => text.includes(word));

            if (matched) {
                element.scrollIntoView({block: "center"});
                element.click();
                return true;
            }
        }

        return false;
    }
    """

    # Try immediately first.
    try:
        clicked = page.evaluate(js_click_details, detail_words)

        if clicked:
            page.wait_for_timeout(2000)
            return
    except Exception:
        pass

    # Scroll and retry. Some Nike detail buttons are lower on the product page.
    for _ in range(8):
        try:
            page.mouse.wheel(0, 1200)
            page.wait_for_timeout(800)

            clicked = page.evaluate(js_click_details, detail_words)

            if clicked:
                page.wait_for_timeout(2500)
                return
        except Exception:
            pass


def fetch_html_playwright(url):
    """
    Fallback for JavaScript-rendered product pages and detail modals.
    Requires:
    pip install playwright
    python -m playwright install chromium
    """

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            viewport={"width": 1366, "height": 900},
        )

        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4000)

        click_product_details_if_possible(page)

        html = page.content()
        browser.close()

    return html


def is_product_type(item):
    item_type = item.get("@type")

    if item_type == "Product":
        return True

    if isinstance(item_type, list) and "Product" in item_type:
        return True

    return False


def find_product_objects(data):
    found = []

    if not isinstance(data, dict):
        return found

    if is_product_type(data):
        found.append(data)

    for value in data.values():
        if isinstance(value, dict):
            found.extend(find_product_objects(value))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    found.extend(find_product_objects(item))

    return found


def parse_json_ld_products(soup):
    products = []
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
            if isinstance(item, dict):
                products.extend(find_product_objects(item))

    return products


def extract_product_name(soup, json_ld_products):
    """
    Extracts real product name.

    Nike can also have [data-testid='product-title'] inside
    [data-testid='view-product-details']. That is often a detail heading,
    not the real product name. So this function skips modal/detail titles.
    """

    for product in json_ld_products:
        name = product.get("name")

        if name:
            return clean_product_name(name)

    selectors = [
        "h1",
        "#pdp_product_title",
        "[id*='product-title']",
        "[class*='product-title']",
        "[class*='ProductTitle']",
    ]

    for selector in selectors:
        element = soup.select_one(selector)

        if element:
            if element.find_parent(attrs={"data-testid": "view-product-details"}):
                continue

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


def extract_from_view_product_details(soup):
    """
    Extracts Nike's full Product Details modal/section.

    Target structure:
    <div data-testid="view-product-details">
        <p data-testid="product-title">Double-stacked foam...</p>
        <p data-testid="product-description">Maximum cushioning...</p>
        <div data-testid="benefit-section">Engineered Mesh Upper...</div>
        <div data-testid="benefit-section">Dual-Density Midsole...</div>
        ...
    </div>
    """

    containers = soup.select("[data-testid='view-product-details']")

    for container in containers:
        parts = []
        seen = set()

        wanted_selectors = [
            "[data-testid='product-reason-to-buy']",
            "[data-testid='product-title']",
            "[data-testid='product-description']",
            "[data-testid='benefit-section']",
            "[data-testid='product-details']",
            "h2",
            "h3",
            "h4",
            "p",
            "li",
        ]

        for selector in wanted_selectors:
            elements = container.select(selector)

            for element in elements:
                text = clean_text(element.get_text(" ", strip=True))

                if not text:
                    continue

                if len(text) < 8:
                    continue

                if text in seen:
                    continue

                seen.add(text)
                parts.append(text)

        result = clean_text(" ".join(parts))

        if result and len(result) > 80:
            return result

    return None


def extract_from_product_description_container(soup):
    selectors = [
        "#product-description-container [data-testid='product-description']",
        "div[data-testid='product-description-container'] [data-testid='product-description']",
        "[data-testid='product-description-container'] [data-testid='product-description']",
        "#product-description-container p",
        "div[data-testid='product-description-container'] p",
    ]

    for selector in selectors:
        elements = soup.select(selector)

        for element in elements:
            if element.find_parent(attrs={"data-testid": "view-product-details"}):
                continue

            text = clean_text(element.get_text(" ", strip=True))

            if text and len(text) > 20:
                return text

    return None


def extract_from_product_description_anywhere(soup):
    selectors = [
        "[data-testid='view-product-details'] [data-testid='product-description']",
        "[data-testid='product-description']",
    ]

    for selector in selectors:
        elements = soup.select(selector)

        for element in elements:
            text = clean_text(element.get_text(" ", strip=True))

            if text and len(text) > 20:
                return text

    return None


def extract_from_json_ld(json_ld_products):
    for product in json_ld_products:
        description = product.get("description")

        if description:
            return clean_text(description)

    return None


def extract_from_meta_tags(soup):
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


def parse_product_info(html, url):
    soup = BeautifulSoup(html, "lxml")
    json_ld_products = parse_json_ld_products(soup)

    name = extract_product_name(soup, json_ld_products)
    image_url = extract_product_image(soup, json_ld_products, html)

    description = extract_from_view_product_details(soup)
    source = "HTML element: [data-testid='view-product-details']"

    if not description:
        description = extract_from_product_description_container(soup)
        source = "HTML element: product-description-container"

    if not description:
        description = extract_from_product_description_anywhere(soup)
        source = "HTML element: [data-testid='product-description']"

    if not description:
        description = extract_from_json_ld(json_ld_products)
        source = "JSON-LD Product description"

    if not description:
        description = extract_from_meta_tags(soup)
        source = "Meta description / og:description / twitter:description"

    if not description:
        description = extract_from_common_html(soup)
        source = "HTML element with description-related class/id"

    if not name:
        name = "Unknown Nike Product"

    if not description:
        raise Exception("Product description could not be found on this page.")

    return {
        "name": name,
        "description": description,
        "description_source": source,
        "image_url": image_url,
        "url": url
    }


def should_try_playwright(info):
    """
    If requests only found JSON-LD/meta/short text, try Playwright.
    JSON-LD often misses lower Product Details / benefits sections.
    """

    if not info:
        return True

    source = info.get("description_source", "")
    description = info.get("description") or ""

    if source == "HTML element: [data-testid='view-product-details']":
        return False

    if source in [
        "JSON-LD Product description",
        "Meta description / og:description / twitter:description",
    ]:
        return True

    if len(description) < 600:
        return True

    return False


def scrape_product_info(url, use_playwright_fallback=True):
    request_info = None
    request_error = None

    try:
        html = fetch_html_requests(url)
        request_info = parse_product_info(html, url)
    except Exception as error:
        request_error = error

    if use_playwright_fallback and should_try_playwright(request_info):
        try:
            html = fetch_html_playwright(url)
            playwright_info = parse_product_info(html, url)

            # Prefer the full view-product-details text.
            if playwright_info["description_source"] == "HTML element: [data-testid='view-product-details']":
                return playwright_info

            # Otherwise prefer whichever description is longer.
            if request_info:
                request_len = len(request_info.get("description") or "")
                playwright_len = len(playwright_info.get("description") or "")

                if playwright_len > request_len:
                    return playwright_info

                return request_info

            return playwright_info

        except Exception as playwright_error:
            if request_info:
                return request_info

            if request_error:
                raise Exception(
                    f"Requests failed: {request_error}; "
                    f"Playwright failed: {playwright_error}"
                )

            raise playwright_error

    if request_info:
        return request_info

    if request_error:
        raise request_error

    raise Exception("Product info could not be scraped.")

def extract_product_image(soup, json_ld_products, html=None):
    """
    Extracts Nike product image URL.

    Priority:
    1. JSON-LD Product image
    2. og:image
    3. twitter:image
    4. static.nike.com links from HTML
    """

    for product in json_ld_products:
        image = product.get("image")

        if isinstance(image, str) and image.startswith("http"):
            return image

        if isinstance(image, list) and len(image) > 0:
            first_image = image[0]

            if isinstance(first_image, str) and first_image.startswith("http"):
                return first_image

            if isinstance(first_image, dict) and first_image.get("url"):
                return first_image.get("url")

        if isinstance(image, dict) and image.get("url"):
            return image.get("url")

    meta_selectors = [
        {"property": "og:image"},
        {"property": "og:image:secure_url"},
        {"name": "twitter:image"},
    ]

    for attrs in meta_selectors:
        tag = soup.find("meta", attrs=attrs)

        if tag and tag.get("content"):
            return tag.get("content")

    image_selectors = [
        "[class*='product-imagery'] img",
        "[data-testid='mobile-image-carousel-list'] img",
        "[data-testid*='image-carousel'] img",
        "picture img",
        "img[src*='static.nike.com']",
    ]

    for selector in image_selectors:
        image_tag = soup.select_one(selector)

        if not image_tag:
            continue

        if image_tag.get("src"):
            return image_tag.get("src")

        if image_tag.get("srcset"):
            return image_tag.get("srcset").split(",")[0].strip().split(" ")[0]

    if html:
        matches = re.findall(r"https://static\.nike\.com[^\"'\s)]+", html)

        cleaned_matches = []

        for match in matches:
            match = match.replace("\\u002F", "/")
            match = match.replace("\\/", "/")

            if match not in cleaned_matches:
                cleaned_matches.append(match)

        for match in cleaned_matches:
            if "/a/images/" in match:
                return match

        if cleaned_matches:
            return cleaned_matches[0]

    return None



def scrape_product_description(url):
    info = scrape_product_info(url)
    return info["description"]


def scrape_product_description_with_source(url):
    info = scrape_product_info(url)

    return {
        "name": info["name"],
        "description": info["description"],
        "source": info["description_source"]
    }
