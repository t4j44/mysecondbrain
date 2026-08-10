import React from 'react';
import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: "Taj's Second Brain — Founder OS",
  description: "Private command center and cognitive amplifier for startup execution.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,100..800;1,100..800&family=Outfit:wght@100..900&display=swap" rel="stylesheet" />
      </head>
      <body className="min-h-screen bg-terminal-bg text-terminal-fg font-sans antialiased selection:bg-terminal-accent selection:text-terminal-panel">
        <div className="scanline" />
        {children}
      </body>
    </html>
  );
}
