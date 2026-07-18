#!/usr/bin/env python3
"""Simple public-page scraper starter for local lead research.

This script fetches a public web page, extracts a small amount of structured
content, and saves it to JSON or CSV. It is intentionally conservative and
only targets pages that are publicly accessible and allowed for scraping.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

DEFAULT_DEMO_URL = "https://example.com"
CONTRA_COSTA_PARCELS_URL = (
    "https://gis.cccounty.us/Downloads/Assessor/"
)
CONTRA_COSTA_CITY_CODES = {
    "CNCD": "CONCORD",
    "LAF": "LAFAYETTE",
    "MRGA": "MORAGA",
    "ORNDA": "ORINDA",
    "PLHL": "PLEASANT HILL",
    "WALCR": "WALNUT CREEK",
}
DEFAULT_OUTPUT_FIELDS = [
    "source_name",
    "source_type",
    "source_url",
    "address",
    "city",
    "parcel_number",
    "contact_name",
    "contact_role",
    "assessed_value",
    "activity_date",
    "notes",
    "lead_rating",
    "lead_reason",
    "relocation_signal",
    "prospect_type",
    "data_strength",
    "review_status",
    "scraped_at",
]

UNIT_SUFFIX_PATTERN = re.compile(r"\b(?:apt|unit|ste|suite|#)\b[^\n]*$", re.I)


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def normalize_property_address(address: str | None) -> str:
    if not address:
        return ""
    cleaned = normalize_text(address).upper()
    cleaned = re.sub(r"\s+(APT|UNIT|STE|SUITE|#)\b.*$", "", cleaned)
    return cleaned.strip()


def contains_any(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def is_actionable_link(url: str, link_text: str) -> bool:
    lowered_url = url.lower()
    lowered_text = link_text.lower()

    if any(skip in lowered_url for skip in ["twitter.com", "youtube.com", "facebook.com", "instagram.com", "nextdoor.com", "mailto:", "tel:", "javascript:"]):
        return False

    if any(keyword in lowered_text for keyword in ["permit", "business", "license", "planning", "building", "development", "inspection", "zoning", "application", "form"]):
        return True

    if any(keyword in lowered_url for keyword in ["/permits", "/business", "/planning", "/building", "/inspection", "/development", "/property", "/parcel", "/assessment"]):
        return True

    return False


def fetch_html(url: str) -> str:
    if url.startswith("file://"):
        return Path(url[7:]).read_text(encoding="utf-8")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.text


def extract_page_data(
    html: str,
    url: str,
    *,
    capture_public_contact_names: bool = False,
) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")

    title = normalize_text(soup.title.get_text(" ", strip=True)) if soup.title else ""
    heading = normalize_text(soup.find("h1").get_text(" ", strip=True)) if soup.find("h1") else ""

    paragraphs = [
        normalize_text(p.get_text(" ", strip=True))
        for p in soup.find_all("p")
        if normalize_text(p.get_text(" ", strip=True))
    ]
    summary = paragraphs[0] if paragraphs else ""

    links: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if href.startswith("http"):
            links.append(href)
        elif href.startswith("/"):
            links.append(urljoin(url, href))

    field_map: dict[str, str] = {}
    for row in soup.find_all(["tr", "div", "li"]):
        cells = [normalize_text(cell.get_text(" ", strip=True)) for cell in row.find_all(["th", "td", "label", "span"])]
        if len(cells) >= 2:
            label = cells[0].lower()
            value = cells[-1]
            if "address" in label:
                field_map["address"] = value
            elif "city" in label:
                field_map["city"] = value
            elif "parcel" in label:
                field_map["parcel_number"] = value
            elif "assessed" in label or "value" in label:
                field_map["assessed_value"] = value
            elif "activity" in label or "date" in label:
                field_map["activity_date"] = value
            elif capture_public_contact_names and any(
                keyword in label
                for keyword in ["property owner", "owner name", "applicant name", "project applicant", "contact name"]
            ):
                field_map["contact_name"] = value
                field_map["contact_role"] = "public_record_contact"

    full_text = " ".join([title, heading, summary, *paragraphs]).lower()
    if not field_map.get("address") and re.search(r"\b\d{1,4} [a-z0-9.\- ]+ (st|street|rd|road|ave|avenue|blvd|boulevard|way|dr|drive|lane|ln|ct|court|pl|place|ter|terrace)\b", title + " " + heading, re.I):
        field_map["address"] = normalize_text(title or heading)

    if not field_map.get("parcel_number"):
        parcel_match = re.search(r"\b(?:parcel(?:\s+number)?|apn)[:#]?\s*([A-Za-z0-9\-\/]+)\b", full_text, re.I)
        if parcel_match:
            field_map["parcel_number"] = parcel_match.group(1)

    if not field_map.get("assessed_value"):
        value_match = re.search(r"\$\s?[0-9]{1,3}(?:,[0-9]{3})*(?:\.\d+)?", full_text)
        if value_match:
            field_map["assessed_value"] = value_match.group(0)

    if not field_map.get("activity_date"):
        date_match = re.search(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", full_text)
        if date_match:
            field_map["activity_date"] = date_match.group(0)

    service_links = []
    for anchor in soup.find_all("a", href=True):
        text = normalize_text(anchor.get_text(" ", strip=True))
        href = anchor["href"]
        if not text or len(text) > 90:
            continue
        full_href = href if href.startswith(("http://", "https://")) else urljoin(url, href)
        if is_actionable_link(full_href, text):
            service_links.append({"text": text, "href": full_href})

    record = {
        "source_name": "public_page",
        "source_url": url,
        "address": field_map.get("address", heading),
        "city": field_map.get("city", ""),
        "parcel_number": field_map.get("parcel_number", ""),
        "contact_name": field_map.get("contact_name", ""),
        "contact_role": field_map.get("contact_role", ""),
        "assessed_value": field_map.get("assessed_value", ""),
        "activity_date": field_map.get("activity_date", ""),
        "notes": summary,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "title": title,
        "heading": heading,
        "summary": summary,
        "paragraph_count": len(paragraphs),
        "link_count": len(links),
        "links": links[:20],
        "service_links": service_links[:12],
    }
    return record


def build_record_from_url(
    url: str,
    source_name: str = "public_page",
    *,
    source_type: str = "public_page",
    capture_public_contact_names: bool = False,
) -> dict[str, Any]:
    try:
        html = fetch_html(url)
    except requests.RequestException as exc:
        return {
            "source_name": source_name,
            "source_type": source_type,
            "source_url": url,
            "address": "",
            "city": "",
            "parcel_number": "",
            "contact_name": "",
            "contact_role": "",
            "assessed_value": "",
            "activity_date": "",
            "notes": f"Fetch failed: {exc}",
            "error": str(exc),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "title": "",
            "heading": "",
            "summary": "",
            "paragraph_count": 0,
            "link_count": 0,
            "links": [],
        }

    record = extract_page_data(
        html,
        url,
        capture_public_contact_names=capture_public_contact_names,
    )
    record["source_name"] = source_name
    record["source_type"] = source_type
    return record


def build_records_from_target(target: dict[str, Any]) -> list[dict[str, Any]]:
    target_type = (target.get("type") or "web_page").lower()
    if target_type != "property_search":
        return [build_record_from_url(
            target.get("url", ""),
            target.get("name", "public_page"),
            source_type=target_type,
            # Names are only retained when the source has been explicitly reviewed
            # and the name is shown in a public record, not a directory or profile.
            capture_public_contact_names=bool(target.get("allow_public_contact_names", False)),
        )]

    query = str(target.get("query", "") or "").strip()
    if not query:
        return []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept": "application/json",
    }
    url = (
        "https://www.publicrecordsdata.us/api/addresscomplete"
        f"?q={quote(query)}"
        "&addressesOnly=true"
        "&useSearch=false"
        "&useCitySearch=false"
        "&useCityStateSearch=false"
        "&useLocation=true"
        "&useGoogle=false"
        "&useGoogleOverride=false"
        "&useAmazonOverride=false"
        "&isSandboxAccount=false"
        "&isOptOutSearch=false"
    )

    try:
        response = requests.get(url, headers=headers, timeout=25)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        return [{
            "source_name": "publicrecordsdata",
            "source_type": "property_search",
            "source_url": url,
            "address": "",
            "city": "",
            "parcel_number": "",
            "contact_name": "",
            "contact_role": "",
            "assessed_value": "",
            "activity_date": "",
            "notes": f"Property search failed: {exc}",
            "error": str(exc),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }]

    hits = payload.get("hits") or []
    records = []
    for hit in hits:
        full_address = str(hit.get("fullAddress") or "").strip()
        address_parts = full_address.split(",")
        address = address_parts[0] if address_parts else ""
        city = address_parts[1].strip() if len(address_parts) > 1 else ""
        parcel_numbers = hit.get("parcelNumbers") or []
        parcel_number = parcel_numbers[0] if parcel_numbers else ""
        records.append({
            "source_name": "publicrecordsdata",
            "source_type": "property_search",
            "source_url": url,
            "address": address,
            "city": city,
            "parcel_number": parcel_number,
            "contact_name": "",
            "contact_role": "",
            "assessed_value": "",
            "activity_date": "",
            "notes": f"Free-only property search for {query}; No paid report requested",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "title": "Property Search Result",
            "heading": address,
            "summary": full_address,
            "query": query,
            "raw_hit": hit,
            "report_mode": "free_only",
        })

    return records


def select_first_field(field_names: list[str], candidates: list[str]) -> str | None:
    """Return the first matching field name, including common GIS abbreviations."""
    normalized = {re.sub(r"[^A-Z0-9]", "", name.upper()): name for name in field_names}
    for candidate in candidates:
        match = normalized.get(re.sub(r"[^A-Z0-9]", "", candidate.upper()))
        if match:
            return match
    return None


def compose_address(data: dict[str, Any], address_field: str | None, field_names: list[str]) -> str:
    """Read either a full GIS address field or Contra Costa's split street fields."""
    if address_field:
        return normalize_text(str(data.get(address_field, "") or ""))
    parts = [
        data.get(select_first_field(field_names, ["S_STR_NBR", "STREET_NUMBER"]), ""),
        data.get(select_first_field(field_names, ["S_FRAC", "STREET_FRACTION"]), ""),
        data.get(select_first_field(field_names, ["S_STR_NM", "STREET_NAME"]), ""),
        data.get(select_first_field(field_names, ["S_STR_SUF", "STREET_SUFFIX"]), ""),
        data.get(select_first_field(field_names, ["S_APT_NBR", "UNIT", "APT"]), ""),
    ]
    return normalize_text(" ".join(str(part or "") for part in parts))


