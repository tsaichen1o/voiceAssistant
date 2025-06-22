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

interface VoiceEvent {
  type: 'text' | 'audio';
  data?: string;
  mime_type?: string;
  text?: string;
}

interface VoiceAssistantOverlayProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function VoiceAssistantOverlay({ isOpen, onClose }: VoiceAssistantOverlayProps) {
  const { user } = useAuth();
  const [paused, setPaused] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isAudioMode, setIsAudioMode] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [lastResponse, setLastResponse] = useState<string>('');
  
  // Get real-time microphone volume (only when open and not paused)
  const volume = useMicrophoneVolume(isOpen && !paused && isAudioMode);
  
  // Get userId from auth context
  const userId = user?.id || `guest-${Math.random().toString().substring(10)}`;
  
  // Use effect to monitor volume changes and interrupt speaking
  useEffect(() => {
    if (isSpeaking && volume > 0.1) { // If volume is above threshold while speaking
      setIsSpeaking(false);
      // Clear the speaking timeout since user interrupted
      if (speakingTimeoutRef.current) {
        clearTimeout(speakingTimeoutRef.current);
        speakingTimeoutRef.current = null;
      }
      console.log('🎤 User interrupted with voice - switching to listening');
    }
  }, [volume, isSpeaking]);
  
  // Refs for audio handling
  const audioPlayerNodeRef = useRef<AudioWorkletNode | null>(null);
  const audioPlayerContextRef = useRef<AudioContext | null>(null);
  const audioRecorderNodeRef = useRef<AudioWorkletNode | null>(null);
  const audioRecorderContextRef = useRef<AudioContext | null>(null);
  const eventSourceRef = useRef<AbortController | null>(null);
  const audioBufferRef = useRef<Uint8Array[]>([]);
  const bufferTimerRef = useRef<NodeJS.Timeout | null>(null);
  const speakingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Connect to SSE for real-time communication
  const connectSSE = useCallback((audioMode: boolean = true) => {
    // Abort existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.abort();
    }

    const sseUrl = `http://localhost:8000/api/voice/events/${userId}?is_audio=${audioMode}`;
    console.log(`🔗 Connecting SSE with audio mode: ${audioMode}`);
    
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
              console.log('🔗 SSE connection established');
              setIsConnected(true);
              // Set audio mode when connection is established
              setIsAudioMode(true);
            } else {
              throw new Error(`Failed to open SSE connection: ${response.status}`);
            }
          },
          onmessage(event) {
            try {
              const messageFromServer: VoiceEvent = JSON.parse(event.data);
              handleServerMessage(messageFromServer);
            } catch (error) {
              console.error('Failed to parse server message:', error);
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

  // Handle messages from server
  const handleServerMessage = (message: VoiceEvent) => {
    console.log('📨 Received server message:', message);
    
    if (message.type === 'text' && message.text) {
      setLastResponse(message.text);
      // When we receive text, system is about to speak
      setIsSpeaking(true);
      
      // Set a timeout to reset speaking state (fallback)
      if (speakingTimeoutRef.current) {
        clearTimeout(speakingTimeoutRef.current);
      }
      speakingTimeoutRef.current = setTimeout(() => {
        setIsSpeaking(false);
        console.log('🔇 Speaking timeout - resetting to listening');
      }, 10000); // 10 seconds timeout
      
    } else if (message.type === 'audio' && message.data && message.mime_type === "audio/pcm") {
      // Play audio response
      if (audioPlayerNodeRef.current) {
        setIsSpeaking(true);
        audioPlayerNodeRef.current.port.postMessage(base64ToArray(message.data));
        
        // Set a timeout to reset speaking state (fallback)
        if (speakingTimeoutRef.current) {
          clearTimeout(speakingTimeoutRef.current);
        }
        speakingTimeoutRef.current = setTimeout(() => {
          setIsSpeaking(false);
          console.log('🔇 Speaking timeout - resetting to listening');
        }, 10000); // 10 seconds timeout
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

      // Listen for audio playback completion
      if (audioPlayerNodeRef.current) {
        audioPlayerNodeRef.current.port.onmessage = (event) => {
          if (event.data.type === 'playback_ended') {
            setIsSpeaking(false);
            // Clear the speaking timeout since playback ended naturally
            if (speakingTimeoutRef.current) {
              clearTimeout(speakingTimeoutRef.current);
              speakingTimeoutRef.current = null;
            }
            console.log('🔇 Audio playback ended');
          }
        };
      }

      // Start audio input
      const [recorderNode, recorderCtx] = await startAudioRecorderWorklet(audioRecorderHandler);
      audioRecorderNodeRef.current = recorderNode as AudioWorkletNode;
      audioRecorderContextRef.current = recorderCtx as AudioContext;

      console.log('🎵 Audio system initialized successfully');
      return true;
    } catch (error) {
      console.error('❌ Failed to initialize audio system:', error);
      return false;
    }
  }, []);

  // Handle audio data from recorder
  function audioRecorderHandler(pcmData: ArrayBuffer) {
    if (paused) return; // Don't process audio when paused
    
    audioBufferRef.current.push(new Uint8Array(pcmData));
    
    // Start sending buffered audio if not already started
    if (!bufferTimerRef.current) {
      bufferTimerRef.current = setInterval(sendBufferedAudio, 200);
    }
  }

  // Send buffered audio to server
  const sendBufferedAudio = async () => {
    if (paused) return; // Don't send audio when paused
    
    const audioBuffer = audioBufferRef.current;
    if (audioBuffer.length === 0) return;

    // Combine all audio chunks
    let totalLength = 0;
    for (const chunk of audioBuffer) {
      totalLength += chunk.length;
    }

    const combinedArray = new Uint8Array(totalLength);
    let offset = 0;
    for (const chunk of audioBuffer) {
      combinedArray.set(chunk, offset);
      offset += chunk.length;
    }

    // Convert to base64 and send
    const base64Data = btoa(String.fromCharCode(...combinedArray));
    
    try {
      const token = await getAccessToken();
      
      await fetch(`http://localhost:8000/api/voice/send/${userId}`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          type: 'audio',
          data: base64Data,
          mime_type: 'audio/pcm',
        }),
      });
    } catch (error) {
      console.error('Failed to send audio data:', error);
    }

    // Clear buffer
    audioBufferRef.current = [];
  };

  // Initialize audio system when overlay opens
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
          
          console.log('🎤 Voice mode starting...');
        } catch (error) {
          console.error('❌ Failed to start voice mode:', error);
        }
      };

      startAudioMode();
    }
  }, [isOpen, isAudioMode, connectSSE, initializeAudio]);

  // Handle pause/play toggle
  const handlePauseToggle = () => {
    setPaused(prev => {
      const newPaused = !prev;
      
              if (newPaused) {
          // When pausing, stop sending audio
          if (bufferTimerRef.current) {
            clearInterval(bufferTimerRef.current);
            bufferTimerRef.current = null;
          }
          console.log('⏸️ Voice paused');
        } else {
          // When resuming, restart audio sending if we have audio
          if (audioRecorderNodeRef.current && audioBufferRef.current.length === 0) {
            // Start fresh
            console.log('▶️ Voice resumed');
          }
        }
      
      return newPaused;
    });
  };

  // Handle close
  const handleClose = useCallback(() => {
    // Stop all audio processing
    if (bufferTimerRef.current) {
      clearInterval(bufferTimerRef.current);
      bufferTimerRef.current = null;
    }
    
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
    audioBufferRef.current = [];
    
    console.log('🔚 Voice assistant closed');
    onClose();
  }, [onClose]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      handleClose();
    };
  }, [handleClose]);

  return (
    <div
      className={`
        fixed inset-0 z-50 flex items-center justify-center
        bg-black/40
        transition-all duration-500
        ${isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}
      `}
    >
      <div
        className={`
          bg-white rounded-3xl shadow-2xl flex flex-col items-center
          px-8 py-10
          transition-transform duration-500
          ${isOpen ? 'scale-100' : 'scale-0'}
          origin-bottom-right
          min-w-[320px] min-h-[380px]
          relative
          overflow-hidden
        `}
      >
        {/* Status indicator */}
        <div className="absolute top-4 left-1/2 -translate-x-1/2 text-sm text-gray-600">
          {!isConnected && '🔄 Connecting...'}
          {isConnected && !isAudioMode && '⚡ Preparing...'}
          {isConnected && isAudioMode && paused && '⏸️ Paused'}
          {isConnected && isAudioMode && !paused && isSpeaking && '🔊 Speaking...'}
          {isConnected && isAudioMode && !paused && !isSpeaking && '🎤 Listening...'}
        </div>

        {/* Last response display */}
        {lastResponse && (
          <div className="absolute top-8 left-4 right-4 text-xs text-gray-500 text-center bg-gray-50 rounded-lg p-2 max-h-16 overflow-y-auto">
            AI: {lastResponse}
          </div>
        )}

        {/* Animated volume visualization */}
        <div className="absolute top-36 left-1/2 -translate-x-1/2 z-10">
          <div className="relative flex items-center justify-center">
            <div
              className={`absolute rounded-full bg-blue-100 transition-all duration-100 ${
                paused ? 'animate-pulse' : ''
              }`}
              style={{
                width: 140 + (paused ? 0 : volume * 200),
                height: 140 + (paused ? 0 : volume * 200),
                opacity: paused ? 0.1 : 0.18 + volume * 0.18,
                zIndex: 1,
              }}
            />
            <div
              className={`absolute rounded-full bg-blue-200 transition-all duration-100 ${
                paused ? 'animate-pulse' : ''
              }`}
              style={{
                width: 120 + (paused ? 0 : volume * 160),
                height: 120 + (paused ? 0 : volume * 160),
                opacity: paused ? 0.15 : 0.28 + volume * 0.28,
                zIndex: 2,
              }} 
            />
            <div
              className={`absolute rounded-full bg-blue-300 transition-all duration-100 ${
                paused ? 'animate-pulse' : ''
              }`}
              style={{
                width: 100 + (paused ? 0 : volume * 120),
                height: 100 + (paused ? 0 : volume * 120),
                opacity: paused ? 0.2 : 0.38 + volume * 0.32,
                zIndex: 3,
              }}
            />
            <div
              className={`absolute rounded-full bg-[#2F70B3] transition-all duration-100 ${
                paused ? 'animate-pulse' : ''
              }`}
              style={{
                width: 80 + (paused ? 0 : volume * 100),
                height: 80 + (paused ? 0 : volume * 100),
                opacity: paused ? 0.5 : 0.8,
                zIndex: 4,
              }}
            />
            <div className="absolute text-2xl font-bold text-[#2F70B3] z-10">🤖</div>
          </div>
        </div>

        {/* Control buttons */}
        <div className="flex gap-12 mt-auto mb-2 z-20">
          <button
            className="size-16 flex justify-center items-center gap-2 px-5 py-2 rounded-2xl bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold transition"
            onClick={handlePauseToggle}
            title={paused ? 'Resume' : 'Pause'}
            disabled={!isAudioMode}
          >
            {paused ? <FaPlay size={24} title="Resume" /> : <FaPause size={24} title="Pause" />}
          </button>
          <button
            className="size-16 flex justify-center items-center gap-2 px-5 py-2 rounded-2xl bg-red-600 hover:bg-red-700 text-[#FAFAFA] font-semibold transition"
            onClick={handleClose}
            title="Close"
          >
            <FaTimes size={24} title="Close" />
          </button>
        </div>
      </div>
    </div>
  );
}
