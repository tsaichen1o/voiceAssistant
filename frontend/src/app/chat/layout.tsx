'use client';

import { useState, useEffect } from 'react';
import ChatSidebar from '@/components/ChatSidebar';
import { useParams } from 'next/navigation';

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [currentChatId, setCurrentChatId] = useState<string>('');
  const params = useParams();

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      setIsDarkMode(savedTheme === 'dark');
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setIsDarkMode(prefersDark);
      localStorage.setItem('theme', prefersDark ? 'dark' : 'light');
    }
  }, []);

  useEffect(() => {
    if (params?.sessionId) {
      setCurrentChatId(params.sessionId as string);
    }
  }, [params]);

  return (
    <div className="flex">
      <ChatSidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} isDarkMode={isDarkMode} currentChatId={currentChatId} />
      <div className="flex-1 min-h-screen">{children}</div>
    </div>
  );
}