'use client';

import { Message } from '@/types/chat';
import TypewriterText from './TypewriterText';


interface ChatMessageProps {
    message: Message;
    isTyping?: boolean;
    onTypingComplete?: () => void;
}

export default function ChatMessage({ message, isTyping, onTypingComplete }: ChatMessageProps) {
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
                    whitespace-pre-wrap
                    shadow
                    ${isUser
                        ? 'bg-[#2F70B3] text-white rounded-br-lg'
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
