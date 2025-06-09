'use client';

import { ChatMessage as ChatMessageType } from '@/types/chat';
import TypewriterText from './TypewriterText';
import ReactMarkdown from 'react-markdown';


interface ChatMessageProps {
    message: ChatMessageType;
    onStreamingComplete?: (finalMessage: ChatMessageType) => void;
    isDarkMode: boolean;
}

export default function ChatMessage({ message, onStreamingComplete, isDarkMode }: ChatMessageProps) {
    const isUser = message.role === 'user';

    const userBubbleClasses = `
        bg-[#2F70B3] text-white rounded-br-lg
        px-4 py-2 rounded-2xl shadow
    `;

    // When the SSE data stream is complete, a callback function can be triggered
    // NOTE: this step is optional, but it helps to update the parent's message state after the stream ends
    const handleComplete = (finalContent: string) => {
        if (onStreamingComplete) {
            const finalMessage = { ...message, content: finalContent, isStreaming: false };
            onStreamingComplete(finalMessage);
        }
    };

    // Build the classes for the assistant text
    const assistantTextClasses = `
        ${isDarkMode ? 'prose-invert text-gray-200' : 'prose text-gray-800'} max-w-none 
    `;

    return (
        <div className={`flex w-full my-1 ${isUser ? 'justify-end' : 'justify-start pl-6 pr-4 py-2'}`}>
            <div
                className={`
                    max-w-[80%]
                    text-base
                    break-words
                    break-all
                    whitespace-pre-wrap
                    ${isUser ? userBubbleClasses : assistantTextClasses}
                `}
            >
                {!isUser && message.isStreaming && message.streamUrl ? (
                    <TypewriterText 
                        streamUrl={message.streamUrl} 
                        onComplete={handleComplete}
                    />
                ) : (
                    <ReactMarkdown>
                        {message.content}
                    </ReactMarkdown>
                )}
            </div>
        </div>
    );
}
