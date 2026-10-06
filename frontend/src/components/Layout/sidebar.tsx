import React from "react";

const primaryLinks = [
  ["⌂", "Home", "all"],
  ["▤", "Library", "all"],
  ["♧", "Bookmarks", "Saved"],
  ["◷", "History", "all"],
];

const aiLinks = [
  ["✦", "Summarize", "new-article"],
  ["◌", "Ask AI", "ask-ai"],
  ["□", "Quiz", "all"],
];

export type SidebarProps = {
  activeFilter?: string;
  onSelectFilter?: (filter: string) => void;
  onSelectAction?: (action: string) => void;
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
};

const Sidebar: React.FC<SidebarProps> = ({
  activeFilter = "All",
  onSelectFilter,
  onSelectAction,
  isMobileOpen = false,
  onCloseMobile,
}) => {
  const handleClick = (filterOrAction: string) => {
    if (filterOrAction === "Saved" || filterOrAction === "all") {
      onSelectFilter?.(filterOrAction === "all" ? "All" : filterOrAction);
    } else {
      onSelectAction?.(filterOrAction);
    }
    onCloseMobile?.();
  };

  return (
    <aside className={`sidebar ${isMobileOpen ? "mobile-open" : ""}`}>
      <nav aria-label="Primary navigation">
        <ul className="nav-list">
          {primaryLinks.map(([icon, label, target]) => {
            const isActive =
              (label === "Home" && activeFilter === "All") ||
              (label === "Bookmarks" && activeFilter === "Saved");
            return (
              <li key={label}>
                <a
                  className={isActive ? "active" : ""}
                  href={`#${label.toLowerCase()}`}
                  onClick={(e) => {
                    e.preventDefault();
                    handleClick(target);
                  }}
                >
                  <span>{icon}</span>
                  {label}
                </a>
              </li>
            );
          })}
        </ul>
        <p className="nav-label">AI tools</p>
        <ul className="nav-list">
          {aiLinks.map(([icon, label, target]) => (
            <li key={label}>
              <a
                href={`#${label.toLowerCase().replace(" ", "-")}`}
                onClick={(e) => {
                  e.preventDefault();
                  handleClick(target);
                }}
              >
                <span>{icon}</span>
                {label}
              </a>
            </li>
          ))}
        </ul>
      </nav>
      <a
        className="settings-link"
        href="#settings"
        onClick={(e) => {
          e.preventDefault();
          onSelectAction?.("settings");
          onCloseMobile?.();
        }}
      >
        <span>⚙</span> Settings
      </a>
    </aside>
  );
};

export default Sidebar;
