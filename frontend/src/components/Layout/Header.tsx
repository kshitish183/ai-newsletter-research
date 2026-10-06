import React from "react";

type IconName = "search" | "bell" | "chevron" | "menu" | "close";

const Icon = ({ name }: { name: IconName }) => {
  const paths = {
    search: (
      <>
        <circle cx="11" cy="11" r="6" />
        <path d="m16 16 4 4" />
      </>
    ),
    bell: (
      <>
        <path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
        <path d="M10 21h4" />
      </>
    ),
    chevron: <path d="m9 18 6-6-6-6" />,
    menu: (
      <>
        <line x1="4" y1="6" x2="20" y2="6" />
        <line x1="4" y1="12" x2="20" y2="12" />
        <line x1="4" y1="18" x2="20" y2="18" />
      </>
    ),
    close: (
      <>
        <line x1="18" y1="6" x2="6" y2="18" />
        <line x1="6" y1="6" x2="18" y2="18" />
      </>
    ),
  };
  return (
    <svg
      aria-hidden="true"
      className="icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
    >
      {paths[name]}
    </svg>
  );
};

export type HeaderProps = {
  searchQuery?: string;
  onSearchChange?: (query: string) => void;
  onToggleMobileMenu?: () => void;
  isMobileMenuOpen?: boolean;
};

const Header: React.FC<HeaderProps> = ({
  searchQuery = "",
  onSearchChange,
  onToggleMobileMenu,
  isMobileMenuOpen = false,
}) => (
  <header className="topbar">
    <button
      className="mobile-menu-btn"
      type="button"
      onClick={onToggleMobileMenu}
      aria-label={isMobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
    >
      <Icon name={isMobileMenuOpen ? "close" : "menu"} />
    </button>
    <a className="brand" href="#dashboard" aria-label="InsightAI dashboard">
      <span className="brand-mark">✦</span>InsightAI
    </a>
    <label className="search-box">
      <Icon name="search" />
      <span className="sr-only">Search articles</span>
      <input
        type="search"
        placeholder="Search articles..."
        value={searchQuery}
        onChange={(e) => onSearchChange?.(e.target.value)}
      />
      <kbd>⌘ K</kbd>
    </label>
    <div className="topbar-actions">
      <button className="icon-button" type="button" aria-label="Notifications">
        <Icon name="bell" />
      </button>
      <button className="profile-button" type="button">
        <span className="avatar">K</span>
        <span className="profile-copy">
          <strong>Kshitish</strong>
          <small>Reader</small>
        </span>
        <Icon name="chevron" />
      </button>
    </div>
  </header>
);

export default Header;
