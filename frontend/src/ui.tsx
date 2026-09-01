import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import axios from "axios";
import {
  ArrowUpRight,
  Bell,
  BookOpenText,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Command,
  Gauge,
  Menu,
  Search as SearchIcon,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { health } from "./api";

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [backendStatus, setBackendStatus] = useState<"online" | "offline" | "endpoint-missing" | "invalid-request" | "failed" | "starting" | "unknown">("unknown");

  useEffect(() => {
    let isCurrent = true;

    async function checkBackend() {
      setBackendStatus("starting");
      try {
        await health();
        if (isCurrent) setBackendStatus("online");
      } catch (error) {
        if (!isCurrent) return;
        if (!axios.isAxiosError(error) || !error.response) {
          setBackendStatus("offline");
        } else if (error.response.status === 404) {
          setBackendStatus("endpoint-missing");
        } else if (error.response.status === 400) {
          setBackendStatus("invalid-request");
        } else {
          setBackendStatus("failed");
        }
      }
    }

    void checkBackend();
    return () => { isCurrent = false; };
  }, []);

  return (
    <div className={`app-shell ${collapsed ? "sidebar-collapsed" : ""}`}>
      <Sidebar
        collapsed={collapsed}
        mobileOpen={mobileOpen}
        onCollapse={() => setCollapsed((isCollapsed) => !isCollapsed)}
        onCloseMobile={() => setMobileOpen(false)}
      />
      <div className="app-content">
        <header className="navbar">
          <div className="navbar-left">
            <button className="mobile-menu" type="button" onClick={() => setMobileOpen(true)} aria-label="Open navigation">
              <Menu size={19} />
            </button>
            <div className="navbar-crumb">
              <span className="pulse-dot" />
              <span>MARKET IMPACT INTELLIGENCE</span>
            </div>
          </div>
          <div className="navbar-actions">
            <button className="top-search" type="button" onClick={() => document.getElementById("breach-search")?.focus()}>
              <SearchIcon size={15} />
              <span>Quick search</span>
              <kbd>CTRL K</kbd>
            </button>
            <button className="icon-button" type="button" aria-label="Notifications"><Bell size={17} /></button>
            <div className="backend-status" data-status={backendStatus} title={`Backend ${backendStatus.replace("-", " ")} `}>
              <span className="backend-status-dot" />
              <span>{backendStatus.replace("-", " ")}</span>
            </div>
            <div className="secure-badge"><ShieldCheck size={15} /><span>SECURE</span></div>
          </div>
        </header>
        {children}
      </div>
    </div>
  );
}

interface SidebarProps {
  collapsed: boolean;
  mobileOpen: boolean;
  onCollapse: () => void;
  onCloseMobile: () => void;
}

function Sidebar({ collapsed, mobileOpen, onCollapse, onCloseMobile }: SidebarProps) {
  const location = useLocation();
  const focusSearch = () => {
    onCloseMobile();
    window.setTimeout(() => document.getElementById("breach-search")?.focus(), 0);
  };
  const scoreTarget = location.pathname.startsWith("/company/") ? "#risk-score" : "/#top";

  return (
    <>
      <button className={`sidebar-backdrop ${mobileOpen ? "is-visible" : ""}`} type="button" aria-label="Close navigation" onClick={onCloseMobile} />
      <aside className={`sidebar ${collapsed ? "is-collapsed" : ""} ${mobileOpen ? "is-mobile-open" : ""}`}>
        <div className="sidebar-top">
          <Link to="/" className="brand" onClick={onCloseMobile}>
            <span className="brand-glyph"><ShieldAlert size={18} strokeWidth={2.3} /></span>
            <span className="brand-name">BREACH<span>ALPHA</span></span>
          </Link>
          <button className="collapse-button" type="button" onClick={onCollapse} aria-label="Toggle sidebar">
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>

        <div className="sidebar-label">WORKSPACE</div>
        <nav className="sidebar-nav" aria-label="Main navigation">
          <Link to="/#top" title={collapsed ? "Company Search" : undefined} onClick={focusSearch} className={`sidebar-link ${location.pathname === "/" ? "is-active" : ""}`}><SearchIcon size={18} strokeWidth={1.8} /><span>Company Search</span></Link>
          <Link to="/#top" title={collapsed ? "Recent Intelligence" : undefined} onClick={focusSearch} className="sidebar-link"><Clock3 size={18} strokeWidth={1.8} /><span>Recent Intelligence</span></Link>
        </nav>

        <div className="sidebar-bottom">
          <div className="sidebar-label">INTELLIGENCE</div>
          <Link className="sidebar-link" to="/#methodology" onClick={onCloseMobile}>
            <BookOpenText size={18} strokeWidth={1.8} />
            <span>Methodology</span>
          </Link>
          <Link className="sidebar-link" to={scoreTarget} onClick={scoreTarget === "/#top" ? focusSearch : onCloseMobile}>
            <Gauge size={18} strokeWidth={1.8} />
            <span>Risk Scoring</span>
          </Link>
        </div>
      </aside>
    </>
  );
}

