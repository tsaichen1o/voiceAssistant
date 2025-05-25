'use client';

import { useEffect, useRef, useState } from 'react';
import ChatMessage from './ChatMessage';
import { Message } from '@/types/chat';
import { IoIosArrowDown } from 'react-icons/io';


interface ChatMessagesListProps {
    messages: Message[];
    isTyping: boolean;
    onTypingComplete: () => void;
}

export default function ChatMessagesList({ messages, isTyping, onTypingComplete }: ChatMessagesListProps) {
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
                className="flex flex-col gap-2 p-4 h-full overflow-y-auto scroll-smooth"
            >
                {messages.map((message, idx) => (
                    <ChatMessage
                        key={message.id}
                        message={message}
                        isTyping={message.role === 'assistant' && idx === messages.length - 1 && isTyping}
                        onTypingComplete={onTypingComplete}
                    />
                ))}
                <div ref={bottomRef} />
            </div>
            {showScrollButton && (
                <button
                    title="Scroll to bottom"
                    onClick={scrollToBottom}
                    className="fixed bottom-24 right-6 bg-white/90 shadow-lg rounded-full p-2 z-50 border border-gray-200 hover:bg-blue-50 transition"
                >
                    <IoIosArrowDown className="text-[#2F70B3]" size={28} />
                </button>
            )}
        </div>
    );
}