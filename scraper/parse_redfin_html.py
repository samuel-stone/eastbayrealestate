import re

def clean_number(value):
    if not value:
        return None
    value = value.replace(",", "")
    nums = re.findall(r'\d+\.?\d*', value)
    if nums:
        return float(nums[0])
    return None

def parse_listing(html, url):
    result = {
        "url": url,
        "address": None,
        "price": None,
        "beds": None,
        "baths": None,
        "sqft": None,
        "dom": 0,
        "price_drops": 0,
        "is_fixer": False
    }

    # ADDRESS
    address = re.search(r'(\d+\s+[A-Za-z0-9\s]+,\s*[A-Za-z]+,\s*[A-Z]{2}\s+\d{5})', html)
    if address:
        result["address"] = address.group(1).split(",")[0]

    # PRICE
    price = re.search(r'\$([\d,]+)', html)
    if price:
        result["price"] = clean_number(price.group(1))

    # BEDS & BATHS
    beds = re.search(r'(\d+)\s*bd', html)
    if beds: result["beds"] = float(beds.group(1))

    baths = re.search(r'(\d+\.?\d*)\s*ba', html)
    if baths: result["baths"] = float(baths.group(1))

    # SQFT
    sqft = re.search(r'([\d,]+)\s*sq\s*ft', html, re.I)
    if sqft: result["sqft"] = clean_number(sqft.group(1))

    # MARKETPLACE SIGNALS (DOM & Price Drops)
    dom_match = re.search(r'(\d+)\s+days?\s+on\s+market', html, re.I)
    if dom_match: result["dom"] = int(dom_match.group(1))

    price_drop_match = re.search(r'(Price drop|Price reduced).*?\$([\d,]+)', html, re.I)
    if price_drop_match: result["price_drops"] = 1

    # KEYWORD FLAGS (Fixer, TLC, Investor)
    if re.search(r'(fixer|needs tlc|as-is|investor special|handyman)', html, re.I):
        result["is_fixer"] = True

    return result