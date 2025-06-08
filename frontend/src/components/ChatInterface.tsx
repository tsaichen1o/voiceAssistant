'use client';

import { useState, useEffect } from 'react';
import ChatInput from './ChatInput';
import { GoSidebarExpand } from 'react-icons/go';
import { FaMoon, FaSun } from 'react-icons/fa';
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
  const [isDarkMode, setIsDarkMode] = useState(false);

  const { t } = useTranslation();
  const rawFAQS = t('faq', { returnObjects: true });
  const FAQS: string[] = Array.isArray(rawFAQS) ? rawFAQS : [];
  const faqTitle = t('faqTitle');

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

  const toggleDarkMode = () => {
    const newTheme = !isDarkMode;
    setIsDarkMode(newTheme);
    localStorage.setItem('theme', newTheme ? 'dark' : 'light');
  };

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
    <div className={`flex flex-col h-screen transition-colors duration-300 ${isDarkMode ? 'bg-gray-900' : 'bg-[#F6F6F6]'}`}>
      <div className={`fixed top-0 left-0 w-full z-30 transition-colors duration-300 ${isDarkMode ? 'bg-gray-800/90 backdrop-blur-md' : 'bg-white'} shadow-sm border-b ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`}>
        <div className="h-14 flex items-center px-4 sm:px-6 md:px-8 relative">
          <button
            className={`p-2 rounded-full absolute left-4 transition-colors duration-200 ${isDarkMode ? 'text-gray-200 hover:bg-gray-700' : 'text-gray-800 hover:bg-gray-100'}`}
            onClick={() => setIsSidebarOpen(true)}
            title="Toggle sidebar"
          >
            <GoSidebarExpand size={24} />
          </button>
          <p className={`text-sm font-medium w-full text-center ${isDarkMode ? 'text-gray-200' : 'text-gray-800'}`}>
            User: {userId} | Session: {sessionId}
          </p>
          <button
            onClick={toggleDarkMode}
            className={`p-2 rounded-full absolute right-4 transition-colors duration-200 ${isDarkMode ? 'text-yellow-400 hover:bg-gray-700' : 'text-gray-800 hover:bg-gray-100'}`}
            title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDarkMode ? <FaSun size={20} /> : <FaMoon size={20} />}
          </button>
        </div>
      </div>

      <ChatSidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} isDarkMode={isDarkMode} />

      <div className="flex-1 flex flex-col mt-14 px-0 sm:px-0 md:px-0">
        <div className="flex-1 overflow-y-auto max-h-[calc(100vh-188px)]">
          <div className="max-w-full mx-auto h-full flex flex-col md:pl-[14rem]">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full py-8">
                <div className={`mb-6 text-2xl font-bold tracking-wide ${isDarkMode ? 'text-blue-400' : 'text-[#2F70B3]'}`}>{faqTitle}</div>
                <div className="flex flex-col gap-4 w-[80%] max-w-md">
                  {FAQS && FAQS.map((q, idx) => (
                    <button
                      key={idx}
                      className={`
                        w-full flex items-center gap-3
                        px-5 py-3
                        rounded-xl
                        border
                        ${isDarkMode 
                          ? 'bg-gray-800 border-gray-700 text-gray-200 hover:bg-gray-700 hover:border-blue-500 hover:text-blue-400' 
                          : 'bg-white border-gray-200 text-gray-700 hover:bg-[#eaf3fb] hover:border-[#2F70B3] hover:text-[#2F70B3]'
                        }
                        shadow-sm
                        text-base font-medium
                        transition-colors duration-200
                        focus:outline-none focus:ring-2 focus:ring-[#2F70B3]/30
                        cursor-pointer
                      `}
                      onClick={() => handleSendMessage(q)}
                    >
                      <FaPersonCircleQuestion size={20} className={isDarkMode ? 'text-blue-400' : 'text-[#2F70B3]'}/>
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
              isDarkMode={isDarkMode}
            />
          </div>
        </div>
        <div className={`transition-colors duration-300 ${isDarkMode ? 'bg-gray-800 border-t border-gray-700' : 'bg-white border-t border-gray-200'}`}>
          <ChatInput onSend={handleSendMessage} isDarkMode={isDarkMode} />
        </div>
      </div>
    </div>
  );
}
