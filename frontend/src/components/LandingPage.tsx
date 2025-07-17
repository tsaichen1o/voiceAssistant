'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useAuth } from '@/context/AuthProvider';
import { createChatSession } from '@/services/api';
import { RiRocket2Line } from 'react-icons/ri';

export default function LandingPage() {
  const [isAnimating, setIsAnimating] = useState(false);
  const [creatingChatSession, setCreatingChatSession] = useState(false);
  const [dotCount, setDotCount] = useState(0);

  const { user } = useAuth();
  const userId = user?.id || 'guest';

  useEffect(() => {
    const timer = setTimeout(() => setIsAnimating(true), 100);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (creatingChatSession) {
      interval = setInterval(() => {
        setDotCount((prev) => (prev + 1) % 4);
      }, 400);
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
      window.location.href = `/chat/${userId}/${session.session_id}`;
    } catch {
      alert('Failed to create a chat session. Please try again later.');
      setCreatingChatSession(false);
    }
  };

  const getAnimationClass = (delay: string) => {
    return `transform transition-all duration-700 ease-out ${delay} ${isAnimating
        ? 'translate-y-0 opacity-100'
        : 'translate-y-6 opacity-0'
      }`;
  };

  return (
    <div className="flex flex-col h-screen w-screen items-center justify-center p-4 bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 text-white overflow-hidden">
      <div className="relative z-10 flex flex-col items-center justify-center p-8 text-center max-w-lg">
        <div className={getAnimationClass('delay-100')}>
          <Image
            src="/icons/logo.png"
            width={110}
            height={110}
            alt="go42TUM Logo"
            className="drop-shadow-lg rounded-3xl"
            priority
          />
        </div>

        <h1 className={`mt-6 text-3xl sm:text-4xl md:text-5xl font-bold text-gray-100 drop-shadow-md ${getAnimationClass('delay-300')}`}>
          go42TUM
        </h1>

        <p className={`mt-3 text-lg sm:text-xl text-gray-400 max-w-md ${getAnimationClass('delay-500')}`}>
          Your personal AI consultant for TUM applications.
        </p>

        <div className={`mt-10 ${getAnimationClass('delay-700')}`}>
          {!user ? (
            <Link
              href="/login"
              className="px-8 py-3 border border-gray-600 text-gray-300 rounded-xl text-base sm:text-lg font-semibold bg-gray-800/50 hover:bg-gray-700/70 hover:border-gray-500 transition-all duration-300 cursor-pointer"
            >
              Login to Start
            </Link>
          ) : (
            <button
              onClick={handleStartNow}
              className={`group relative flex items-center justify-center gap-3 px-8 py-3 bg-[#2b63b2] text-white rounded-xl text-base sm:text-lg font-semibold hover:bg-blue-500 shadow-lg shadow-blue-600/20 transition-all duration-300 transform hover:scale-105
                ${creatingChatSession ? 'cursor-not-allowed' : 'cursor-pointer'}`}
                disabled={creatingChatSession}
              type='button'
            >
              <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600 to-cyan-500 rounded-xl blur opacity-0 group-hover:opacity-75 transition duration-500"></div>

              <div className="relative flex items-center gap-3">
                <RiRocket2Line className={`transition-transform duration-500 ${creatingChatSession ? 'animate-spin' : 'group-hover:rotate-[-45deg]'}`} />
                {creatingChatSession ? (
                  <span>
                    Creating Session{'.'.repeat(dotCount)}
                  </span>
                ) : (
                  'Start Now'
                )}
              </div>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}