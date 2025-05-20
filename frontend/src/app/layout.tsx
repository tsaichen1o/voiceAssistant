import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: 'TUM Application Assistant',
  description: 'An accessible PWA to guide students applying to TUM using voice interaction.',
  manifest: '/manifest.json',
  themeColor: '#0066cc',
  icons: {
    icon: '/icons/favicon.ico',
    shortcut: '/icons/apple-touch-icon.png',
    apple: '/icons/apple-touch-icon.png',
  },
  // Generate @ https://realfavicongenerator.net/
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
