'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { FaPause, FaPlay, FaTimes } from 'react-icons/fa';
import { useMicrophoneVolume } from '@/hooks/useMicrophoneVolume';
import {
  startAudioPlayerWorklet,
  startAudioRecorderWorklet,
  base64ToArray,
} from '@/services/audioProcessor';
import { getAccessToken } from '@/services/api';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { useAuth } from '@/context/AuthProvider';


interface TranscriptData {
  inline_data?: unknown;
  language?: string;
  text?: string;
}

interface VoiceEvent {
  type: 'text' | 'audio' | 'session_created' | 'transcript' | 'heartbeat' | 'error';
  data?: TranscriptData | string;
  mime_type?: string;
  text?: string;
  session_id?: string;
  timestamp?: string;
  error?: string;
  message?: string;
  partial?: boolean;
}

interface VoiceAssistantOverlayProps {
  isOpen: boolean;
  onClose: () => void;
  isDarkMode: boolean;
}


export default function VoiceAssistantOverlay({ isOpen, onClose, isDarkMode }: VoiceAssistantOverlayProps) {
  const { user } = useAuth();
  const [paused, setPaused] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isAudioMode, setIsAudioMode] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [lastResponse, setLastResponse] = useState<string>('');
  const [transcript, setTranscript] = useState<string>('');

  const volume = useMicrophoneVolume(isOpen && !paused && isAudioMode);
  const userId = user?.id;
  const sessionIdRef = useRef<string | null>(null);

  const isSendingRef = useRef(false);
  const audioPlayerNodeRef = useRef<AudioWorkletNode | null>(null);
  const audioPlayerContextRef = useRef<AudioContext | null>(null);
  const audioRecorderNodeRef = useRef<AudioWorkletNode | null>(null);
  const audioRecorderContextRef = useRef<AudioContext | null>(null);
  const eventSourceRef = useRef<AbortController | null>(null);
  const audioBufferRef = useRef<Uint8Array[]>([]);
  const speakingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (isSpeaking && volume > 0.1) {
      // 1. Send clear command to AudioWorklet to stop playback immediately
      if (audioPlayerNodeRef.current) {
        audioPlayerNodeRef.current.port.postMessage({ command: 'clear' });
      }

      // 2. Clear the subsequent "speaking timeout" timer that might be triggered
      if (speakingTimeoutRef.current) {
        clearTimeout(speakingTimeoutRef.current);
        speakingTimeoutRef.current = null;
      }

      setIsSpeaking(false);
      console.log('🎤 User interrupted with voice - switching to listening');
    }
  }, [volume]);

  // Connect to SSE for real-time communication
  const connectSSE = useCallback((audioMode: boolean = true) => {
    // Abort existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.abort();
    }

    const sseUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/voice-redis/events/${userId}?is_audio=${audioMode}`;
    console.log(`🔗 Connecting Redis SSE with audio mode: ${audioMode}`);

    const startConnection = async () => {
      try {
        const token = await getAccessToken();

        const abortController = new AbortController();
        eventSourceRef.current = abortController; // Store abort controller for cleanup

        await fetchEventSource(sseUrl, {
          headers: {
            'Authorization': `Bearer ${token}`
          },
          signal: abortController.signal,
          async onopen(response) {
            if (response.ok) {
              console.log('🔗 Redis SSE connection established');
              setIsConnected(true);
              // Set audio mode when connection is established
              setIsAudioMode(true);
            } else {
              throw new Error(`Failed to open SSE connection: ${response.status}`);
            }
          },
          onmessage(event) {
            try {
              console.log('🔍 Raw SSE message:', event.data);
              const messageFromServer: VoiceEvent = JSON.parse(event.data);
              handleServerMessage(messageFromServer);
            } catch (error) {
              console.error('Failed to parse server message:', error, 'Raw data:', event.data);
            }
          },
          onerror(error) {
            console.error('SSE connection error:', error);
            setIsConnected(false);
            throw error; // This will stop the connection
          }
        });
      } catch (error) {
        console.error('Failed to connect SSE:', error);
        setIsConnected(false);
      }
    };

    // Start connection but don't await it
    startConnection();
  }, [userId]);

  const sendBufferedAudio = async () => {
    if (paused || !isOpen || audioBufferRef.current.length === 0) {
      isSendingRef.current = false;
      return;
    }

    setLastResponse('');
    isSendingRef.current = true;

    const currentSessionId = sessionIdRef.current;
    if (!currentSessionId) {
      console.warn("Session ID not available, aborting send.");
      isSendingRef.current = false;
      return;
    }

    const audioBufferToSend = [...audioBufferRef.current];
    audioBufferRef.current = [];
    console.log(`🎤 Preparing to send ${audioBufferToSend.length} audio chunks to session: ${currentSessionId}`);

    const totalLength = audioBufferToSend.reduce((acc, chunk) => acc + chunk.length, 0);
    const combinedArray = new Uint8Array(totalLength);
    let offset = 0;
    for (const chunk of audioBufferToSend) {
      combinedArray.set(chunk, offset);
      offset += chunk.length;
    }

    const base64Data = btoa(String.fromCharCode(...combinedArray));

    console.log(`🎤 Sending audio data to session: ${currentSessionId}, size: ${base64Data.length} chars`);

    try {
      const token = await getAccessToken();
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/voice-redis/send/${currentSessionId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ mime_type: 'audio/pcm', data: base64Data }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (reader) {
        const decoder = new TextDecoder();
        let buffer = ''; // Buffer to hold incomplete message parts

        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            // Append new data from the stream to our buffer
            buffer += decoder.decode(value, { stream: true });

            // Process all complete messages (ending in '\n\n') in the buffer
            let boundaryIndex;
            while ((boundaryIndex = buffer.indexOf('\n\n')) >= 0) {
              // Extract a full message
              const message = buffer.substring(0, boundaryIndex);
              // Remove the processed message and its boundary from the buffer
              buffer = buffer.substring(boundaryIndex + 2);

              if (message.startsWith('data: ')) {
                const eventData = message.substring(6);
                if (eventData.trim()) {
                  try {
                    const data = JSON.parse(eventData);
                    handleServerMessage(data);
                  } catch (e) {
                    console.error('Error parsing server event message:', eventData, e);
                  }
                }
              }
            }
          }
        } finally {
          reader.releaseLock();
        }
      }
    } catch (error) {
      console.error('Failed to send audio data:', error);
      audioBufferRef.current = [...audioBufferToSend, ...audioBufferRef.current];
    } finally {
      isSendingRef.current = false;

      if (audioBufferRef.current.length > 0) {
        setTimeout(() => {
          if (!isSendingRef.current) {
            sendBufferedAudio();
          }
        }, 0);
      }
    }
  };

  const isSpeakingRef = useRef(isSpeaking);
  useEffect(() => {
    isSpeakingRef.current = isSpeaking;
  }, [isSpeaking]);

  // Audio recorder handler
  // This function will be called by the AudioWorklet when new PCM data is available
  const MAX_BUFFER_SIZE = 100;
  const MIN_BUFFER_CHUNKS = 20;
  const maxWaitRef = useRef<NodeJS.Timeout | null>(null);

  const audioRecorderHandler = (pcmData: ArrayBuffer) => {
    if (paused || !isOpen || isSpeakingRef.current) return;

    audioBufferRef.current.push(new Uint8Array(pcmData));

    if (audioBufferRef.current.length > MAX_BUFFER_SIZE) {
      audioBufferRef.current.shift();
      console.warn("⚠️ audioBufferRef exceeded MAX_BUFFER_SIZE, dropping old data.");
    }

    if (maxWaitRef.current) clearTimeout(maxWaitRef.current);
    maxWaitRef.current = setTimeout(() => {
      if (!isSendingRef.current && audioBufferRef.current.length > 0) {
        sendBufferedAudio();
      }
    }, 3000);

    if (!isSendingRef.current && audioBufferRef.current.length >= MIN_BUFFER_CHUNKS) {
      sendBufferedAudio();
    }
  };

  const startSpeaking = () => {
    setIsSpeaking(true);
    if (audioRecorderContextRef.current) {
      audioRecorderContextRef.current.suspend();
      console.log('🔇 Suspend recording');
    }

    audioBufferRef.current = [];
    isSendingRef.current = false;
  };

  const stopSpeaking = () => {
    setIsSpeaking(false);
    setLastResponse('');

    // 1. Reset the audio buffer to discard any stale data.
    audioBufferRef.current = [];

    // 2. Ensure the sending flag is reset.
    isSendingRef.current = false;

    if (audioRecorderContextRef.current?.state === 'suspended') {
      audioRecorderContextRef.current.resume();
      console.log('🎙️ Resume recording');
    }
  };

  const handleServerMessage = (message: VoiceEvent) => {
    console.log('📨 Received Redis server message:', message);

    if (message.type === 'session_created' && message.session_id) {
      sessionIdRef.current = message.session_id;
      console.log('✅ Voice session created and ref updated:', message.session_id);
      return;
    }

    if (message.type === 'transcript') {
      if (typeof message.data === 'object' && message.data && 'text' in message.data) {
        setTranscript((message.data as TranscriptData).text || '');
      } else {
        setTranscript('');
      }
      return;
    }


    if (message.type === 'heartbeat') {
      console.log('💓 Heartbeat received');
      return;
    }

    if (message.type === 'error') {
      console.error('❌ Server error:', message.error || message.message);
      return;
    }

    if (message.type === 'text') {
      setTranscript('');
      setLastResponse(typeof message.data === 'string' ? message.data : '');
      startSpeaking();

      if (speakingTimeoutRef.current) clearTimeout(speakingTimeoutRef.current);
      speakingTimeoutRef.current = setTimeout(stopSpeaking, 20000);
    } else if (message.type === 'audio' && message.data) {
      setTranscript('');
      if (audioPlayerNodeRef.current) {
        startSpeaking();
        if (typeof message.data === 'string') {
          audioPlayerNodeRef.current.port.postMessage(base64ToArray(message.data));
        } else {
          console.warn('Expected audio data as base64 string but got:', message.data);
        }

        if (speakingTimeoutRef.current) clearTimeout(speakingTimeoutRef.current);
        speakingTimeoutRef.current = setTimeout(stopSpeaking, 10000);
      }
    }
  };

  // Initialize audio system
  const initializeAudio = useCallback(async () => {
    try {
      // Start audio output
      const [playerNode, playerCtx] = await startAudioPlayerWorklet();
      audioPlayerNodeRef.current = playerNode as AudioWorkletNode;
      audioPlayerContextRef.current = playerCtx as AudioContext;

      if (audioPlayerNodeRef.current) {
        audioPlayerNodeRef.current.port.onmessage = (event) => {
          if (event.data.type === 'playback_ended') {
            stopSpeaking();
            if (speakingTimeoutRef.current) {
              clearTimeout(speakingTimeoutRef.current);
              speakingTimeoutRef.current = null;
            }
          }
        };

      }

      const [recorderNode, recorderCtx] = await startAudioRecorderWorklet(audioRecorderHandler);
      audioRecorderNodeRef.current = recorderNode as AudioWorkletNode;
      audioRecorderContextRef.current = recorderCtx as AudioContext;

      console.log('🎵 Audio system initialized successfully');
      return true;
    } catch (error) {
      console.error('❌ Failed to initialize audio system:', error);
      return false;
    }
  }, [paused, isOpen, setIsSpeaking]);

  // Start audio mode when overlay opens
  useEffect(() => {
    if (isOpen && !isAudioMode) {
      const startAudioMode = async () => {
        try {
          // Initialize audio system
          const success = await initializeAudio();
          if (!success) {
            throw new Error('Failed to initialize audio system');
          }

          // Connect SSE with audio mode
          connectSSE(true);

          console.log('🎤 Redis voice mode starting...');
        } catch (error) {
          console.error('❌ Failed to start voice mode:', error);
        }
      };

      startAudioMode();
    }
  }, [isOpen, isAudioMode, connectSSE]);


  // Handle pause/play toggle
  const handlePauseToggle = () => {
    setPaused(prev => {
      const newPaused = !prev;
      if (newPaused) {
        console.log('⏸️ Voice paused');
      } else {
        // When resuming, check and try to send again
        console.log('▶️ Voice resumed');
        if (!isSendingRef.current) {
          sendBufferedAudio();
        }
      }
      return newPaused;
    });
  };

  // Handle close
  const handleClose = useCallback(() => {
    console.log('🔚 handleClose called');

    // Clear speaking timeout
    if (speakingTimeoutRef.current) {
      clearTimeout(speakingTimeoutRef.current);
      speakingTimeoutRef.current = null;
    }

    // Abort SSE connection
    if (eventSourceRef.current) {
      eventSourceRef.current.abort();
      eventSourceRef.current = null;
    }

    // Close audio contexts
    if (audioRecorderContextRef.current) {
      audioRecorderContextRef.current.close();
      audioRecorderContextRef.current = null;
    }
    if (audioPlayerContextRef.current) {
      audioPlayerContextRef.current.close();
      audioPlayerContextRef.current = null;
    }

    // Reset states
    setIsConnected(false);
    setIsAudioMode(false);
    setPaused(false);
    setIsSpeaking(false);
    setLastResponse('');
    // setSessionId(null);
    sessionIdRef.current = null;
    audioBufferRef.current = [];
    isSendingRef.current = false;

    console.log('🔚 Redis voice assistant closed');
    onClose();
  }, [onClose]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      handleClose();
    };
  }, []);

  return (
    <div
      className={`
        fixed inset-0 z-50 flex flex-col justify-between p-6
        transition-opacity duration-500 ease-in-out
        ${isDarkMode ? 'bg-gradient-to-br from-gray-900 to-blue-950' : 'bg-gradient-to-br from-white to-blue-50'}
        ${isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}
      `}
    >
      <header className="w-full flex justify-between items-start">
        <div className={`
            px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-300
            ${isSpeaking ? 'bg-blue-500/20 text-blue-300' : 'bg-gray-500/20 text-gray-400'}
        `}>
          {!isConnected && '🔄 Connecting...'}
          {isConnected && paused && '⏸️ Paused'}
          {isConnected && !paused && isSpeaking && '🔊 Speaking...'}
          {isConnected && !paused && !isSpeaking && '🎤 Listening...'}
          {/* {isConnected && !paused && !isSpeaking && '⏳ Waiting for session...'} */}
        </div>
        <button
          className="size-12 flex justify-center items-center rounded-full bg-black/20 hover:bg-black/40 text-white transition cursor-pointer relative z-10"
          onClick={() => { handleClose(); }}
          title="Close"
        >
          <FaTimes size={20} />
        </button>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center -mt-10">
        <div className="h-24 text-center">
          <p className={`text-2xl font-semibold transition-opacity duration-300 ${isDarkMode ? 'text-gray-200' : 'text-gray-800'}`}>
            {transcript || lastResponse}
          </p>
        </div>

        <div className="relative w-64 h-64 flex items-center justify-center z-0">
          {[
            { size: 240, opacity: 0.05, delay: 'delay-300' },
            { size: 200, opacity: 0.1, delay: 'delay-200' },
            { size: 160, opacity: 0.15, delay: 'delay-100' },
            { size: 120, opacity: 0.2, delay: '' },
          ].map((layer, i) => (
            <div
              key={i}
              className={`absolute rounded-full bg-blue-500 transition-all duration-500 ease-out ${layer.delay} ${paused ? 'animate-pulse' : ''}`}
              style={{
                width: layer.size + (paused ? 0 : volume * (280 - i * 40)),
                height: layer.size + (paused ? 0 : volume * (280 - i * 40)),
                opacity: paused ? 0.05 : layer.opacity,
              }}
            />
          ))}

          <div
            className={`absolute text-4xl transition-transform duration-500 ease-out 
            ${isSpeaking ? 'scale-125' : 'scale-100'}`}
          >
            🤖
          </div>
        </div>
      </main>

      <footer className="w-full flex justify-center items-center">
        <button
          className="size-20 flex justify-center items-center rounded-full bg-white/90 hover:bg-white shadow-lg text-blue-600 transition-transform hover:scale-105 cursor-pointer"
          onClick={handlePauseToggle}
          title={paused ? 'Resume' : 'Pause'}
          disabled={!isAudioMode}
        >
          {paused ? <FaPlay size={28} /> : <FaPause size={28} />}
        </button>
      </footer>
    </div>
  );
}