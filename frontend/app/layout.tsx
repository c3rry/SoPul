import type { Metadata, Viewport } from "next";
import "./globals.css";

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#020617",
};

export const metadata: Metadata = {
  title: "Pulse2026 / SoPul — 2026 U.S. Midterms Election Forecast & Arbitrage Engine",
  description:
    "Zero-cost quantitative election forecasting engine synthesizing public polling, Kalshi prediction markets, and DeBERTa-v3 bounded social media residuals with 10,000-draw correlated Monte Carlo simulations.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 antialiased selection:bg-blue-600 selection:text-white">
        {children}
      </body>
    </html>
  );
}
