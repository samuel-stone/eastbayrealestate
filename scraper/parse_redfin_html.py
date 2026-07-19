import re


def clean_number(value):

    if not value:
        return None

    value = value.replace(",", "")

    nums = re.findall(
        r'\d+\.?\d*',
        value
    )

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
        "sqft": None

    }


    # ADDRESS

    address = re.search(
        r'(\d+\s+[A-Za-z0-9\s]+,\s*[A-Za-z]+,\s*[A-Z]{2}\s+\d{5})',
        html
    )

    if address:

        result["address"] = (
            address.group(1)
            .split(",")[0]
        )


    # PRICE

    price = re.search(
        r'\$([\d,]+)',
        html
    )

    if price:

        result["price"] = clean_number(
            price.group(1)
        )


    # BEDS

    beds = re.search(
        r'(\d+)\s*bd',
        html
    )

    if beds:

        result["beds"] = float(
            beds.group(1)
        )


    # BATHS

    baths = re.search(
        r'(\d+\.?\d*)\s*ba',
        html
    )

    if baths:

        result["baths"] = float(
            baths.group(1)
        )


    # SQFT

    sqft = re.search(
        r'([\d,]+)\s*sq\s*ft',
        html,
        re.I
    )

    if sqft:

        result["sqft"] = clean_number(
            sqft.group(1)
        )


    return result