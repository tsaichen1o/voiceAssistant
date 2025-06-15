'use client';

import { useState, useEffect } from 'react';

interface TypewriterTextProps {
  text: string;
  speed?: number;
  onComplete?: () => void;
}

export default function TypewriterTextForSidebar({ text, speed = 50, onComplete }: TypewriterTextProps) {
  const [displayedText, setDisplayedText] = useState('');

  useEffect(() => {
    if (displayedText.length < text.length) {
      const timer = setTimeout(() => {
        setDisplayedText(text.slice(0, displayedText.length + 1));
      }, speed);

      return () => clearTimeout(timer);
    } 
    else if (onComplete) {
      onComplete();
    }
  }, [displayedText, text, speed, onComplete]);

  return (
    <>
      <span>{displayedText}</span>
      <span className="opacity-0">{text.slice(displayedText.length)}</span>
    </>
  );
}