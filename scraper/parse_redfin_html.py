import re

def clean_number(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    
    numbers = re.findall(r"\d+", str(value).replace(",", ""))
    if not numbers:
        return None
        
    return int(numbers[0])

def extract_address(html):
    """Pull address from Redfin HTML metadata."""
    patterns = [
        r'"streetAddress":"([^"]+)"',
        r'"address":"([^"]+)"',
        r'<title>([^<]+)</title>'
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            value = match.group(1)
            if value:
                return value.strip()
    return None

def extract_price(html):
    match = re.search(r'\$[\d,]+', html)
    if match:
        return clean_number(match.group(0))
    return None

def extract_beds(html):
    match = re.search(r'(\d+)\s*(?:beds|bd)', html, re.IGNORECASE)
    if match:
        return clean_number(match.group(1))
    return None

def extract_baths(html):
    match = re.search(r'(\d+(?:\.\d+)?)\s*(?:baths|ba)', html, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None

def extract_sqft(html):
    match = re.search(r'([\d,]+)\s*(?:sq\.?\s*ft|square feet)', html, re.IGNORECASE)
    if match:
        return clean_number(match.group(1))
    return None

def parse_listing(html, url=None, address=None):
    """Parse Redfin listing HTML."""
    listing = {
        "address": address or extract_address(html),
        "url": url,
        "price": extract_price(html),
        "beds": extract_beds(html),
        "baths": extract_baths(html),
        "sqft": extract_sqft(html),
        "dom": None,
        "price_drops": 0,
        "is_fixer": False
    }
    return listing

def parse_listing_data(raw):
    return {
        "address": raw.get("address"),
        "url": raw.get("url"),
        "price": clean_number(raw.get("price")),
        "beds": clean_number(raw.get("beds")),
        "baths": raw.get("baths"),
        "sqft": clean_number(raw.get("sqft")),
        "dom": clean_number(raw.get("dom")),
        "price_drops": clean_number(raw.get("price_drops")),
        "is_fixer": raw.get("is_fixer", False)
    }