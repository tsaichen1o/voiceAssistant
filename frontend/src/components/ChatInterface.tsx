'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import ChatInput from './ChatInput';
import { GoSidebarExpand } from 'react-icons/go';
import { FaMoon, FaSun } from 'react-icons/fa';
import ChatSidebar from './ChatSidebar';
import ChatMessagesList from './ChatMessagesList';
import { ChatMessage } from '@/types/chat';
import { v4 as uuidv4 } from 'uuid';
import { useTranslation } from 'react-i18next';
import '../i18n';
import { FaPersonCircleQuestion, FaXmark } from "react-icons/fa6";
import { sendMessage, getChatSessionHistory, saveChatHistory, createChatSession } from '@/services/api';
import { useAuth } from '@/context/AuthProvider';


interface ChatInterfaceProps {
  chatSessionId: string;
}

export default function ChatInterface({ chatSessionId }: ChatInterfaceProps) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [showFAQModal, setShowFAQModal] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [isThinking, setIsThinking] = useState(false);
  const [dotCount, setDotCount] = useState(0);
  
  const { user } = useAuth();
  const { t } = useTranslation();
  const rawFAQS = t('faq', { returnObjects: true });
  const FAQS: string[] = Array.isArray(rawFAQS) ? rawFAQS : [];
  const faqTitle = t('faqTitle');
  const router = useRouter();

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

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (isThinking) {
      interval = setInterval(() => {
        setDotCount((prev) => (prev + 1) % 4);
      }, 400);
    } else {
      setDotCount(0);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isThinking]);

  useEffect(() => {
    if (messages.length > 0) {
      const lastMsg = messages[messages.length - 1];
      if (lastMsg.role === 'assistant' && !lastMsg.isStreaming) {
        setIsThinking(false);
      }
    }
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;
    setIsThinking(true);

    let currentChatId = chatSessionId;
    let messagesWithUserUpdate = [...messages];

    const userMessage: ChatMessage = {
      id: uuidv4(),
      session_id: currentChatId,
      chat_id: currentChatId,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };

    const isNewChat = chatSessionId === 'new';

    if (isNewChat) {
      try {
        const newSession = await createChatSession();
        if (!newSession.session_id) {
          throw new Error("Failed to create a new session from backend.");
        }
        currentChatId = newSession.session_id;

        router.replace(`/chat/${user?.id}/${currentChatId}`);

        userMessage.session_id = currentChatId;
        userMessage.chat_id = currentChatId;
        
        messagesWithUserUpdate = [userMessage];
        setMessages(messagesWithUserUpdate);

        await saveChatHistory(messagesWithUserUpdate, currentChatId);

      } catch (error) {
        console.error("Failed to initialize a new chat session:", error);
        const errorMessage: ChatMessage = {
          id: uuidv4(),
          session_id: currentChatId,
          chat_id: currentChatId,
          role: 'assistant',
          content: "Sorry, I encountered an error while creating a new chat session. Please try again.",
          created_at: new Date().toISOString(),
        };
        setMessages([errorMessage]);
        return;
      }
    } else {
      userMessage.session_id = currentChatId;
      userMessage.chat_id = currentChatId;
      
      messagesWithUserUpdate = [...messages, userMessage];
      setMessages(messagesWithUserUpdate);
    }

    try {
      // const streamInitResponse = await sendMessage(
      //   messagesWithUserUpdate,
      //   currentChatId
      // );
      const streamInitResponse = await sendMessage([userMessage], currentChatId);
      const streamId = streamInitResponse.stream_id;
      console.log("SSE stream_id:", streamId);

      if (!streamId) {
        throw new Error("Backend did not return a stream_id");
      }

      const assistantMessage: ChatMessage = {
        id: uuidv4(),
        session_id: currentChatId,
        chat_id: currentChatId,
        role: 'assistant',
        content: '',
        created_at: new Date().toISOString(),
        isStreaming: true,
        streamUrl: `${process.env.NEXT_PUBLIC_API_URL}/api/chat/stream/${streamId}`
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: ChatMessage = {
        id: uuidv4(),
        session_id: currentChatId,
        chat_id: currentChatId,
        role: 'assistant',
        content: "Sorry, I encountered an error. Please try again.",
        created_at: new Date().toISOString(),
        isStreaming: false,
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  useEffect(() => {
    const loadSessionHistory = async () => {
      if (chatSessionId === 'new') {
        setMessages([]);
        setIsLoadingHistory(false);
        return;
      }

      if (!chatSessionId) {
        setIsLoadingHistory(false);
        return;
      }

      setIsLoadingHistory(true);

      try {
        const history = await getChatSessionHistory(chatSessionId);

        setMessages(history.messages || []);
      } catch (error) {
        console.error('Failed to load session history:', error);
        setMessages([]);
      } finally {
        setIsLoadingHistory(false);
      }
    };

    loadSessionHistory();
  }, [chatSessionId]);


  const handleStreamingComplete = useCallback(async (completedMessage: ChatMessage) => {
    setMessages(prevMessages => {
      const finalMessages = prevMessages.map(msg =>
        msg.id === completedMessage.id ? completedMessage : msg
      );

      saveChatHistory(finalMessages, chatSessionId)
        .then(() => {
          console.log("Session history saved successfully.");
        })
        .catch(error => {
          console.error("Failed to save session history:", error);
        });

      return finalMessages;
    });
  }, [chatSessionId]);

  return (
    <div className={`flex flex-col h-screen transition-colors duration-300 ${isDarkMode ? 'bg-gray-900' : 'bg-[#F6F6F6]'}`}>
      <div className={`fixed top-0 left-0 w-full z-30 transition-colors duration-300 ${isDarkMode ? 'bg-gray-800/90 backdrop-blur-md' : 'bg-white'} shadow-sm border-b ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`}>
        <div className="h-14 flex items-center px-4 sm:px-6 md:px-8 relative">
          <button
            className={`p-2 rounded-full absolute left-4 transition-colors duration-200 cursor-pointer ${isDarkMode ? 'text-gray-200 hover:bg-gray-700' : 'text-gray-800 hover:bg-gray-100'}`}
            onClick={() => setIsSidebarOpen(true)}
            title="Toggle sidebar"
          >
            <GoSidebarExpand size={24} />
          </button>
          <div className={`
            text-lg font-bold cursor-pointer
            transition-all duration-300 hover:scale-105
            ${isDarkMode ? 'text-[#3775B6] hover:text-[#4a8ac9]' : 'text-[#3775B6] hover:text-[#4a8ac9]'}
            w-full text-center
            md:w-auto md:text-left md:ml-[14.5rem]
          `}>
            go42TUM
          </div>
          <button
            onClick={toggleDarkMode}
            className={`p-2 rounded-full absolute right-4 transition-colors duration-200 cursor-pointer ${isDarkMode ? 'text-yellow-400 hover:bg-gray-700' : 'text-gray-800 hover:bg-gray-100'}`}
            title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDarkMode ? <FaSun size={20} /> : <FaMoon size={20} />}
          </button>
        </div>
      </div>

      <ChatSidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} isDarkMode={isDarkMode} currentChatId={chatSessionId} />

      <div className="flex-1 flex flex-col mt-14 px-0 sm:px-0 md:px-0">
        <div className="flex-1 overflow-y-auto max-h-[calc(100vh-188px)]">
          <div className="max-w-full mx-auto h-full flex flex-col md:pl-[14rem]">

            {isLoadingHistory ? (
              <div className="flex-1 flex items-center justify-center">
                {/* TODO: add loading spinner */}
                {/* <LoadingSpinner /> */}
              </div>
            ) : messages.length === 0 ? (
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
                      <FaPersonCircleQuestion size={20} className={isDarkMode ? 'text-blue-400' : 'text-[#2F70B3]'} />
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                <ChatMessagesList
                  messages={messages}
                  onStreamingComplete={handleStreamingComplete}
                  isDarkMode={isDarkMode}
                />
                {isThinking && (
                  <div className="flex items-center justify-center py-2">
                    <span className={`text-base font-medium ${isDarkMode ? 'text-blue-300' : 'text-[#2F70B3]'}`}>
                      Thinking{'.'.repeat(dotCount)}
                    </span>
                  </div>
                )}
                <button
                  onClick={() => setShowFAQModal(true)}
                  className={`
                    fixed bottom-24 right-6
                    p-2 rounded-full
                    shadow-lg
                    border
                    transition-all duration-200
                    ${isDarkMode
                            ? 'bg-gray-800 border-gray-700 text-blue-400 hover:bg-gray-700'
                            : 'bg-white/90 border-gray-200 text-[#2F70B3] hover:bg-blue-50'
                          }
                    z-50
                    cursor-pointer
                  `}
                  title="FAQ"
                >
                  <FaPersonCircleQuestion size={28} />
                </button>
              </>
            )}
          </div>
        </div>
        <div className={`transition-colors duration-300 ${isDarkMode ? 'bg-gray-800' : 'bg-white'}`}>
          <ChatInput
            onSend={handleSendMessage}
            isDarkMode={isDarkMode}
          />
        </div>
      </div>

      {showFAQModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className={`
            bg-white rounded-xl p-6 max-w-md w-[90%] max-h-[80vh] overflow-y-auto
            ${isDarkMode ? 'bg-gray-800 text-gray-200' : 'bg-white text-gray-800'}
          `}>
            <div className="flex justify-between items-center mb-4">
              <h2 className={`text-xl font-bold ${isDarkMode ? 'text-blue-400' : 'text-[#2F70B3]'}`}>{faqTitle}</h2>
              <button
                onClick={() => setShowFAQModal(false)}
                className={`p-2 rounded-full cursor-pointer ${isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}
                title="Close FAQ"
              >
                <FaXmark size={20} />
              </button>
            </div>
            <div className="flex flex-col gap-3">
              {FAQS && FAQS.map((q, idx) => (
                <button
                  key={idx}
                  className={`
                    w-full flex items-center gap-3
                    px-4 py-3
                    rounded-lg
                    border
                    ${isDarkMode
                      ? 'bg-gray-700 border-gray-600 text-gray-200 hover:bg-gray-600 hover:border-blue-500 hover:text-blue-400'
                      : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-[#eaf3fb] hover:border-[#2F70B3] hover:text-[#2F70B3]'
                    }
                    text-sm font-medium
                    transition-colors duration-200
                    focus:outline-none focus:ring-2 focus:ring-[#2F70B3]/30
                    cursor-pointer
                  `}
                  onClick={() => {
                    handleSendMessage(q);
                    setShowFAQModal(false);
                  }}
                >
                  <FaPersonCircleQuestion size={18} className={isDarkMode ? 'text-blue-400' : 'text-[#2F70B3]'} />
                  {q}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
