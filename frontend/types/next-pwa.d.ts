declare module 'next-pwa' {
  import { NextConfig } from 'next';
  
  export function withPWA(config: NextConfig): NextConfig;
} 