interface SearchProps {
  onSearch: (query: string) => void;
  recentSearches: string[];
}

const popularSearches = ["Apple", "Uber", "Yahoo", "Target", "Equifax", "SolarWinds", "Capital One"];

export function Search({ onSearch, recentSearches }: SearchProps) {
  const [query, setQuery] = useState("");
  const [focused, setFocused] = useState(false);
  const filtered = popularSearches.filter((item) => item.toLowerCase().includes(query.toLowerCase()));
  const suggestions = query ? filtered : popularSearches;

  useEffect(() => {
    const handleShortcut = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        document.getElementById("breach-search")?.focus();
      }
    };
    window.addEventListener("keydown", handleShortcut);
    return () => window.removeEventListener("keydown", handleShortcut);
  }, []);

  const submit = (value: string) => {
    const cleanValue = value.trim();
    if (cleanValue) {
      setFocused(false);
      onSearch(cleanValue);
    }
  };

  return (
    <div className="search-experience">
      <form className={`hero-search ${focused ? "is-focused" : ""}`} onSubmit={(event) => { event.preventDefault(); submit(query); }}>
        <SearchIcon size={22} strokeWidth={1.8} />
        <input id="breach-search" value={query} onChange={(event) => setQuery(event.target.value)} onFocus={() => setFocused(true)} onBlur={() => window.setTimeout(() => setFocused(false), 180)} placeholder="Search historical breach intelligence..." autoComplete="off" aria-label="Search historical breach intelligence" />
        <button className="search-submit" type="submit" aria-label="Search intelligence"><span>Analyze</span><ArrowUpRight size={17} /></button>
        <kbd className="search-shortcut"><Command size={12} /> K</kbd>
      </form>

      {focused && (
        <div className="search-suggestions">
          <div className="suggestion-heading"><Sparkles size={14} /> {query ? "MATCHING INTELLIGENCE" : "POPULAR SEARCHES"}</div>
          {suggestions.length > 0 ? (
            <div className="suggestion-list">
              {suggestions.map((item) => (
                <button key={item} type="button" onMouseDown={() => submit(item)}>
                  <span className="suggestion-company">{item}</span>
                  <span className="suggestion-action">View intelligence <ArrowUpRight size={14} /></span>
                </button>
              ))}
            </div>
          ) : <p className="empty-suggestion">No saved intelligence matches. Try a company or ticker.</p>}
        </div>
      )}

      <div className="search-meta">
        <div><span>POPULAR</span>{popularSearches.map((item) => <button type="button" key={item} onClick={() => submit(item)}>{item}</button>)}</div>
        {recentSearches.length > 0 && <div className="recent-searches"><Clock3 size={14} /><span>RECENT</span>{recentSearches.map((item) => <button type="button" key={item} onClick={() => submit(item)}>{item}</button>)}</div>}
      </div>
    </div>
  );
}

export function Loader() {
  return (
    <main className="loader-screen" aria-label="Loading BreachAlpha">
      <div className="loader-grid" />
      <div className="loader-content">
        <div className="loader-mark" aria-hidden="true"><span /><span /><span /></div>
        <p className="eyebrow">BREACHALPHA / INTELLIGENCE NETWORK</p>
        <h1>Reading the signal.</h1>
        <div className="loader-progress" aria-hidden="true"><span /></div>
        <p className="loader-status">INITIALIZING MARKET IMPACT ENGINE</p>
      </div>
      <p className="loader-corner">SECURE RESEARCH ENVIRONMENT · v1.0</p>
    </main>
  );
}
