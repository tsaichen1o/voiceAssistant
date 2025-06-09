'use client';

import { ChatMessage as ChatMessageType } from '@/types/chat';
import TypewriterText from './TypewriterText';


interface ChatMessageProps {
    message: ChatMessageType;
    isTyping?: boolean;
    onTypingComplete?: () => void;
    isDarkMode: boolean;
}

export default function ChatMessage({ message, isTyping, onTypingComplete, isDarkMode }: ChatMessageProps) {
    const isUser = message.role === 'user';

    return (
        <div className={`flex w-full my-1 ${isUser ? 'justify-end' : 'justify-start'}`}>
            <div
                className={`
                    max-w-[80%]
                    px-4 py-2
                    rounded-2xl
                    text-base
                    break-words
                    break-all
                    whitespace-pre-wrap
                    shadow
                    ${isUser
                        ? 'bg-[#2F70B3] text-white rounded-br-lg'
                        : isDarkMode
                            ? 'bg-gray-800 text-gray-200 rounded-bl-lg'
                            : 'bg-white text-gray-900 rounded-bl-lg'
                    }`
                }
            >
                {!isUser && isTyping ? (
                    <TypewriterText text={message.content} onComplete={onTypingComplete} />
                ) : (
                    message.content
                )}
            </div>
        </div>
    );
}
