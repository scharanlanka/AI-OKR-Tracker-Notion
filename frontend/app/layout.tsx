import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "OKR Tracker",
  description: "Goal and progress intelligence dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
