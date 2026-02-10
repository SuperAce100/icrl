import type { Metadata } from "next";
import { Archivo, Inter, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";

const archivo = Archivo({
  variable: "--font-archivo",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const siteTitle = "ICRL — In-Context Reinforcement Learning for LLM Agents";
const siteDescription =
  "ICRL is a trajectory-learning framework that lets LLM agents improve continuously at runtime — no retraining required. Store successful trajectories, retrieve them by goal and step observation, and curate stale entries over time.";
const siteUrl = "https://icrl.dev";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: siteTitle,
    template: "%s | ICRL",
  },
  description: siteDescription,
  keywords: [
    "ICRL",
    "in-context reinforcement learning",
    "LLM agents",
    "trajectory learning",
    "reinforcement learning",
    "AI agents",
    "agent memory",
    "retrieval augmented generation",
    "RAG",
    "continuous learning",
    "runtime learning",
    "LLM improvement",
    "agent framework",
    "Stanford AI research",
    "decision-making",
    "coding agents",
    "ICRLHF",
    "ReAct loop",
  ],
  authors: [{ name: "ICRL Team" }, { name: "Stanford Graphics Lab" }],
  creator: "ICRL Team",
  publisher: "Stanford Graphics Lab",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: siteUrl,
    siteName: "ICRL",
    title: siteTitle,
    description: siteDescription,
    images: [
      {
        url: "/opengraph-image.png",
        width: 1200,
        height: 630,
        alt: "ICRL — In-Context Reinforcement Learning for LLM Agents",
        type: "image/png",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: siteTitle,
    description: siteDescription,
    images: ["/twitter-image.png"],
  },
  alternates: {
    canonical: siteUrl,
  },
  icons: {
    icon: "/favicon.png",
    apple: "/favicon.png",
  },
  category: "technology",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${archivo.variable} ${inter.variable} ${geistMono.variable} font-sans antialiased`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