def is_usable_property_address(address: str) -> bool:
    """Exclude parcel rows that represent roads or unassigned locations."""
    normalized = normalize_text(address).upper()
    if not normalized or normalized.startswith(("NO ADDRESS", "UNASSIGNED", "UNKNOWN")):
        return False
    return bool(re.search(r"\d", normalized))


def matching_city(city: str, requested_cities: set[str]) -> str | None:
    """Match abbreviations such as 'WAL CREEK' to 'WALNUT CREEK'."""
    normalized_city = normalize_text(city).upper()
    if not requested_cities:
        return CONTRA_COSTA_CITY_CODES.get(normalized_city, normalized_city)
    mapped_city = CONTRA_COSTA_CITY_CODES.get(normalized_city)
    if mapped_city and mapped_city in requested_cities:
        return mapped_city
    if normalized_city in requested_cities:
        return normalized_city

    city_tokens = normalized_city.split()
    for requested in requested_cities:
        requested_tokens = requested.split()
        if len(city_tokens) != len(requested_tokens):
            continue
        if all(
            left.startswith(right) or right.startswith(left)
            for left, right in zip(city_tokens, requested_tokens)
        ):
            return requested
    return None


def build_records_from_parcel_shapefile(
    parcel_file: str,
    *,
    source_url: str = CONTRA_COSTA_PARCELS_URL,
    cities: list[str] | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """Create address leads from a public parcel shapefile or its ZIP archive.

    This deliberately extracts property attributes only. Contra Costa's online
    assessor tools do not publish owner names, so this importer never creates
    a contact name.
    """
    try:
        import shapefile  # pyshp
    except ImportError as exc:
        raise SystemExit("Parcel imports require pyshp; run pip install -r scraper/requirements.txt") from exc

    source_path = Path(parcel_file)
    if not source_path.exists():
        raise SystemExit(f"Parcel file does not exist: {source_path}")

    with tempfile.TemporaryDirectory(prefix="eastbay-parcels-") as temp_dir:
        if source_path.suffix.lower() == ".zip":
            with zipfile.ZipFile(source_path) as archive:
                archive.extractall(temp_dir)
            shp_files = list(Path(temp_dir).rglob("*.shp"))
            if not shp_files:
                raise SystemExit("The parcel ZIP did not contain a .shp file")
            reader = shapefile.Reader(str(shp_files[0]))
        else:
            reader = shapefile.Reader(str(source_path))

        field_names = [field[0] for field in reader.fields[1:]]
        address_field = select_first_field(field_names, ["SITUS_ADDR", "SITE_ADDR", "PROPERTY_ADDRESS", "ADDRESS", "SITUSADDRESS"])
        city_field = select_first_field(field_names, ["SITUS_CITY", "SITE_CITY", "CITY", "SITUSCITY", "S_CTY_ABBR"])
        parcel_field = select_first_field(field_names, ["APN", "PARCEL", "PARCEL_NUMBER", "PARCELNO", "APN_NUMBER"])
        value_field = select_first_field(field_names, ["TOTAL_AV", "ASSESSED_VALUE", "ASSESSED", "TOTALVALUE"])

        has_split_address = bool(select_first_field(field_names, ["S_STR_NBR", "STREET_NUMBER"])) and bool(
            select_first_field(field_names, ["S_STR_NM", "STREET_NAME"])
        )
        if not address_field and not has_split_address:
            available = ", ".join(field_names)
            raise SystemExit(f"Could not identify an address field. Available fields: {available}")

        allowed_cities = {normalize_text(city).upper() for city in cities or []}
        records: list[dict[str, Any]] = []
        for shape_record in reader.iterShapeRecords():
            data = shape_record.record.as_dict()
            address = compose_address(data, address_field, field_names)
            city = normalize_text(str(data.get(city_field, "") or "")) if city_field else ""
            matched_city = matching_city(city, allowed_cities)
            if not is_usable_property_address(address) or matched_city is None:
                continue

            assessed_value = data.get(value_field, "") if value_field else ""
            if isinstance(assessed_value, (int, float)):
                assessed_value = f"${assessed_value:,.0f}"
            records.append({
                "source_name": "contra_costa_gis_parcels",
                "source_type": "official_parcel_download",
                "source_url": source_url,
                "address": address,
                "city": matched_city,
                "parcel_number": normalize_text(str(data.get(parcel_field, "") or "")) if parcel_field else "",
                "contact_name": "",
                "contact_role": "",
                "assessed_value": str(assessed_value or ""),
                "activity_date": "",
                "notes": "Official Contra Costa County public parcel download; owner names are not included.",
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            })
            if len(records) >= limit:
                break
    return records


def build_records_from_parcel_url(
    parcel_url: str,
    *,
    cities: list[str] | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """Download one public parcel ZIP and turn it into reviewable address leads."""
    headers = {"User-Agent": "EastBayRealEstateResearch/1.0 (public-record review)"}
    try:
        response = requests.get(parcel_url, headers=headers, timeout=120)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise SystemExit(f"Parcel download failed: {exc}") from exc

    with tempfile.NamedTemporaryFile(suffix=".zip") as downloaded:
        downloaded.write(response.content)
        downloaded.flush()
        return build_records_from_parcel_shapefile(
            downloaded.name,
            source_url=parcel_url,
            cities=cities,
            limit=limit,
        )


def inspect_parcel_shapefile(parcel_file: str, *, sample_size: int = 100) -> tuple[list[str], list[str]]:
    """Return schema and sample city values to configure a new public GIS source."""
    try:
        import shapefile  # pyshp
    except ImportError as exc:
        raise SystemExit("Parcel imports require pyshp; run pip install -r scraper/requirements.txt") from exc

    source_path = Path(parcel_file)
    with tempfile.TemporaryDirectory(prefix="eastbay-parcels-") as temp_dir:
        if source_path.suffix.lower() == ".zip":
            with zipfile.ZipFile(source_path) as archive:
                archive.extractall(temp_dir)
            shp_files = list(Path(temp_dir).rglob("*.shp"))
            if not shp_files:
                raise SystemExit("The parcel ZIP did not contain a .shp file")
            reader = shapefile.Reader(str(shp_files[0]))
        else:
            reader = shapefile.Reader(str(source_path))
        field_names = [field[0] for field in reader.fields[1:]]
        city_field = select_first_field(field_names, ["SITUS_CITY", "SITE_CITY", "CITY", "SITUSCITY", "S_CTY_ABBR"])
        cities: set[str] = set()
        if city_field:
            for shape_record in reader.iterShapeRecords():
                value = normalize_text(str(shape_record.record.as_dict().get(city_field, "") or ""))
                if value:
                    cities.add(value)
                if len(cities) >= sample_size:
                    break
    return field_names, sorted(cities)


def inspect_parcel_url(parcel_url: str) -> tuple[list[str], list[str]]:
    headers = {"User-Agent": "EastBayRealEstateResearch/1.0 (public-record review)"}
    try:
        response = requests.get(parcel_url, headers=headers, timeout=120)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise SystemExit(f"Parcel download failed: {exc}") from exc
    with tempfile.NamedTemporaryFile(suffix=".zip") as downloaded:
        downloaded.write(response.content)
        downloaded.flush()
        return inspect_parcel_shapefile(downloaded.name)


def score_prospect(record: dict[str, Any]) -> tuple[int, str, str]:
    score = 0
    relocation_signal = "none"

    if record.get("address"):
        score += 1

    if record.get("city"):
        score += 1

    if record.get("parcel_number"):
        score += 2

    if record.get("assessed_value"):
        score += 2

    if record.get("activity_date"):
        score += 2

    text_blob = " ".join([
        str(record.get("title", "")),
        str(record.get("heading", "")),
        str(record.get("summary", "")),
        str(record.get("notes", "")),
        str(record.get("source_name", "")),
    ])

    if contains_any(text_blob, ["assessor", "parcel", "property", "tax", "assessment", "property record"]):
        score += 2

    if contains_any(text_blob, ["permit", "business", "license", "planning", "building", "development", "inspection", "zoning", "application"]):
        score += 2

    if record.get("service_links"):
        score += 1

    if contains_any(text_blob, ["relocation", "moving", "new resident", "new to", "welcome"]):
        score += 2
        relocation_signal = "relocation_interest"
    elif contains_any(text_blob, ["permit", "business", "license", "planning", "building", "development", "inspection"]):
        relocation_signal = "property_interest"
    elif contains_any(text_blob, ["property", "assessor", "parcel", "tax", "assessment"]):
        relocation_signal = "property_interest"

    if score >= 8:
        rating = "A"
    elif score >= 5:
        rating = "B"
    elif score >= 3:
        rating = "C"
    else:
        rating = "D"

    if relocation_signal == "none" and score >= 4:
        relocation_signal = "property_interest"

    return score, rating, relocation_signal


def build_prospect_row(record: dict[str, Any]) -> dict[str, Any]:
    score, rating, relocation_signal = score_prospect(record)
    reasons: list[str] = []

    if record.get("address"):
        reasons.append("address")
    if record.get("city"):
        reasons.append("city")
    if record.get("parcel_number"):
        reasons.append("parcel")
    if record.get("assessed_value"):
        reasons.append("value")
    if record.get("activity_date"):
        reasons.append("activity")

    notes = str(record.get("notes", "")).lower()
    if any(keyword in notes for keyword in ["permit", "business", "license", "planning", "building"]):
        reasons.append("public_activity")
    if record.get("service_links"):
        reasons.append("service_links")

    if record.get("parcel_number") or record.get("assessed_value"):
        prospect_type = "property_record"
        data_strength = "high"
    elif any(keyword in str(record.get("notes", "")).lower() for keyword in ["permit", "license", "planning", "building", "development", "inspection"]):
        prospect_type = "permit_signal"
        data_strength = "medium"
    elif record.get("service_links"):
        prospect_type = "service_page"
        data_strength = "medium"
    else:
        prospect_type = "metadata"
        data_strength = "low"

    row = {
        "source_name": record.get("source_name", ""),
        "source_type": record.get("source_type", ""),
        "source_url": record.get("source_url", ""),
        "address": record.get("address", ""),
        "city": record.get("city", ""),
        "parcel_number": record.get("parcel_number", ""),
        "contact_name": record.get("contact_name", ""),
        "contact_role": record.get("contact_role", ""),
        "assessed_value": record.get("assessed_value", ""),
        "activity_date": record.get("activity_date", ""),
        "notes": record.get("notes", ""),
        "lead_rating": rating,
        "lead_reason": ", ".join(reasons) if reasons else "public_page",
        "relocation_signal": relocation_signal,
        "prospect_type": prospect_type,
        "data_strength": data_strength,
        "review_status": "needs_review",
        "scraped_at": record.get("scraped_at", ""),
    }
    return row


def deduplicate_and_rank_records(records: list[dict[str, Any]], limit: int = 40) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}

    for record in records:
        normalized_address = normalize_property_address(record.get("address"))
        normalized_city = normalize_text(record.get("city")).upper()
        key = (normalized_address, normalized_city)

        existing = grouped.get(key)
        if existing is None:
            # Keep the complete source record. The previous implementation
            # replaced it with a synthetic B-rated record, discarding useful
            # evidence such as assessed value, activity date, and source type.
            grouped[key] = {**record, "address": normalized_address, "city": normalized_city}
            continue

        if record.get("parcel_number") and not existing.get("parcel_number"):
            existing["parcel_number"] = record.get("parcel_number", "")
        if not existing.get("notes") and record.get("notes"):
            existing["notes"] = record.get("notes", "")
        if not existing.get("contact_name") and record.get("contact_name"):
            existing["contact_name"] = record.get("contact_name", "")
            existing["contact_role"] = record.get("contact_role", "")

    ranked = sorted(
        grouped.values(),
        key=lambda item: (
            -score_prospect(item)[0],
            item.get("address", ""),
        ),
    )
    return ranked[:limit]


def save_results(records: list[dict[str, Any]], output_path: str, *, limit: int = 40) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    if output.suffix.lower() == ".csv":
        cleaned_records = deduplicate_and_rank_records(records, limit=limit)
        prospect_rows = []
        for record in cleaned_records:
            base_row = build_prospect_row(record)
            prospect_rows.append(base_row)

        fieldnames = DEFAULT_OUTPUT_FIELDS + ["title", "heading", "summary", "paragraph_count", "link_count"]
        with output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in prospect_rows:
                writer.writerow({key: row.get(key, "") for key in fieldnames})
    else:
        output.write_text(json.dumps(records, indent=2), encoding="utf-8")

    return output


def save_to_database(records: list[dict[str, Any]], database_path: str, *, limit: int = 40) -> int:
    """Upsert reviewable leads and append their source evidence to SQLite."""
    database = Path(database_path)
    database.parent.mkdir(parents=True, exist_ok=True)
    cleaned_records = deduplicate_and_rank_records(records, limit=limit)
    rows = [build_prospect_row(record) for record in cleaned_records]

    with sqlite3.connect(database) as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY,
                normalized_address TEXT NOT NULL,
                city TEXT NOT NULL,
                address TEXT NOT NULL,
                parcel_number TEXT,
                contact_name TEXT,
                contact_role TEXT,
                assessed_value TEXT,
                activity_date TEXT,
                lead_rating TEXT NOT NULL,
                lead_reason TEXT,
                relocation_signal TEXT,
                prospect_type TEXT,
                data_strength TEXT,
                review_status TEXT NOT NULL DEFAULT 'needs_review',
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                last_source_name TEXT,
                last_source_type TEXT,
                last_source_url TEXT,
                last_notes TEXT,
                UNIQUE(normalized_address, city)
            );

            CREATE TABLE IF NOT EXISTS lead_observations (
                id INTEGER PRIMARY KEY,
                lead_id INTEGER NOT NULL REFERENCES leads(id),
                observed_at TEXT NOT NULL,
                source_name TEXT,
                source_type TEXT,
                source_url TEXT,
                notes TEXT,
                parcel_number TEXT,
                assessed_value TEXT,
                activity_date TEXT
            );
        """)

        for row in rows:
            normalized_address = normalize_property_address(row["address"])
            values = {
                **row,
                "normalized_address": normalized_address,
                "first_seen_at": row["scraped_at"],
                "last_seen_at": row["scraped_at"],
                "last_source_name": row["source_name"],
                "last_source_type": row["source_type"],
                "last_source_url": row["source_url"],
                "last_notes": row["notes"],
            }
            connection.execute("""
                INSERT INTO leads (
                    normalized_address, city, address, parcel_number, contact_name, contact_role,
                    assessed_value, activity_date, lead_rating, lead_reason, relocation_signal,
                    prospect_type, data_strength, review_status, first_seen_at, last_seen_at,
                    last_source_name, last_source_type, last_source_url, last_notes
                ) VALUES (
                    :normalized_address, :city, :address, :parcel_number, :contact_name, :contact_role,
                    :assessed_value, :activity_date, :lead_rating, :lead_reason, :relocation_signal,
                    :prospect_type, :data_strength, :review_status, :first_seen_at, :last_seen_at,
                    :last_source_name, :last_source_type, :last_source_url, :last_notes
                )
                ON CONFLICT(normalized_address, city) DO UPDATE SET
                    address = excluded.address,
                    parcel_number = COALESCE(NULLIF(excluded.parcel_number, ''), leads.parcel_number),
                    contact_name = COALESCE(NULLIF(excluded.contact_name, ''), leads.contact_name),
                    contact_role = COALESCE(NULLIF(excluded.contact_role, ''), leads.contact_role),
                    assessed_value = COALESCE(NULLIF(excluded.assessed_value, ''), leads.assessed_value),
                    activity_date = COALESCE(NULLIF(excluded.activity_date, ''), leads.activity_date),
                    lead_rating = excluded.lead_rating,
                    lead_reason = excluded.lead_reason,
                    relocation_signal = excluded.relocation_signal,
                    prospect_type = excluded.prospect_type,
                    data_strength = excluded.data_strength,
                    review_status = CASE
                        WHEN leads.review_status = 'needs_review' THEN excluded.review_status
                        ELSE leads.review_status
                    END,
                    last_seen_at = excluded.last_seen_at,
                    last_source_name = excluded.last_source_name,
                    last_source_type = excluded.last_source_type,
                    last_source_url = excluded.last_source_url,
                    last_notes = excluded.last_notes
            """, values)
            lead_id = connection.execute(
                "SELECT id FROM leads WHERE normalized_address = ? AND city = ?",
                (normalized_address, row["city"]),
            ).fetchone()[0]
            connection.execute("""
                INSERT INTO lead_observations (
                    lead_id, observed_at, source_name, source_type, source_url,
                    notes, parcel_number, assessed_value, activity_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lead_id, row["scraped_at"], row["source_name"], row["source_type"], row["source_url"],
                row["notes"], row["parcel_number"], row["assessed_value"], row["activity_date"],
            ))
    return len(rows)


