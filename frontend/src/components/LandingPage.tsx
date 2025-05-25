'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
// import { v4 as uuidv4 } from 'uuid';


export default function LandingPage() {
  const [showLogo, setShowLogo] = useState(false);
  const [showText, setShowText] = useState(false);
  const [showButton, setShowButton] = useState(false);

  // TODO: Remove fake userId/sessionId
  // const fakeUserId = 'u_' + uuidv4();
  // const fakeSessionId = 's_' + uuidv4();
  const fakeUserId = 'Teresa';
  const fakeSessionId = '1234567890';


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
        <Link
          href={`/chat/${fakeUserId}/${fakeSessionId}`}
          className="px-4 py-2 bg-[#2F70B3] text-white rounded-md text-sm sm:text-base md:text-lg"
        >
          Start Now
        </Link>
        <Link
          href="/login"
          className="px-4 py-2 border border-[#2F70B3] text-[#2F70B3] rounded-md text-sm sm:text-base md:text-lg bg-white hover:bg-[#f1f7ff]"
        >
          Login
        </Link>
      </div>
    </div>
  );
}