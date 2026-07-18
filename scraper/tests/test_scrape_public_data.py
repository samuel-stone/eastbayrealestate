import sys
import sqlite3
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scraper.scrape_public_data import (
    build_prospect_row,
    build_record_from_url,
    build_records_from_target,
    deduplicate_and_rank_records,
    extract_page_data,
    normalize_property_address,
    read_queries,
    select_first_field,
    score_prospect,
    save_to_database,
    build_records_from_parcel_url,
    compose_address,
    matching_city,
    is_usable_property_address,
)


def test_extract_page_data_returns_expected_fields():
    html = """
    <html>
      <head><title>Example Property Page</title></head>
      <body>
        <h1>123 Main St</h1>
        <p>Property summary for a sample home.</p>
        <p>Another paragraph.</p>
        <a href="https://example.com/next">Next</a>
      </body>
    </html>
    """

    result = extract_page_data(html, "https://example.com")

    assert result["title"] == "Example Property Page"
    assert result["heading"] == "123 Main St"
    assert result["summary"] == "Property summary for a sample home."
    assert result["paragraph_count"] == 2
    assert result["link_count"] == 1
    assert result["links"] == ["https://example.com/next"]


def test_extract_property_fields_from_labels():
    html = """
    <html>
      <body>
        <h1>Property Details</h1>
        <table>
          <tr><th>Address</th><td>123 Main St</td></tr>
          <tr><th>City</th><td>Walnut Creek</td></tr>
          <tr><th>Parcel Number</th><td>123-456-789</td></tr>
          <tr><th>Assessed Value</th><td>$750,000</td></tr>
          <tr><th>Activity Date</th><td>07/17/2026</td></tr>
        </table>
      </body>
    </html>
    """

    result = extract_page_data(html, "https://example.com/property")

    assert result["address"] == "123 Main St"
    assert result["city"] == "Walnut Creek"
    assert result["parcel_number"] == "123-456-789"
    assert result["assessed_value"] == "$750,000"
    assert result["activity_date"] == "07/17/2026"


def test_public_contact_name_requires_explicit_target_permission():
    html = """
    <table><tr><th>Project Applicant</th><td>Jordan Example</td></tr></table>
    """

    withheld = extract_page_data(html, "https://example.com/record")
    retained = extract_page_data(
        html,
        "https://example.com/record",
        capture_public_contact_names=True,
    )

    assert withheld["contact_name"] == ""
    assert retained["contact_name"] == "Jordan Example"
    assert retained["contact_role"] == "public_record_contact"


def test_normalize_property_address_removes_unit_suffixes():
    assert normalize_property_address("1116 FAIRLAWN CT APT 4") == "1116 FAIRLAWN CT"
    assert normalize_property_address("123 MAIN ST UNIT 12") == "123 MAIN ST"


def test_select_first_field_handles_common_gis_address_names():
    fields = ["APN_NUMBER", "SITUS_ADDR", "SITUS_CITY", "TOTAL_AV"]

    assert select_first_field(fields, ["ADDRESS", "SITUS_ADDR"]) == "SITUS_ADDR"
    assert select_first_field(fields, ["PARCEL", "APN"]) is None


def test_compose_address_supports_contra_costa_split_fields():
    fields = ["S_STR_NBR", "S_STR_NM", "S_STR_SUF", "S_APT_NBR"]
    record = {"S_STR_NBR": "123", "S_STR_NM": "MAIN", "S_STR_SUF": "ST", "S_APT_NBR": "4"}

    assert compose_address(record, None, fields) == "123 MAIN ST 4"


def test_is_usable_property_address_excludes_unassigned_parcels():
    assert is_usable_property_address("123 Main St") is True
    assert is_usable_property_address("NO ADDRESS") is False
    assert is_usable_property_address("CITRUS CIR") is False


def test_matching_city_accepts_county_abbreviations():
    cities = {"WALNUT CREEK", "LAFAYETTE", "ORINDA"}

    assert matching_city("WAL CREEK", cities) == "WALNUT CREEK"
    assert matching_city("WALCR", cities) == "WALNUT CREEK"
    assert matching_city("LAFAYETTE", cities) == "LAFAYETTE"
    assert matching_city("CONCORD", cities) is None


def test_parcel_url_download_failure_is_actionable(monkeypatch):
    def raise_error(*args, **kwargs):
        raise requests.ConnectionError("offline")

    monkeypatch.setattr("scraper.scrape_public_data.requests.get", raise_error)

    try:
        build_records_from_parcel_url("https://example.com/parcels.zip")
    except SystemExit as exc:
        assert "Parcel download failed" in str(exc)
    else:
        raise AssertionError("Expected parcel URL download to fail")


def test_save_to_database_preserves_review_status_and_history(tmp_path):
    database = tmp_path / "leads.sqlite3"
    record = {
        "source_name": "county",
        "source_type": "official_parcel_download",
        "source_url": "https://example.com/parcels.zip",
        "address": "123 Main St Apt 1",
        "city": "Walnut Creek",
        "parcel_number": "123-456",
        "notes": "Public parcel record",
        "scraped_at": "2026-07-17T00:00:00+00:00",
    }

    assert save_to_database([record], str(database)) == 1
    with sqlite3.connect(database) as connection:
        connection.execute("UPDATE leads SET review_status = 'approved'")

    record["scraped_at"] = "2026-07-18T00:00:00+00:00"
    assert save_to_database([record], str(database)) == 1
    with sqlite3.connect(database) as connection:
        lead = connection.execute("SELECT review_status, first_seen_at, last_seen_at FROM leads").fetchone()
        observation_count = connection.execute("SELECT COUNT(*) FROM lead_observations").fetchone()[0]

    assert lead == ("approved", "2026-07-17T00:00:00+00:00", "2026-07-18T00:00:00+00:00")
    assert observation_count == 2


