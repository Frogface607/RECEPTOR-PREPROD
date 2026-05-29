import type { Metadata } from "next";
import { Geist, Geist_Mono, Cormorant_Garamond } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin", "cyrillic"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

// Display moments only — hero tagline, brand mark, editorial pull-quotes.
// Cormorant Garamond carries premium serif personality with strong italic;
// Cyrillic subset ships with the font (Vogue-grade aesthetic).
const cormorant = Cormorant_Garamond({
  variable: "--font-display",
  subsets: ["latin", "cyrillic"],
  weight: ["400", "500", "600", "700"],
  style: ["normal", "italic"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "RECEPTOR — чувствует кухню",
  description:
    "AI-копайлот владельца ресторана. Подключение к iiko, живая аналитика выручки, чат с цифрами в одно касание.",
  metadataBase: new URL("https://www.receptorai.pro"),
  openGraph: {
    title: "RECEPTOR — чувствует кухню",
    description:
      "AI-копайлот владельца ресторана. Подключение к iiko, живая аналитика выручки, чат с цифрами в одно касание.",
    url: "https://www.receptorai.pro",
    siteName: "RECEPTOR",
    locale: "ru_RU",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="ru"
      className={`dark ${geistSans.variable} ${geistMono.variable} ${cormorant.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-background text-foreground font-sans">
        {children}
      </body>
    </html>
  );
}
