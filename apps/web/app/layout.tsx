import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  applicationName: "MoonWitness",
  title: {
    default: "MoonWitness",
    template: "%s · MoonWitness",
  },
  description:
    "A focused operational platform for knowledge, records, and connected work.",
  icons: {
    icon: "/icon.svg",
    shortcut: "/icon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
