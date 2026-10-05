import ipaddress
import re
import socket
import urllib.parse
import requests
from bs4 import BeautifulSoup

BLOCKED_HOSTNAMES = {"localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254", "[::1]"}


def is_ip_private(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast
    except ValueError:
        return False


def validate_url(url: str):
    if not url or not isinstance(url, str):
        raise ValueError("Invalid URL: URL must be a non-empty string.")

    parsed = urllib.parse.urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Invalid URL scheme. Only http:// and https:// URLs are allowed.")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Invalid URL: missing domain or hostname.")

    hostname_lower = hostname.lower()
    if hostname_lower in BLOCKED_HOSTNAMES:
        raise ValueError("Access to local/private network resources is blocked.")

    if is_ip_private(hostname_lower):
        raise ValueError("Access to private IP addresses is blocked.")

    try:
        resolved_ips = socket.getaddrinfo(hostname, None)
        for res in resolved_ips:
            ip_str = res[4][0]
            if is_ip_private(ip_str):
                raise ValueError("Domain resolves to a private IP address.")
    except socket.gaierror:
        pass


def scrape_article(url: str):
    validate_url(url)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15, stream=True)
        response.raise_for_status()

        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > 5 * 1024 * 1024:
            raise ValueError("Target article is too large (max limit is 5MB).")

        content_bytes = bytearray()
        for chunk in response.iter_content(chunk_size=8192):
            content_bytes.extend(chunk)
            if len(content_bytes) > 5 * 1024 * 1024:
                raise ValueError("Target article exceeds 5MB size limit.")

        encoding = response.encoding or "utf-8"
        text = content_bytes.decode(encoding, errors="replace")

    except requests.Timeout:
        raise ValueError("Connection timed out while fetching article.")
    except requests.HTTPError as e:
        raise ValueError(f"HTTP error status {response.status_code} while fetching article: {e}")
    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch article URL: {e}")

    soup = BeautifulSoup(text, "html.parser")

    for element in soup(["script", "style", "nav", "footer", "header", "aside", "form", "figure", "figcaption", "time"]):
        element.decompose()

    audio_label = re.compile(
        r"^(?:listen\s+to\s+this\s+article|\d+\s*(?:minute|minutes|second|seconds)\s+listen)\b",
        re.IGNORECASE,
    )
    for element in soup.find_all(["button", "a", "span", "div", "p"]):
        element_text = element.get_text(" ", strip=True)
        if len(element_text) <= 120 and audio_label.match(element_text):
            element.decompose()

    title = soup.title.get_text(strip=True) if soup.title else ""
    if not title:
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)
    if not title:
        title = "Untitled Article"

    raw_paragraphs = soup.find_all("p")
    cleaned_paragraphs = []
    
    NOISE_PREFIXES = (
        "photo by", "photo:", "image:", "illustration by", "credit:",
        "getty images", "panos pictures", "listen to this article",
        "minute listen", "minutes listen"
    )

    for p in raw_paragraphs:
        p_text = p.get_text(" ", strip=True)
        if not p_text:
            continue
        p_lower = p_text.lower()
        if re.match(r"^\d+\s*(?:minute|minutes|second|seconds)\s+listen\b", p_lower):
            continue
        if any(p_lower.startswith(prefix) for prefix in NOISE_PREFIXES):
            continue
        if p_lower.startswith("is ") and ("professor" in p_lower or "researcher" in p_lower or "author" in p_lower or "fellow" in p_lower):
            continue
        if "cookie" in p_lower and "privacy" in p_lower:
            continue
        cleaned_paragraphs.append(p_text)

    # Deduplicate consecutive identical paragraphs
    final_paragraphs = []
    for p in cleaned_paragraphs:
        if not final_paragraphs or p != final_paragraphs[-1]:
            final_paragraphs.append(p)

    content = "\n\n".join(final_paragraphs)

    if not content or len(content.strip()) < 50:
        body = soup.find("body")
        if body:
            content = body.get_text(" ", strip=True)

    if not content or len(content.strip()) < 20:
        raise ValueError("Could not extract readable article text from the URL.")

    return {
        "title": title,
        "content": content
    }


if __name__ == "__main__":
    test_url = "https://psyche.co/guides/how-to-solve-problems-by-thinking-like-a-detective"
    article = scrape_article(test_url)
    print("\nTITLE:", article["title"])
    print("\nCONTENT:", article["content"], "...")