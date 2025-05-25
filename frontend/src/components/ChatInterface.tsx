'use client';

import { useState } from 'react';
import ChatInput from './ChatInput';
import { GoSidebarExpand } from 'react-icons/go';
import ChatSidebar from './ChatSidebar';
import ChatMessagesList from './ChatMessagesList';
import { Message } from '@/types/chat';
import { v4 as uuidv4 } from 'uuid';
import { useTranslation } from 'react-i18next';
import '../i18n';
import { FaPersonCircleQuestion } from "react-icons/fa6";


interface ChatInterfaceProps {
  userId: string;
  sessionId: string;
}

export default function ChatInterface({ userId, sessionId }: ChatInterfaceProps) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);

  const { t } = useTranslation();
  const rawFAQS = t('faq', { returnObjects: true });
  const FAQS: string[] = Array.isArray(rawFAQS) ? rawFAQS : [];
  const faqTitle = t('faqTitle');


  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;

    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content,
      timestamp: Date.now(),
    };
    setMessages(prev => [...prev, userMessage]);

    // TODO: Call API to get assistant response
    setIsTyping(true);

    setTimeout(() => {
      const assistantMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content,
        timestamp: Date.now(),
      };
      setMessages(prev => [...prev, assistantMessage]);
      // setIsTyping(false);
    }, 1000);
  };

  const handleTypingComplete = () => {
    setIsTyping(false);
  };

  return (
    <div className="flex flex-col h-screen bg-[#F6F6F6]">
      <div className="fixed top-0 left-0 w-full z-30 bg-white shadow-sm border-b">
        <div className="h-14 flex items-center px-4 sm:px-6 md:px-8 relative">
          <button
            className="p-2 text-gray-800 hover:bg-gray-100 rounded-full absolute left-4"
            onClick={() => setIsSidebarOpen(true)}
            title="Toggle sidebar"
          >
            <GoSidebarExpand size={24} />
          </button>
          <p className="text-sm font-medium text-gray-800 w-full text-center">
            User: {userId} | Session: {sessionId}
          </p>
        </div>
      </div>

      <ChatSidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />

      <div className="flex-1 flex flex-col mt-14 px-0 sm:px-0 md:px-0">
        <div className="flex-1 overflow-y-auto max-h-[calc(100vh-188px)]">
          <div className="max-w-full mx-auto h-full flex flex-col md:pl-[14rem]">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full py-8">
                <div className="mb-6 text-2xl font-bold text-[#2F70B3] tracking-wide">{faqTitle}</div>
                <div className="flex flex-col gap-4 w-[80%] max-w-md">
                  {FAQS && FAQS.map((q, idx) => (
                    <button
                      key={idx}
                      className="
                        w-full flex items-center gap-3
                        px-5 py-3
                        rounded-xl
                        border border-gray-200
                        bg-white
                        shadow-sm
                        text-base font-medium text-gray-700
                        hover:bg-[#eaf3fb] hover:border-[#2F70B3] hover:text-[#2F70B3]
                        transition
                        focus:outline-none focus:ring-2 focus:ring-[#2F70B3]/30
                      "
                      onClick={() => handleSendMessage(q)}
                    >
                      <FaPersonCircleQuestion size={20} className="text-[#2F70B3]"/>
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
            <ChatMessagesList
              messages={messages}
              isTyping={isTyping}
              onTypingComplete={handleTypingComplete}
            />
          </div>
        </div>
        <ChatInput onSend={handleSendMessage} />
      </div>
    </div>
  );
}
