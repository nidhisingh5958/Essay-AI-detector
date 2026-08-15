"use client";

import { useSyncExternalStore } from "react";

function subscribe(onChange: () => void) {
  const observer = new MutationObserver(onChange);
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
  return () => observer.disconnect();
}

function getSnapshot() {
  return document.documentElement.classList.contains("dark");
}

function getServerSnapshot() {
  return false;
}

/**
 * Reads/writes the .dark class set by the inline anti-FOUC script in
 * layout.tsx (see THEME_INIT_SCRIPT). useSyncExternalStore (rather than
 * effect + setState) keeps this consistent with the DOM as the source
 * of truth and avoids a hydration mismatch between the server's
 * always-light markup and the client's actual theme.
 */
export function ThemeToggle() {
  const isDark = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const toggle = () => {
    const next = !isDark;
    document.documentElement.classList.toggle("dark", next);
    window.localStorage.setItem("theme", next ? "dark" : "light");
  };

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
      title={isDark ? "Switch to light theme" : "Switch to dark theme"}
      className="flex size-9 items-center justify-center rounded-full border border-zinc-200 text-zinc-600 transition-colors hover:bg-zinc-100 hover:text-zinc-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent dark:border-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-50"
    >
      {isDark ? (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="size-[18px]" aria-hidden="true">
          <circle cx="12" cy="12" r="4.5" />
          <path
            strokeLinecap="round"
            d="M12 3v1.5M12 19.5V21M21 12h-1.5M4.5 12H3M18.36 5.64l-1.06 1.06M6.7 17.3l-1.06 1.06M18.36 18.36l-1.06-1.06M6.7 6.7 5.64 5.64"
          />
        </svg>
      ) : (
        <svg viewBox="0 0 24 24" fill="currentColor" className="size-[18px]" aria-hidden="true">
          <path d="M20.6 15.07A8.5 8.5 0 1 1 8.93 3.4a.75.75 0 0 1 .92.98A7 7 0 0 0 19.62 14.15a.75.75 0 0 1 .98.92Z" />
        </svg>
      )}
    </button>
  );
}
