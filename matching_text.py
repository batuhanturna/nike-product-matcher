import re


NOISY_PATTERNS = [
    r"\bStyle:\s*[A-Z0-9\-]+",
    r"\bStyle Code:\s*[A-Z0-9\-]+",
    r"\bNot intended for use as Personal Protective Equipment \(PPE\)",
    r"\bImported\b",
    r"\bReflective details\b",
    r"\bProduct Details\b",
    r"\bBenefits\b",
    r"\bSize\s+\d+(\.\d+)?\b",
]


LOW_VALUE_LINES = [
    "style:",
    "style code:",
    "not intended for use",
    "personal protective equipment",
    "imported",
    "reflective details",
]


IMPORTANT_KEYWORDS = [
    "cushion",
    "cushioned",
    "foam",
    "zoomx",
    "reactx",
    "react",
    "air",
    "mesh",
    "upper",
    "outsole",
    "traction",
    "grip",
    "waffle",
    "durable",
    "breathable",
    "comfortable",
    "comfort",
    "running",
    "trail",
    "basketball",
    "football",
    "lifestyle",
    "training",
    "support",
    "responsive",
    "lightweight",
    "padding",
    "midsole",
    "heel-to-toe",
    "transition",
    "stability",
    "soft",
    "ride",
]


COLOR_PATTERNS = [
    r"\bShown:\s*([A-Za-z0-9 /\-]+)",
    r"\bColor Shown:\s*([A-Za-z0-9 /\-]+)",
    r"\bColour Shown:\s*([A-Za-z0-9 /\-]+)",
]


def normalize_text(text):
    if not text:
        return ""

    return " ".join(text.split()).strip()


def extract_color_text(description):
    """
    Extracts Nike color information such as:
    Shown: Wolf Grey/Pure Platinum/Summit White/Anthracite

    Color is useful for Nike similarity, so we keep it separately.
    """

    if not description:
        return ""

    colors = []

    for pattern in COLOR_PATTERNS:
        matches = re.findall(pattern, description, flags=re.IGNORECASE)

        for match in matches:
            color = normalize_text(match)

            if color and color not in colors:
                colors.append(color)

    return " | ".join(colors)


def remove_noisy_patterns(text):
    if not text:
        return ""

    cleaned = text

    for pattern in NOISY_PATTERNS:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def split_into_segments(text):
    if not text:
        return []

    section_headings = [
        "Engineered Mesh Upper",
        "Dual-Density Midsole",
        "Pods Around Outsole",
        "Plush Padding",
        "What's New?",
        "Product Details",
        "Benefits",
    ]

    normalized = normalize_text(text)

    for heading in section_headings:
        normalized = normalized.replace(heading, f". {heading}. ")

    raw_segments = re.split(r"(?<=[.!?])\s+", normalized)

    segments = []

    for segment in raw_segments:
        segment = normalize_text(segment)

        if not segment:
            continue

        if len(segment) < 12:
            continue

        segments.append(segment)

    return segments


def is_low_value_segment(segment):
    segment_lower = segment.lower()

    for low_value in LOW_VALUE_LINES:
        if low_value in segment_lower:
            return True

    if re.search(r"\b[A-Z]{2}\d{4}-\d{3}\b", segment):
        return True

    return False


def segment_importance_score(segment):
    segment_lower = segment.lower()

    score = 0

    for keyword in IMPORTANT_KEYWORDS:
        if keyword in segment_lower:
            score += 1

    if len(segment) > 80:
        score += 1

    if len(segment) > 160:
        score += 1

    return score


def clean_description_for_matching(description, max_segments=8):
    """
    Keeps important product features for similarity matching.

    Removed:
    - style code
    - size
    - PPE warning
    - low-value technical/legal lines

    Kept separately:
    - color information
    """

    if not description:
        return ""

    description = remove_noisy_patterns(description)
    segments = split_into_segments(description)

    useful_segments = []

    for segment in segments:
        if is_low_value_segment(segment):
            continue

        score = segment_importance_score(segment)

        if score > 0:
            useful_segments.append((score, segment))

    if not useful_segments:
        return normalize_text(description)

    useful_segments = sorted(
        useful_segments,
        key=lambda item: item[0],
        reverse=True
    )

    selected_segments = [segment for score, segment in useful_segments[:max_segments]]

    return normalize_text(" ".join(selected_segments))


def build_matching_text(name=None, category=None, description=None):
    """
    Builds the text that will be converted into an embedding.

    We use:
    - product name
    - category
    - important product features
    - color information

    We remove:
    - style code
    - size
    - low-value legal/product-code details
    """

    clean_description = clean_description_for_matching(description)
    color_text = extract_color_text(description)

    parts = []

    if name:
        parts.append(f"Product name: {name}")
        parts.append(f"Product identity: {name}")

    if category:
        parts.append(f"Category: {category}")

    if clean_description:
        parts.append(f"Important product features: {clean_description}")

    if color_text:
        # Color is useful, but not repeated too much.
        # This keeps color important without dominating product function.
        parts.append(f"Color: {color_text}")

    return "\n".join(parts).strip()