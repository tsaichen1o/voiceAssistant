'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useAuth } from '@/context/AuthProvider';
import { createChatSession } from '@/services/api';

export default function LandingPage() {
  const [showLogo, setShowLogo] = useState(false);
  const [showText, setShowText] = useState(false);
  const [showButton, setShowButton] = useState(false);
  // TODO: add chatSessionId to state
  // const [chatSessionId, setChatSessionId] = useState<string | null>(null);
  const [creatingChatSession, setCreatingChatSession] = useState(false);
  const [dotCount, setDotCount] = useState(0);

  const { user } = useAuth();
  const userId = user?.id || 'guest';

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (creatingChatSession) {
      interval = setInterval(() => {
        setDotCount((prev) => (prev + 1) % 4);
      }, 300);
    } else {
      setDotCount(0);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [creatingChatSession]);

  const handleStartNow = async () => {
    setCreatingChatSession(true);
    try {
      const session = await createChatSession();
      // setChatSessionId(session.session_id);
      setTimeout(() => {
        window.location.href = `/chat/${userId}/${session.session_id}`;
      }, 500);
    } catch {
      alert('Failed to create chat session, please try again later');
      setCreatingChatSession(false);
    }
  };

  useEffect(() => {
    const timers = [
      setTimeout(() => setShowLogo(true), 100),
      setTimeout(() => setShowText(true), 700),
      setTimeout(() => setShowButton(true), 1300),
    ];

    return () => timers.forEach(clearTimeout);
  }, []);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-[#E7E7E7]">
      <div
        className={`transition-opacity duration-700 ${showLogo ? 'opacity-100' : 'opacity-0'
          }`}
      >
        <Image
          src="/icons/logo.png"
          width={120}
          height={120}
          alt="go42TUM Logo"
        />
      </div>

      <p
        className={`mt-4 text-base sm:text-lg md:text-xl text-center text-gray-800 transition-opacity duration-700 ${showText ? 'opacity-100' : 'opacity-0'
          }`}
      >
        Welcome to go42TUM! <br />
        Your personal consultant for TUM applications.
      </p>

      <div className={`flex gap-4 mt-6 transition-opacity duration-700 ${showButton ? 'opacity-100' : 'opacity-0'}`}>
        {!user ? (
          <Link
            href="/login"
            className="px-4 py-2 border border-[#2F70B3] text-[#2F70B3] rounded-md text-sm sm:text-base md:text-lg bg-white hover:bg-[#f1f7ff] cursor-pointer"
          >
            Login
          </Link>
        ) : (
          <button
            onClick={handleStartNow}
            className="px-4 py-2 bg-[#2F70B3] text-white rounded-md text-sm sm:text-base md:text-lg hover:bg-[#2F70B3]/80 transition-colors duration-300 cursor-pointer"
            disabled={creatingChatSession}
          >
            {creatingChatSession ? (
              <span>
                Creating{'.'.repeat(dotCount)}
              </span>
            ) : (
              'Start Now'
            )}
          </button>
        )}
      </div>
    </div>
  );
}