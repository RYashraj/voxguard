import type { Metadata } from "next";
import "@fontsource/ibm-plex-sans/400.css";
import "@fontsource/ibm-plex-sans/500.css";
import "@fontsource/ibm-plex-sans/600.css";
import "@fontsource/ibm-plex-sans/700.css";
import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-mono/500.css";
import "@fontsource/ibm-plex-mono/600.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "VoxGuard — Call risk monitor",
  description: "Live voice-impersonation risk monitoring for active calls.",
};

// Runs before paint to avoid a light-mode flash for users who already
// chose dark mode. Reads the same key ThemeToggle writes to.
const noFlashScript = `
(function () {
  try {
    var stored = window.localStorage.getItem("voxguard-theme");
    var isDark = stored === "dark" || (!stored && window.matchMedia("(prefers-color-scheme: dark)").matches);
    if (isDark) document.documentElement.classList.add("dark");
  } catch (e) {}
})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <script dangerouslySetInnerHTML={{ __html: noFlashScript }} />
        {children}
      </body>
    </html>
  );
}
