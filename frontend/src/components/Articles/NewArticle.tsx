import { FormEvent, useState } from "react";
import { fetchArticle } from "../Common/articleReader";

type NewArticleProps = {
  onOpen?: (url: string, article?: unknown) => void;
};

function NewArticle({ onOpen }: NewArticleProps) {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const articleUrl = url.trim();
    if (!articleUrl) return;

    setLoading(true);
    setError(null);

    try {
      const article = await fetchArticle(articleUrl);
      onOpen?.(articleUrl, article);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      if (typeof detail === "string") {
        setError(detail);
      } else if (err?.message) {
        setError(err.message);
      } else {
        setError("Couldn't open that article. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="new-article" aria-labelledby="new-article-title">
      <h2 id="new-article-title">Read any article</h2>
      <p>
        Paste a link and InsightAI opens it in a clean reader you can summarize
        or ask questions about.
      </p>

      <form className="new-article-form" onSubmit={handleSubmit}>
        <label className="url-input" htmlFor="article-url">
          <span aria-hidden="true">🔗</span>
          <span className="sr-only">Article URL</span>
          <input
            id="article-url"
            type="url"
            inputMode="url"
            placeholder="https://example.com/article"
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            disabled={loading}
            required
          />
        </label>
        <button className="reader-button" type="submit" disabled={loading}>
          {loading ? "Opening..." : "Open in reader"}
        </button>
      </form>

      {error && (
        <p role="alert" style={{ color: "#d93838", marginTop: "12px", fontSize: "14px", fontWeight: 600 }}>
          {error}
        </p>
      )}
    </section>
  );
}

export default NewArticle;