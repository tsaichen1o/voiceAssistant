'use client';

import { ChatMessage as ChatMessageType } from '@/types/chat';
import TypewriterText from './TypewriterText';


interface ChatMessageProps {
    message: ChatMessageType;
    onStreamingComplete?: (finalMessage: ChatMessageType) => void;
    isDarkMode: boolean;
}

export default function ChatMessage({ message, onStreamingComplete, isDarkMode }: ChatMessageProps) {
    const isUser = message.role === 'user';

    // When the SSE data stream is complete, a callback function can be triggered
    // NOTE: this step is optional, but it helps to update the parent's message state after the stream ends
    const handleComplete = (finalContent: string) => {
        if (onStreamingComplete) {
            const finalMessage = { ...message, content: finalContent, isStreaming: false };
            onStreamingComplete(finalMessage);
        }
    };

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
                {!isUser && message.isStreaming && message.streamUrl ? (
                    <TypewriterText 
                        streamUrl={message.streamUrl} 
                        onComplete={handleComplete}
                    />
                ) : (
                    message.content
                )}
            </div>
        </div>
    );
}