def test_deduplicate_and_rank_records_keeps_one_row_per_property():
    records = [
        {"address": "1116 FAIRLAWN CT APT 4", "city": "WALNUT CREEK", "parcel_number": "900-001-502-5"},
        {"address": "1116 FAIRLAWN CT APT 6", "city": "WALNUT CREEK", "parcel_number": "900-001-504-1"},
        {"address": "123 MAIN ST", "city": "CONCORD", "parcel_number": "111-222-333-4"},
    ]

    cleaned = deduplicate_and_rank_records(records, limit=5)

    assert len(cleaned) == 2
    assert cleaned[0]["address"] == "1116 FAIRLAWN CT"
    assert cleaned[0]["parcel_number"] == "900-001-502-5"
    assert cleaned[1]["address"] == "123 MAIN ST"


def test_deduplicate_and_rank_records_retains_source_evidence():
    records = [{
        "address": "123 Main St Apt 1",
        "city": "Concord",
        "parcel_number": "111-222-333-4",
        "assessed_value": "$750,000",
        "activity_date": "07/17/2026",
        "source_type": "permit_page",
        "contact_name": "Jordan Example",
    }]

    cleaned = deduplicate_and_rank_records(records)

    assert cleaned[0]["assessed_value"] == "$750,000"
    assert cleaned[0]["activity_date"] == "07/17/2026"
    assert cleaned[0]["source_type"] == "permit_page"
    assert cleaned[0]["contact_name"] == "Jordan Example"


def test_build_prospect_row_assigns_rating_and_signal():
    record = {
        "source_name": "fixture",
        "source_url": "https://example.com/property",
        "address": "123 Main St",
        "city": "Walnut Creek",
        "parcel_number": "123-456",
        "assessed_value": "$750,000",
        "activity_date": "07/17/2026",
        "notes": "Permit information for a new business",
        "summary": "Welcome to the area",
        "service_links": [{"text": "Business Licenses", "href": "https://example.com"}],
    }

    prospect = build_prospect_row(record)

    assert prospect["lead_rating"] == "A"
    assert prospect["relocation_signal"] == "relocation_interest"


def test_score_prospect_prioritizes_property_and_permit_signals():
    record = {
        "address": "123 Main St",
        "city": "Walnut Creek",
        "parcel_number": "123-456",
        "assessed_value": "$750,000",
        "activity_date": "07/17/2026",
        "notes": "Building permit application",
        "service_links": [{"text": "Building Permits", "href": "https://example.com"}],
    }

    score, rating, signal = score_prospect(record)

    assert score >= 9
    assert rating == "A"
    assert signal == "property_interest"


def test_build_records_from_target_supports_property_search(monkeypatch):
    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    payload = {
        "q": "1116 Fairlawn Ct Walnut Creek CA 94595",
        "hits": [
            {
                "id": "123",
                "fullAddress": "1116 FAIRLAWN CT APT 4, WALNUT CREEK, CA 94595",
                "slug": "/ca/walnut-creek/1116-fairlawn-ct-apt-4/94595",
                "parcelNumbers": ["900-001-502-5"],
            }
        ],
    }

    monkeypatch.setattr("scraper.scrape_public_data.requests.get", lambda *args, **kwargs: FakeResponse(payload))

    records = build_records_from_target({"type": "property_search", "query": "1116 Fairlawn Ct Walnut Creek CA 94595"})

    assert len(records) == 1
    assert records[0]["address"] == "1116 FAIRLAWN CT APT 4"
    assert records[0]["city"] == "WALNUT CREEK"
    assert records[0]["parcel_number"] == "900-001-502-5"
    assert records[0]["source_name"] == "publicrecordsdata"


def test_read_queries_reads_addresses_from_text_file(tmp_path):
    query_file = tmp_path / "addresses.txt"
    query_file.write_text("1116 Fairlawn Ct Walnut Creek CA 94595\n\n123 Main St Concord CA 94520\n", encoding="utf-8")

    queries = read_queries(str(query_file))

    assert queries == ["1116 Fairlawn Ct Walnut Creek CA 94595", "123 Main St Concord CA 94520"]


def test_property_search_results_are_marked_as_free_only(monkeypatch):
    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    payload = {
        "q": "1116 Fairlawn Ct Walnut Creek CA 94595",
        "hits": [
            {
                "id": "123",
                "fullAddress": "1116 FAIRLAWN CT APT 4, WALNUT CREEK, CA 94595",
                "slug": "/ca/walnut-creek/1116-fairlawn-ct-apt-4/94595",
                "parcelNumbers": ["900-001-502-5"],
            }
        ],
    }

    monkeypatch.setattr("scraper.scrape_public_data.requests.get", lambda *args, **kwargs: FakeResponse(payload))

    records = build_records_from_target({"type": "property_search", "query": "1116 Fairlawn Ct Walnut Creek CA 94595"})

    assert records[0]["report_mode"] == "free_only"
    assert "No paid report" in records[0]["notes"]


def test_build_record_from_url_records_fetch_error(monkeypatch):
    def raise_error(url: str) -> str:
        raise requests.HTTPError("simulated fetch failure")

    monkeypatch.setattr("scraper.scrape_public_data.fetch_html", raise_error)

    result = build_record_from_url("https://example.com/bad", "bad_source")

    assert result["source_name"] == "bad_source"
    assert result["source_url"] == "https://example.com/bad"
    assert result["notes"].startswith("Fetch failed")
    assert result["error"] == "simulated fetch failure"
