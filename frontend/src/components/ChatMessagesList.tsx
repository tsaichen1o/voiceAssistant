'use client';

import { useEffect, useRef, useState } from 'react';
import ChatMessage from './ChatMessage';
import { ChatMessage as ChatMessageType } from '@/types/chat';
import { IoIosArrowDown } from 'react-icons/io';
import { ThinkingIndicator } from './ThinkingIndicator';


interface ChatMessagesListProps {
    messages: ChatMessageType[];
    onStreamingComplete: (finalMessage: ChatMessageType) => void;
    onEmailSuggestion: (suggestion: { message: string }) => void;
    isDarkMode: boolean;
    isSidebarOpen?: boolean;
}

export default function ChatMessagesList({ messages, onStreamingComplete, onEmailSuggestion, isDarkMode, isSidebarOpen = false }: ChatMessagesListProps) {
    const bottomRef = useRef<HTMLDivElement>(null);
    const scrollContainerRef = useRef<HTMLDivElement>(null);
    const [showScrollButton, setShowScrollButton] = useState(false);

    const lastMessage = messages[messages.length - 1];
    const showThinkingIndicator =
        lastMessage &&
        lastMessage.role === 'assistant' &&
        lastMessage.isStreaming === true &&
        lastMessage.content === '';

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    useEffect(() => {
        const container = scrollContainerRef.current;
        if (!container) return;

        const handleScroll = () => {
            const isAtBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 40;
            setShowScrollButton(!isAtBottom);
        };

        container.addEventListener('scroll', handleScroll);
        handleScroll();

        return () => {
            container.removeEventListener('scroll', handleScroll);
        };
    }, [messages]);

    const scrollToBottom = () => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    return (
        <div className="relative h-full w-full">
            <div
                ref={scrollContainerRef}
                className={`flex flex-col gap-2 p-4 h-full overflow-y-auto scroll-smooth ${isDarkMode ? 'text-gray-200' : ''}`}
            >
                {messages.map((message) => (
                    <ChatMessage
                        key={message.id}
                        message={message}
                        onStreamingComplete={onStreamingComplete}
                        onEmailSuggestion={onEmailSuggestion}
                        isDarkMode={isDarkMode}
                    />
                ))}
                {showThinkingIndicator && (
                    <ThinkingIndicator isDarkMode={isDarkMode} />
                )}
                <div ref={bottomRef} />
            </div>
            {showScrollButton && (
                <button
                    title="Scroll to bottom"
                    onClick={scrollToBottom}
                    className={`fixed bottom-24 left-1/2 -translate-x-1/2 md:ml-14 shadow-lg rounded-full p-2 z-50 border transition-colors duration-200 cursor-pointer ${isDarkMode
                            ? 'bg-gray-800 border-gray-700 text-blue-400 hover:bg-gray-700'
                            : 'bg-white/90 border-gray-200 text-[#2F70B3] hover:bg-blue-50'
                        } ${isSidebarOpen ? 'sm:block hidden' : 'block'}`}
                >
                    <IoIosArrowDown size={28} />
                </button>
            )}
        </div>
    );
}