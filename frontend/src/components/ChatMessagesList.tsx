'use client';

import { useEffect, useRef, useState } from 'react';
import ChatMessage from './ChatMessage';
import { Message } from '@/types/chat';
import { IoIosArrowDown } from 'react-icons/io';


interface ChatMessagesListProps {
    messages: Message[];
    isTyping: boolean;
    onTypingComplete: () => void;
    isDarkMode: boolean;
}

export default function ChatMessagesList({ messages, isTyping, onTypingComplete, isDarkMode }: ChatMessagesListProps) {
    const bottomRef = useRef<HTMLDivElement>(null);
    const scrollContainerRef = useRef<HTMLDivElement>(null);
    const [showScrollButton, setShowScrollButton] = useState(false);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isTyping]);

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
    }, [messages, isTyping]);

    const scrollToBottom = () => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    return (
        <div className="relative h-full w-full">
            <div
                ref={scrollContainerRef}
                className={`flex flex-col gap-2 p-4 h-full overflow-y-auto scroll-smooth ${isDarkMode ? 'text-gray-200' : ''}`}
            >
                {messages.map((message, idx) => (
                    <ChatMessage
                        key={message.id}
                        message={message}
                        isTyping={message.role === 'assistant' && idx === messages.length - 1 && isTyping}
                        onTypingComplete={onTypingComplete}
                        isDarkMode={isDarkMode}
                    />
                ))}
                <div ref={bottomRef} />
            </div>
            {showScrollButton && (
                <button
                    title="Scroll to bottom"
                    onClick={scrollToBottom}
                    className={`fixed bottom-24 right-6 shadow-lg rounded-full p-2 z-50 border transition-colors duration-200 ${
                        isDarkMode 
                            ? 'bg-gray-800 border-gray-700 text-blue-400 hover:bg-gray-700' 
                            : 'bg-white/90 border-gray-200 text-[#2F70B3] hover:bg-blue-50'
                    }`}
                >
                    <IoIosArrowDown size={28} />
                </button>
            )}
        </div>
    );
}