import type { Metadata } from "next";
import "../styles/globals.css";
import { AuthProvider } from "@/context/AuthProvider";
import NextTopLoader from 'nextjs-toploader';


export const metadata: Metadata = {
  title: 'TUM Application Assistant',
  description: 'An accessible PWA to guide students applying to TUM using voice interaction.',
  manifest: '/manifest.json',
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
        className="bg-yellow-50"
        suppressHydrationWarning
      >
        <AuthProvider>
        <NextTopLoader
          color="linear-gradient(to right, rgb(56, 189, 248), rgb(251, 113, 133), rgb(163, 230, 53))"
          height={5}
          speed={300}
          easing="ease"
        />
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
