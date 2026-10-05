import pytest
from services.scrapper import validate_url, is_ip_private


def test_validate_url_valid():
    # Should not raise exception
    validate_url("https://example.com/article")


def test_validate_url_invalid_scheme():
    with pytest.raises(ValueError, match="Only http:// and https:// URLs are allowed"):
        validate_url("ftp://example.com/file")


def test_validate_url_private_ip():
    with pytest.raises(ValueError, match="blocked"):
        validate_url("http://127.0.0.1/admin")


def test_is_ip_private():
    assert is_ip_private("127.0.0.1") is True
    assert is_ip_private("10.0.0.1") is True
    assert is_ip_private("8.8.8.8") is False
