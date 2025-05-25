'use client';

import { useState } from 'react';
import { FaPause, FaPlay, FaTimes } from 'react-icons/fa';
import { useMicrophoneVolume } from '@/hooks/useMicrophoneVolume';


interface VoiceAssistantOverlayProps {
    open: boolean;
    onClose: () => void;
}

export default function VoiceAssistantOverlay({ open, onClose }: VoiceAssistantOverlayProps) {
    const [paused, setPaused] = useState(false);
    const volume = useMicrophoneVolume(open && !paused);

    return (
        <div
            className={`
                fixed inset-0 z-50 flex items-center justify-center
                bg-black/40
                transition-all duration-500
                ${open ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}
      `}
        >
            <div
                className={`
                    bg-white rounded-3xl shadow-2xl flex flex-col items-center
                    px-8 py-10
                    transition-transform duration-500
                    ${open ? 'scale-100' : 'scale-0'}
                    origin-bottom-right
                    min-w-[320px] min-h-[380px]
                    relative
                    overflow-hidden
                `}
            >
                <div className="absolute top-36 left-1/2 -translate-x-1/2 z-10">
                    <div className="relative flex items-center justify-center">
                        <div
                            className="absolute rounded-full bg-blue-100 transition-all duration-100"
                            style={{
                                width: 140 + volume * 200,
                                height: 140 + volume * 200,
                                opacity: 0.18 + volume * 0.18,
                                zIndex: 1,
                            }}
                        />
                        <div
                            className="absolute rounded-full bg-blue-200 transition-all duration-100"
                            style={{
                                width: 120 + volume * 160,
                                height: 120 + volume * 160,
                                opacity: 0.28 + volume * 0.28,
                                zIndex: 2,
                            }}
                        />
                        <div
                            className="absolute rounded-full bg-blue-300 transition-all duration-100"
                            style={{
                                width: 100 + volume * 120,
                                height: 100 + volume * 120,
                                opacity: 0.38 + volume * 0.32,
                                zIndex: 3,
                            }}
                        />
                        <div
                            className="absolute rounded-full bg-[#2F70B3] transition-all duration-100"
                            style={{
                                width: 80 + volume * 100,
                                height: 80 + volume * 100,
                                opacity: 0.8,
                                zIndex: 4,
                            }}
                        />
                        <div className="absolute text-2xl font-bold text-[#2F70B3] z-10">🤖</div>
                    </div>
                </div>

                <div className="flex gap-12 mt-auto mb-2 z-20">
                    <button
                        className="size-16 flex justify-center items-center gap-2 px-5 py-2 rounded-2xl bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold transition"
                        onClick={() => setPaused((p) => !p)}
                        title={paused ? 'Play' : 'Pause'}
                    >
                        {paused ? <FaPlay size={24} title="Play" /> : <FaPause size={24} title="Pause" />}
                    </button>
                    <button
                        className="size-16 flex justify-center items-center gap-2 px-5 py-2 rounded-2xl bg-red-600 hover:bg-red-700 text-[#FAFAFA] font-semibold transition"
                        onClick={onClose}
                        title="Close"
                    >
                        <FaTimes size={24} title="Close" />
                    </button>
                </div>
            </div>
        </div>
    );
}
