'use client';

import { fetchEventSource } from '@microsoft/fetch-event-source';
import { useState, useEffect } from 'react';
import { getAccessToken } from '@/services/api';
// Source: https://zhuanlan.zhihu.com/p/634018241
// Source: https://medium.com/pon-tech-talk/extend-the-usage-of-the-eventsource-api-with-microsoft-fetch-event-source-a5c83ff95964


interface TypewriterTextProps {
  streamUrl: string;
  onComplete?: (finalContent: string) => void;
}

export default function TypewriterText({ streamUrl, onComplete }: TypewriterTextProps) {
  const [displayedText, setDisplayedText] = useState('');

  useEffect(() => {
    const abortController = new AbortController();
  
    const startStream = async () => {
      const token = await getAccessToken();

      let finalAccumulatedText = '';
  
      await fetchEventSource(streamUrl, {
        headers: {
          'Authorization': `Bearer ${token}`
        },
        signal: abortController.signal,
        onmessage(event) {
          if (event.data === '[done]') {
            abortController.abort();
            if (onComplete) onComplete(finalAccumulatedText);
          } else if (event.data.startsWith('[error]')) {
            abortController.abort();
            setDisplayedText('Stream failed, please try again!');
          } else {
            const chunk = event.data;
            finalAccumulatedText += chunk;
            setDisplayedText((prev) => prev + chunk);
          }
        },
        onerror(err) {
          console.error("EventSource failed:", err);
          abortController.abort();
          throw err;
        },
        onclose() {
          console.log("Stream closed");
        },
      });
    };
  
    startStream();
  
    return () => {
      abortController.abort();
    };
  }, [streamUrl, onComplete, displayedText]);

  return <span>{displayedText}</span>;
}