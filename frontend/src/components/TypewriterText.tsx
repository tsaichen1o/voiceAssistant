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
    let isCancelled = false;
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
          if (isCancelled) return;

          if (event.data === '[done]') {
            abortController.abort();
            if (onComplete) {
              onComplete(finalAccumulatedText);
            }
            return;
          }

          if (event.data.startsWith('[error]')) {
            console.error("Stream error from server:", event.data);
            abortController.abort();
            return;
          }

          // NOTE: since the backend is now sending a JSON object, we need to parse it
          try {
            const payload = JSON.parse(event.data);
            
            const chunk = payload.content;

            if (typeof chunk === 'string') {
              finalAccumulatedText += chunk;
              setDisplayedText((prev) => prev + chunk);
            }
          } catch (e) {
            console.error("Failed to parse stream data:", event.data, e);
          }
        },
        onerror(err) {
          if (!isCancelled) {
            console.error("EventSource failed:", err);
          }
          abortController.abort();
          throw err; 
        }
      });
    };

    startStream();

    return () => {
      isCancelled = true;
      abortController.abort();
    };
  }, [streamUrl, onComplete]);

  return <span>{displayedText}</span>;
}