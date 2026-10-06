import { useState, useEffect } from "react";
import NewArticle from "../Articles/NewArticle";
import ArticleViewer, { ArticleData } from "../AI/ArticleViewer";
import Header from "./Header";
import Sidebar from "./sidebar";
import "./Layout.css";

type Article = {
  title: string;
  description: string;
  time: string;
  topic: string;
  tone: "violet" | "blue" | "orange";
};

const initialArticles: Article[] = [
  {
    title: "The quiet revolution in artificial intelligence",
    description:
      "A look at the ideas reshaping the way we build and work with AI.",
    time: "8 min",
    topic: "AI",
    tone: "violet",
  },
  {
    title: "Designing technology people want to use",
    description:
      "The principles that turn helpful products into lasting habits.",
    time: "6 min",
    topic: "Technology",
    tone: "blue",
  },
  {
    title: "The science of a more curious mind",
    description:
      "Why better questions can lead to more creative breakthroughs.",
    time: "10 min",
    topic: "Science",
    tone: "orange",
  },
];

const filters = [
  "All",
  "Technology",
  "Science",
  "Business",
  "Saved",
];

type StatCardProps = {
  value: string;
  label: string;
  detail: string;
};

function StatCard({ value, label, detail }: StatCardProps) {
  return (
    <article className="stat-card">
      <strong>{value}</strong>
      <span>{label}</span>
      <small>{detail}</small>
    </article>
  );
}

type ArticleCardProps = {
  article: Article;
  isBookmarked: boolean;
  onToggleBookmark: () => void;
  onSelect?: () => void;
};

function ArticleCard({
  article,
  isBookmarked,
  onToggleBookmark,
  onSelect,
}: ArticleCardProps) {
  return (
    <article
      className="article-card"
      onClick={onSelect}
      style={{ cursor: "pointer" }}
    >
      <div className={`article-cover ${article.tone}`}>
        <span>{article.topic.slice(0, 2).toUpperCase()}</span>

        <button
          type="button"
          aria-label={`Bookmark ${article.title}`}
          title={isBookmarked ? "Remove bookmark" : "Bookmark article"}
          onClick={(e) => {
            e.stopPropagation();
            onToggleBookmark();
          }}
          style={{ color: isBookmarked ? "#6b4ce6" : "#536078", fontWeight: "bold" }}
        >
          {isBookmarked ? "★" : "♧"}
        </button>
      </div>

      <div className="article-body">
        <p className="article-tag">{article.topic}</p>

        <h3>{article.title}</h3>

        <p>{article.description}</p>

        <footer>
          <span>◷ {article.time}</span>

          <button
            type="button"
            aria-label={`Bookmark ${article.title}`}
            title={isBookmarked ? "Remove bookmark" : "Bookmark article"}
            onClick={(e) => {
              e.stopPropagation();
              onToggleBookmark();
            }}
            style={{ color: isBookmarked ? "#6b4ce6" : "#536078", fontWeight: "bold" }}
          >
            {isBookmarked ? "★" : "♧"}
          </button>
        </footer>
      </div>
    </article>
  );
}

