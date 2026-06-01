import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "PULSE",
  description: "OKR Intelligence for Qualified Health PBC",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
