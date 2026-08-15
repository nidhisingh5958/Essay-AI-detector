import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

import { ThemeToggle } from "@/components/ThemeToggle/ThemeToggle";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AI Detector for Admissions Essays",
  description:
    "Evidence-based, explainable analysis of admissions essay writing characteristics.",
};

// Applies the persisted/system theme before first paint so switching
// to class-based dark mode (see globals.css) never causes a flash of
// the wrong theme.
const THEME_INIT_SCRIPT = `
(function () {
  try {
    var stored = localStorage.getItem("theme");
    var dark = stored ? stored === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    document.documentElement.classList.toggle("dark", dark);
  } catch (e) {}
})();
`;

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <header className="sticky top-0 z-10 border-b border-zinc-200 bg-white/80 backdrop-blur-sm dark:border-zinc-800 dark:bg-zinc-950/80">
          <div className="mx-auto flex w-full max-w-3xl items-center justify-between px-6 py-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-zinc-900 dark:text-zinc-50">
              <span className="flex size-7 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="size-4" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                </svg>
              </span>
              <span>Essay Detector</span>
            </div>
            <ThemeToggle />
          </div>
        </header>

        <div className="flex flex-1 flex-col">{children}</div>

        <footer className="border-t border-zinc-200 py-6 dark:border-zinc-800">
          <div className="mx-auto w-full max-w-3xl px-6 text-center text-xs text-zinc-500 dark:text-zinc-500">
            Reports statistical writing patterns, not proof of authorship.
          </div>
        </footer>
      </body>
    </html>
  );
}