function MainLayout() {
  const [activeFilter, setActiveFilter] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedArticle, setSelectedArticle] = useState<ArticleData | null>(null);
  const [isViewerOpen, setIsViewerOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Persistent bookmark state
  const [bookmarkedTitles, setBookmarkedTitles] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem("ia-bookmarks");
      return saved ? JSON.parse(saved) : ["The quiet revolution in artificial intelligence"];
    } catch {
      return ["The quiet revolution in artificial intelligence"];
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem("ia-bookmarks", JSON.stringify(bookmarkedTitles));
    } catch (e) {
      console.error(e);
    }
  }, [bookmarkedTitles]);

  const toggleBookmark = (title: string) => {
    setBookmarkedTitles((prev) =>
      prev.includes(title) ? prev.filter((t) => t !== title) : [...prev, title]
    );
  };

  function openArticle(_url?: string, articleData?: unknown) {
    if (articleData && typeof articleData === "object") {
      setSelectedArticle(articleData as ArticleData);
    } else {
      setSelectedArticle(null); // Will default to the sample article in ArticleViewer
    }
    setIsViewerOpen(true);
  }

  const handleAction = (action: string) => {
    if (action === "new-article" || action === "ask-ai") {
      const input = document.getElementById("article-url");
      if (input) {
        input.focus();
        input.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    } else if (action === "settings") {
      alert("Settings: InsightAI configuration active.");
    }
  };

  // Filter and search logic
  const filteredArticles = initialArticles.filter((article) => {
    const matchesFilter =
      activeFilter === "All"
        ? true
        : activeFilter === "Saved"
        ? bookmarkedTitles.includes(article.title)
        : article.topic.toLowerCase() === activeFilter.toLowerCase();

    const query = searchQuery.trim().toLowerCase();
    const matchesSearch =
      !query ||
      article.title.toLowerCase().includes(query) ||
      article.description.toLowerCase().includes(query) ||
      article.topic.toLowerCase().includes(query);

    return matchesFilter && matchesSearch;
  });

  const uniqueTopicsCount = new Set(initialArticles.map((a) => a.topic)).size;

  if (isViewerOpen) {
    return (
      <ArticleViewer
        articleData={selectedArticle || undefined}
        onBack={() => setIsViewerOpen(false)}
      />
    );
  }

  return (
    <div className="app-shell" id="dashboard">
      {/* Sidebar */}
      <Sidebar
        activeFilter={activeFilter}
        onSelectFilter={(f) => setActiveFilter(f)}
        onSelectAction={handleAction}
        isMobileOpen={isMobileMenuOpen}
        onCloseMobile={() => setIsMobileMenuOpen(false)}
      />

      {isMobileMenuOpen && (
        <div
          className="sidebar-backdrop"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      <div className="page-frame">
        {/* Header */}
        <Header
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          onToggleMobileMenu={() => setIsMobileMenuOpen((prev) => !prev)}
          isMobileMenuOpen={isMobileMenuOpen}
        />

        <main className="dashboard-content">
          {/* Welcome Section */}
          <section className="welcome-section" aria-labelledby="welcome-title">
            <p className="eyebrow">Tuesday, September 8</p>

            <h1 id="welcome-title">
              Good evening, Kshitish <span>✦</span>
            </h1>

            <p className="subtitle">
              Your personalized reading intelligence
            </p>

            <div className="stat-grid">
              <StatCard
                value="12"
                label="Articles read"
                detail="↗ 18% this week"
              />

              <StatCard
                value={String(bookmarkedTitles.length)}
                label="Bookmarks"
                detail={`${bookmarkedTitles.length} saved in library`}
              />

              <StatCard
                value={String(uniqueTopicsCount)}
                label="Topics explored"
                detail="AI, Tech & Science"
              />
            </div>
          </section>

          <NewArticle onOpen={openArticle} />

          {/* Continue Reading */}
          <section className="reading-section" aria-labelledby="continue-title">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Picked for you</p>
                <h2 id="continue-title">Continue reading</h2>
              </div>

              <a
                href="#library"
                onClick={(e) => {
                  e.preventDefault();
                  setActiveFilter("All");
                  const elem = document.getElementById("library");
                  elem?.scrollIntoView({ behavior: "smooth" });
                }}
              >
                View library →
              </a>
            </div>

            <article className="continue-card">
              <div className="continue-art">
                <span>PS</span>
              </div>

              <div className="continue-copy">
                <p className="article-tag">PSYCHE GUIDES · THINKING</p>

                <h3>How to solve problems by thinking like a detective</h3>

                <p>
                  Learn how observation, curiosity, and a structured approach
                  can help you uncover better answers.
                </p>

                <div className="article-meta">
                  <span>◷ 8 min read</span>
                  <span>·</span>
                  <span>68% complete</span>
                </div>
              </div>

              <button
                className="primary-button"
                type="button"
                onClick={() => openArticle()}
              >
                Continue reading <span>→</span>
              </button>
            </article>
          </section>

          {/* Library */}
          <section
            className="library-section"
            id="library"
            aria-labelledby="library-title"
          >
            <div className="section-heading">
              <div>
                <p className="eyebrow">Your collection</p>
                <h2 id="library-title">Your library</h2>
              </div>

              <button
                className="text-button"
                type="button"
                onClick={() => {
                  setActiveFilter("All");
                  setSearchQuery("");
                }}
              >
                Reset filters
              </button>
            </div>

            {/* Filters */}
            <div className="filter-row" aria-label="Filter articles">
              {filters.map((filter) => (
                <button
                  key={filter}
                  type="button"
                  className={
                    activeFilter === filter ? "filter active" : "filter"
                  }
                  onClick={() => setActiveFilter(filter)}
                >
                  {filter}
                </button>
              ))}
            </div>

            {/* Articles Grid */}
            {filteredArticles.length > 0 ? (
              <div className="article-grid">
                {filteredArticles.map((article) => (
                  <ArticleCard
                    key={article.title}
                    article={article}
                    isBookmarked={bookmarkedTitles.includes(article.title)}
                    onToggleBookmark={() => toggleBookmark(article.title)}
                    onSelect={() => openArticle()}
                  />
                ))}
              </div>
            ) : (
              <div
                style={{
                  padding: "36px 20px",
                  textAlign: "center",
                  background: "#fff",
                  borderRadius: "11px",
                  border: "1px solid var(--line)",
                  color: "var(--muted)",
                }}
              >
                <p style={{ margin: 0, fontWeight: 600 }}>
                  No articles found for "{activeFilter}"
                  {searchQuery ? ` matching "${searchQuery}"` : ""}.
                </p>
                <button
                  type="button"
                  className="text-button"
                  style={{ marginTop: "12px" }}
                  onClick={() => {
                    setActiveFilter("All");
                    setSearchQuery("");
                  }}
                >
                  View all articles
                </button>
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}

export default MainLayout;