def read_urls(path: str) -> list[str]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    urls = [line.strip() for line in lines if line.strip() and not line.startswith("#")]
    return urls


def read_queries(path: str) -> list[str]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    queries = [line.strip() for line in lines if line.strip() and not line.startswith("#")]
    return queries


def load_targets(path: str) -> list[dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    sources = data.get("sources", [])
    return sources


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape a public web page and save the results")
    parser.add_argument("--url", help="URL to scrape")
    parser.add_argument("--urls-file", help="Text file containing one URL per line")
    parser.add_argument("--queries-file", help="Text file containing one address/query per line")
    parser.add_argument("--targets-file", help="JSON file containing a list of source targets")
    parser.add_argument("--parcels-file", help="Public parcel .shp file or ZIP archive to turn into address leads")
    parser.add_argument("--parcels-url", help="Direct URL to one public parcel ZIP archive")
    parser.add_argument("--parcel-cities", help="Optional comma-separated city filter for --parcels-file")
    parser.add_argument("--inspect-parcels", action="store_true", help="Print parcel schema and sample city values, then exit")
    parser.add_argument("--limit", type=int, default=40, help="Maximum number of rows in CSV output")
    parser.add_argument("--database", help="Optional SQLite database path for persistent lead tracking")
    parser.add_argument("--output", default="scraper/output/results.json", help="Output file path")
    parser.add_argument("--demo", action="store_true", help="Scrape the demo URL instead of requiring --url")
    args = parser.parse_args()

    records: list[dict[str, Any]] = []

    if args.inspect_parcels:
        if args.parcels_file:
            fields, cities = inspect_parcel_shapefile(args.parcels_file)
        elif args.parcels_url:
            fields, cities = inspect_parcel_url(args.parcels_url)
        else:
            raise SystemExit("--inspect-parcels requires --parcels-file or --parcels-url")
        print(f"Fields: {', '.join(fields)}")
        print(f"Sample city values: {', '.join(cities) or '(no city field found)'}")
        return

    if args.parcels_file:
        cities = args.parcel_cities.split(",") if args.parcel_cities else None
        records = build_records_from_parcel_shapefile(
            args.parcels_file,
            cities=cities,
            limit=args.limit,
        )
    elif args.parcels_url:
        cities = args.parcel_cities.split(",") if args.parcel_cities else None
        records = build_records_from_parcel_url(
            args.parcels_url,
            cities=cities,
            limit=args.limit,
        )
    elif args.targets_file:
        targets = load_targets(args.targets_file)
        for target in targets:
            records.extend(build_records_from_target(target))
    elif args.queries_file:
        for query in read_queries(args.queries_file):
            records.extend(build_records_from_target({"type": "property_search", "query": query}))
    elif args.demo:
        records.append(build_record_from_url(DEFAULT_DEMO_URL))
    elif args.url:
        records.append(build_record_from_url(args.url))
    elif args.urls_file:
        for current_url in read_urls(args.urls_file):
            records.append(build_record_from_url(current_url))
    else:
        raise SystemExit("Provide --url, --urls-file, --targets-file, or --demo")

    output_path = save_results(records, args.output, limit=args.limit)
    print(f"Saved {len(records)} record(s) to {output_path}")
    if args.database:
        saved_count = save_to_database(records, args.database, limit=args.limit)
        print(f"Saved {saved_count} lead(s) to {args.database}")


if __name__ == "__main__":
    main()
