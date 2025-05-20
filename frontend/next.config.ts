import type { NextConfig } from "next";
import withPWA from "next-pwa";

const isDev = process.env.NODE_ENV === 'development';

const nextConfig: NextConfig = {
  reactStrictMode: true,
  swcMinify: true, // Enable SWC minification for improved performance

  compiler: {
    removeConsole: !isDev, // Remove console.log in production
  },

  pwa: {
    dest: 'public', // Destination directory for the service worker
    disable: isDev, // Disable PWA in development
    register: true, // Register the service worker
    skipWaiting: true, // Skip waiting for the service worker to be installed
  },
};

export default withPWA(nextConfig);
