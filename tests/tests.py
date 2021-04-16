import pytest
import requests

from scraperuodas.main import Scraperuodas


def test_generate_single_url() -> None:
    scraper = Scraperuodas()
    test_url = ["https://www.aruodas.lt/butu-nuoma/vilniuje/"]
    returned_url = scraper.generate_urls(27, "vilniuje", 400)
    assert test_url == returned_url


def test_generate_multiple_url() -> None:
    scraper = Scraperuodas()
    test_urls = [
        "https://www.aruodas.lt/butu-nuoma/vilniuje/",
        "https://www.aruodas.lt/butu-nuoma/vilniuje/puslapis/2",
    ]
    returned_urls = scraper.generate_urls(28, "vilniuje", 400)
    assert test_urls == returned_urls


def test_response_status_code() -> None:
    test_url = "https://www.aruodas.lt/butu-nuoma/vilniuje/"
    test_params = {"FOrder": "AddDate", "FPriceMax": "400"}
    resp = requests.get(test_url, params=test_params)
    assert resp.status_code == 200
