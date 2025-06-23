'use client';

import { fetchEventSource } from '@microsoft/fetch-event-source';
import { useState, useEffect } from 'react';
import { getAccessToken } from '@/services/api';
import { Citation, StreamResponse } from '@/types/chat';
import { EventSourceMessage } from '@microsoft/fetch-event-source';
// Source: https://zhuanlan.zhihu.com/p/634018241
// Source: https://medium.com/pon-tech-talk/extend-the-usage-of-the-eventsource-api-with-microsoft-fetch-event-source-a5c83ff95964


interface TypewriterTextProps {
  streamUrl: string;
  onComplete?: (finalContent: string, citations?: Citation[]) => void;
  onError?: (error: string) => void;
}

// TODO: citations implementation
export default function TypewriterText({ streamUrl, onComplete, onError }: TypewriterTextProps) {
  const [displayedText, setDisplayedText] = useState('');
  // const [citations, setCitations] = useState<Citation[]>([]);
  const [error, setError] = useState<string | null>(null);

    useEffect(() => {
    if (!streamUrl) {
      return;
    }

    setDisplayedText('');
    // setCitations([]);
    setError(null);
    
    let accumulatedText = '';
    let accumulatedCitations: Citation[] = [];
    
    const abortController = new AbortController();

    const startStream = async () => {
      try {
        const token = await getAccessToken();

        await fetchEventSource(streamUrl, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Accept': 'text/event-stream',
          },
          signal: abortController.signal,

          onopen: async (response) => {
            if (!response.ok) {
              const errorText = await response.text();
              throw new Error(`Failed to open stream: ${response.status} ${errorText}`);
            }
          },

          onmessage: (event: EventSourceMessage) => {
            if (abortController.signal.aborted) return;
            if (event.data === '[done]') {
              onComplete?.(accumulatedText, accumulatedCitations);
              abortController.abort();
              return;
            }
            if (event.data.startsWith('[error]')) {
              const errorMsg = event.data.replace('[error]', '').trim();
              setError(errorMsg);
              onError?.(errorMsg);
              abortController.abort();
              return;
            }

            try {
              const payload: StreamResponse = JSON.parse(event.data);
              if (payload.content) {
                accumulatedText += payload.content;
                setDisplayedText(prev => prev + payload.content);
              }
              if (payload.citations && payload.citations.length > 0) {
                accumulatedCitations = payload.citations;
                // setCitations(payload.citations);
              }
            } catch (e) {
              console.error('Failed to parse stream data:', event.data, e);
            }
          },

          onerror: (err) => {
            if (!abortController.signal.aborted) {
              setError(err.message || 'A stream error occurred.');
              onError?.(err.message || 'A stream error occurred.');
            }
            abortController.abort();
            throw err;
          },
        });
      } catch (fetchError) {
        if (!abortController.signal.aborted) {
          setError((fetchError as Error).message);
          onError?.((fetchError as Error).message);
        }
      }
    };

    startStream();

    return () => {
      console.log(`Cleaning up stream for: ${streamUrl}`);
      abortController.abort();
    };

  }, [streamUrl, onComplete, onError]);

  if (error) {
    console.error(error);
  }

  return <span>{displayedText}</span>;
}