import requests
from bs4 import BeautifulSoup


def scrape_article(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove unnecessary elements
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()

    # Get title
    title = soup.title.get_text(strip=True) if soup.title else "Unknown Title"

    # Get article paragraphs
    paragraphs = soup.find_all("p")

    content = "\n".join(
        paragraph.get_text(" ", strip=True)
        for paragraph in paragraphs
        if paragraph.get_text(strip=True)
    )

    return {
        "title": title,
        "content": content
    }


if __name__ == "__main__":

    url = "https://psyche.co/guides/how-to-solve-problems-by-thinking-like-a-detective"

    article = scrape_article(url)

    print("\nTITLE:")
    print(article["title"])

    print("\nCONTENT:")
    print(article["content"])