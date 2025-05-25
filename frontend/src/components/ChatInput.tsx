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
}

export default function ChatInput({ onSend }: ChatInputProps) {
  const [input, setInput] = useState('');
  const [preview, setPreview] = useState<string[]>([]);
  const [voiceOpen, setVoiceOpen] = useState(false);

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

  const handleSubmit = () => {
    if (input.trim()) {
      onSend(input);
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // When e.nativeEvent.isComposing is true, 
    // it means the user is composing a character (Chinese input method selection)
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <>
      <VoiceAssistantOverlay open={voiceOpen} onClose={() => setVoiceOpen(false)} />
      <div className="fixed bottom-0 left-0 w-full z-10 px-4 pb-4 bg-gradient-to-t from-white via-white/90 to-transparent md:ml-56">
        <div className="sm:w-full md:w-[calc(100%-14rem)] bg-white rounded-3xl shadow-md border border-gray-300 px-4 pt-4 pb-3 flex flex-col gap-3 max-h-[60vh] overflow-y-auto">
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
                    className="absolute -top-2 -right-2 bg-white text-black rounded-full p-1 shadow-sm"
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
            className="w-full pl-2 pr-1 text-base sm:text-lg text-gray-800 bg-transparent placeholder-gray-400 outline-none resize-none overflow-y-auto max-h-40"
          />

          <div className="flex justify-between items-center h-10">
            <label className="p-2 rounded-full text-gray-800 cursor-pointer border border-gray-300" title="Add">
              <RiAddLargeFill className="size-5" />
              <input
                type="file"
                accept="image/*"
                multiple
                onChange={handleFileChange}
                className="hidden"
                title="Add"
              />
            </label>

            {hasText || preview.length > 0 ? (
              <button
                onClick={handleSubmit}
                className="p-2 bg-gray-800 text-white rounded-full"
                type="button"
                title="Send"
              >
                <RiSendPlane2Fill className="size-5" />
              </button>
            ) : (
              <button
                className="p-2 bg-gray-800 text-white rounded-full"
                type="button"
                title="Voice"
                onClick={() => setVoiceOpen(true)}
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
