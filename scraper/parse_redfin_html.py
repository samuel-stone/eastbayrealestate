import re
import json
from bs4 import BeautifulSoup


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def clean_number(value):

    if value is None:
        return None

    if isinstance(value, (int, float)):
        return value

    value = str(value)

    nums = re.findall(r"\d+", value.replace(",", ""))

    if not nums:
        return None

    return int(nums[0])


def extract_json_blocks(html):

    """
    Extract embedded JSON from Redfin pages.
    """

    blocks = []

    patterns = [
        r'<script type="application/json">(.*?)</script>',
        r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});',
        r'__NEXT_DATA__"\s*:\s*(\{.*\})'
    ]

    for p in patterns:

        matches = re.findall(
            p,
            html,
            re.DOTALL
        )

        for m in matches:

            try:
                blocks.append(
                    json.loads(m)
                )
            except Exception:
                pass


    return blocks



# --------------------------------------------------
# Address
# --------------------------------------------------

def extract_address(html):

    patterns = [

        r'"streetAddress":"([^"]+)"',

        r'"fullAddress":"([^"]+)"',

        r'"address":"([^"]+)"',

    ]


    for p in patterns:

        m = re.search(
            p,
            html,
            re.I
        )

        if m:
            return m.group(1)


    soup = BeautifulSoup(
        html,
        "html.parser"
    )


    if soup.title:

        title = soup.title.text

        if "Redfin" in title:
            return title.split("|")[0].strip()


    return None



# --------------------------------------------------
# Price
# --------------------------------------------------

def extract_price(html):

    json_blocks = extract_json_blocks(html)


    for block in json_blocks:

        text = json.dumps(block)


        match = re.search(
            r'"price"\s*:\s*"?\$?([\d,]+)',
            text
        )

        if match:

            return clean_number(
                match.group(1)
            )


    # fallback

    matches = re.findall(
        r'\$([\d,]{5,})',
        html
    )


    if matches:

        return clean_number(
            matches[0]
        )


    return None



# --------------------------------------------------
# Beds
# --------------------------------------------------

def extract_beds(html):

    patterns = [

        r'"beds"\s*:\s*(\d+)',

        r'(\d+)\s*(?:beds|bd)'

    ]


    for p in patterns:

        m = re.search(
            p,
            html,
            re.I
        )

        if m:
            return int(m.group(1))


    return None



# --------------------------------------------------
# Baths
# --------------------------------------------------

def extract_baths(html):

    patterns = [

        r'"baths"\s*:\s*([\d\.]+)',

        r'([\d\.]+)\s*(?:baths|ba)'

    ]


    for p in patterns:

        m = re.search(
            p,
            html,
            re.I
        )

        if m:

            return float(
                m.group(1)
            )


    return None



# --------------------------------------------------
# Sqft
# --------------------------------------------------

def extract_sqft(html):

    patterns = [

        r'"sqFt"\s*:\s*"?([\d,]+)',

        r'([\d,]+)\s*(?:sq\.?\s*ft|square feet)'

    ]


    for p in patterns:

        m = re.search(
            p,
            html,
            re.I
        )


        if m:

            return clean_number(
                m.group(1)
            )


    return None



# --------------------------------------------------
# Main parser
# --------------------------------------------------

def parse_listing(
        html,
        url=None,
        address=None
):

    return {

        "address":
            address or extract_address(html),

        "url":
            url,

        "price":
            extract_price(html),

        "beds":
            extract_beds(html),

        "baths":
            extract_baths(html),

        "sqft":
            extract_sqft(html),

        "dom":
            None,

        "price_drops":
            0,

        "is_fixer":
            False

    }



def parse_listing_data(raw):

    return {

        "address":
            raw.get("address"),

        "url":
            raw.get("url"),

        "price":
            clean_number(
                raw.get("price")
            ),

        "beds":
            clean_number(
                raw.get("beds")
            ),

        "baths":
            raw.get("baths"),

        "sqft":
            clean_number(
                raw.get("sqft")
            ),

        "dom":
            clean_number(
                raw.get("dom")
            ),

        "price_drops":
            clean_number(
                raw.get("price_drops")
            ),

        "is_fixer":
            raw.get(
                "is_fixer",
                False
            )

    }