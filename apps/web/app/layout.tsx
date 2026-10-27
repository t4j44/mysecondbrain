import type { Metadata, Viewport } from 'next';
import { JetBrains_Mono, Outfit } from 'next/font/google';
import './globals.css';
import { ThemeProvider } from '@/providers/theme-provider';
import { Toaster } from '@/components/ui/toaster';

const outfit = Outfit({ 
  subsets: ['latin'], 
  variable: '--font-outfit',
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({ 
  subsets: ['latin'], 
  variable: '--font-jetbrains-mono',
  display: 'swap',
  preload: false,
});

export const metadata: Metadata = {
  applicationName: "Taj's Second Brain",
  manifest: '/manifest.webmanifest',
  title: {
    template: '%s | Taj’s Second Brain',
    default: 'Second Brain — Your saved context',
  },
  description: 'Save useful context about people and work, then recall it with supporting sources.',
  keywords: ['Second Brain', 'AI OS', 'Founder Terminal', 'Multi-Venture', 'Productivity'],
  authors: [{ name: 'Taj', url: 'https://tajssecondbrain.ai' }],
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'Second Brain',
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  themeColor: '#12081d',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning className={`${outfit.variable} ${jetbrainsMono.variable}`}>
      <body className="min-h-screen bg-background font-sans text-foreground antialiased selection:bg-[#00ff9d] selection:text-[#0a0510]">
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem disableTransitionOnChange>
            {children}
            <Toaster />
        </ThemeProvider>
      </body>
    </html>
  );
}
