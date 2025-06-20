'use client';

import { useState, useRef, useEffect } from 'react';
import {
  RiChatVoiceAiFill,
  RiSendPlane2Fill,
  RiAddLargeFill,
  RiCloseFill,
} from 'react-icons/ri';
import VoiceAssistantOverlay from './VoiceAssistantOverlay';


interface ChatInputProps {
  onSend: (content: string) => void;
  isDarkMode: boolean;
  userId?: string;
}

export default function ChatInput({ onSend, isDarkMode, userId }: ChatInputProps) {
  const [input, setInput] = useState('');
  const [preview, setPreview] = useState<string[]>([]);
  const [voiceOpen, setVoiceOpen] = useState(false);
  const [isSending, setIsSending] = useState(false);
  // Use provided userId or generate a fallback
  const voiceUserId = userId || `guest-${Math.random().toString().substring(10)}`;

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const hasText = input.trim().length > 0;

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    if (files.length === 0) return;
    files.forEach((file) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview((prev) => [...prev, reader.result as string]);
      };
      reader.readAsDataURL(file);
    });

    e.target.value = '';
  };

  const handleRemovePreview = (idx: number) => {
    setPreview((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleSubmit = async () => {
    if (!input.trim() || isSending) return;

    setIsSending(true);
    try {
      onSend(input);
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    } catch (error) {
      console.error('An error occurred in handleSubmit:', error);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // When e.nativeEvent.isComposing is true, 
    // it means the user is composing a character (Chinese input method selection)
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {

      e.preventDefault();
      e.stopPropagation();
      handleSubmit();
    }
  };

  return (
    <>
      <VoiceAssistantOverlay 
        userId={voiceUserId} 
        isOpen={voiceOpen} 
        onClose={() => setVoiceOpen(false)} 
      />
      <div className={`fixed bottom-0 left-0 w-full z-10 px-4 pb-4 ${isDarkMode ? 'bg-gradient-to-t from-gray-900 via-gray-900/90 to-transparent' : 'bg-gradient-to-t from-white via-white/90 to-transparent'} md:ml-56`}>
        <div className={`sm:w-full md:w-[calc(100%-14rem)] rounded-3xl shadow-md border px-4 pt-4 pb-3 flex flex-col gap-3 max-h-[60vh] overflow-y-auto ${isDarkMode
            ? 'bg-gray-800 border-gray-700'
            : 'bg-white border-gray-300'
          }`}>
          {preview.length > 0 && (
            <div className="flex gap-2 mb-1 overflow-x-auto">
              {preview.map((img, idx) => (
                <div key={idx} className="relative w-20 h-20 shrink-0">
                  <img
                    src={img}
                    alt={`Preview ${idx + 1}`}
                    className="w-full h-full object-cover rounded-md"
                  />
                  <button
                    onClick={() => handleRemovePreview(idx)}
                    className={`absolute -top-2 -right-2 rounded-full p-1 shadow-sm ${isDarkMode ? 'bg-gray-700 text-gray-200' : 'bg-white text-black'
                      }`}
                    title="Remove"
                    type="button"
                  >
                    <RiCloseFill className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}

          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            placeholder="Ask anything"
            disabled={isSending}
            className={`w-full pl-2 pr-1 text-base sm:text-lg bg-transparent outline-none resize-none overflow-y-auto max-h-40 ${isDarkMode
                ? 'text-gray-200 placeholder-gray-500'
                : 'text-gray-800 placeholder-gray-400'
              } ${isSending ? 'opacity-50 cursor-not-allowed' : ''}`}
          />

          <div className="flex justify-between items-center h-10">
            <label className={`p-2 rounded-full cursor-pointer border ${isDarkMode
                ? 'text-gray-200 border-gray-600 hover:bg-gray-700'
                : 'text-gray-800 border-gray-300 hover:bg-gray-100'
              } ${isSending ? 'opacity-50 cursor-not-allowed' : ''}`} title="Add">
              <RiAddLargeFill className="size-5" />
              <input
                type="file"
                accept="image/*"
                multiple
                onChange={handleFileChange}
                className="hidden"
                disabled={isSending}
                title="Add"
              />
            </label>

            {hasText || preview.length > 0 ? (
              <button
                onClick={handleSubmit}
                disabled={isSending}
                className={`p-2 rounded-full transition-colors duration-200 ${isDarkMode
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : 'bg-gray-800 hover:bg-gray-900 text-white'
                  } ${isSending ? 'opacity-50 cursor-not-allowed' : ''}`}
                type="button"
                title={isSending ? 'Sending...' : 'Send'}
              >
                <RiSendPlane2Fill className="size-5" />
              </button>
            ) : (
              <button
                className={`p-2 rounded-full transition-colors duration-200 ${isDarkMode
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : 'bg-gray-800 hover:bg-gray-900 text-white'
                  } ${isSending ? 'opacity-50 cursor-not-allowed' : ''}`}
                type="button"
                title="Voice"
                onClick={() => setVoiceOpen(true)}
                disabled={isSending}
              >
                <RiChatVoiceAiFill className="size-5" />
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
