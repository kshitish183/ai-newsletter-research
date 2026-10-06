import pytest
from unittest.mock import patch, MagicMock
import requests
from services.scrapper import scrape_article, validate_url


def test_validate_url_blocks_internal_hosts():
    with pytest.raises(ValueError, match="blocked"):
        validate_url("http://localhost:8000")

    with pytest.raises(ValueError, match="blocked"):
        validate_url("http://169.254.169.254/latest/meta-data")


@patch("requests.Session.get")
def test_scrape_article_detects_private_redirect(mock_get):
    # Mock initial response as a 302 redirect to a private IP
    mock_redirect_res = MagicMock()
    mock_redirect_res.is_redirect = True
    mock_redirect_res.status_code = 302
    mock_redirect_res.headers = {"Location": "http://127.0.0.1/admin"}
    mock_get.return_value = mock_redirect_res

    with pytest.raises(ValueError, match="blocked"):
        scrape_article("https://example.com/redirect-to-private")


@patch("requests.Session.get")
def test_scrape_article_detects_too_many_redirects(mock_get):
    # Mock infinite redirect loop between public URLs
    mock_redirect_res = MagicMock()
    mock_redirect_res.is_redirect = True
    mock_redirect_res.status_code = 302
    mock_redirect_res.headers = {"Location": "https://example.com/redirect-loop"}
    mock_get.return_value = mock_redirect_res

    with pytest.raises(ValueError, match="Too many redirects"):
        scrape_article("https://example.com/redirect-loop")
