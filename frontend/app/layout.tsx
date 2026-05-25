import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI OKR Tracker",
  description: "Mission control for objectives, key results, and AI assistance",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
