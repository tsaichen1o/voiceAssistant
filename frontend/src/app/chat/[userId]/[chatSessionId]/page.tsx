'use client';

import { useParams } from 'next/navigation';
import ChatInterface from '@/components/ChatInterface';
import ChatSidebar from '@/components/ChatSidebar';
import { useState } from 'react';

export default function ChatPage() {
  const params = useParams();
  const chatSessionId = Array.isArray(params.chatSessionId) ? params.chatSessionId[0] : params.chatSessionId;
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  if (!chatSessionId) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p>Please select a chat to start.</p>
      </div>
    );
  }

  return (
    <div className="flex h-screen">
      <ChatSidebar 
        isOpen={isSidebarOpen} 
        onClose={() => setIsSidebarOpen(false)} 
        isDarkMode={false}
        currentChatId={chatSessionId} 
      />
      <main className="flex-1">
        <ChatInterface chatSessionId={chatSessionId} />
      </main>
    </div>
  );
}