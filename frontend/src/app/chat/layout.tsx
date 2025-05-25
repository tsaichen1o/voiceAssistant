'use client';

import { useState } from 'react';
import ChatSidebar from '@/components/ChatSidebar';


export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  return (
    <div className="flex">
      <ChatSidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
      <div className="flex-1 min-h-screen">{children}</div>
    </div>
  );
}