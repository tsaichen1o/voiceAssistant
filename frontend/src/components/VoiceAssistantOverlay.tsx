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
  type: 'text' | 'audio' | 'session_created' | 'heartbeat' | 'error';
  data?: string;
  mime_type?: string;
  format?: string;  // Audio format (mp3, pcm, etc.)
  text?: string;
  session_id?: string;
  timestamp?: string;
  error?: string;
  message?: string;
  partial?: boolean;
  sample_rate?: number;  // Audio sample rate
  text_source?: string;  // Source text for TTS audio
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
  const [sessionId, setSessionId] = useState<string | null>(null);
  const sessionIdRef = useRef<string | null>(null);
  const isSendingRef = useRef(false);
  const isOpenRef = useRef(isOpen);
  const pausedRef = useRef(paused);
  const lastSendTimeRef = useRef(0);
  const sendTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Keep refs in sync with current state
  useEffect(() => {
    isOpenRef.current = isOpen;
  }, [isOpen]);
  
  useEffect(() => {
    pausedRef.current = paused;
  }, [paused]);
  
  // Debug isOpen prop changes specifically
  const prevIsOpenRef = useRef(isOpen);
  useEffect(() => {
    if (prevIsOpenRef.current !== isOpen) {
      console.log('🚨 CRITICAL: isOpen prop changed from', prevIsOpenRef.current, 'to', isOpen);
      console.log('🔄 Updating isOpenRef to:', isOpen);
      prevIsOpenRef.current = isOpen;
    }
  }, [isOpen]);
  
  // Debug component render and state changes
  useEffect(() => {
    console.log('🔍 VoiceAssistantOverlay rendered - isOpen:', isOpen, 'paused:', paused, 'isAudioMode:', isAudioMode, 'isConnected:', isConnected);
  });
  
  // Debug state changes
  useEffect(() => {
    console.log('🔍 State changed - paused:', paused, 'isOpen:', isOpen, 'isAudioMode:', isAudioMode, 'isConnected:', isConnected);
  }, [paused, isOpen, isAudioMode, isConnected]);
  
  const volume = useMicrophoneVolume(isOpen && !paused && isAudioMode);
  const userId = user?.id;
  
  // Debug sessionId changes
  useEffect(() => {
    console.log('🔍 SessionId state changed to:', sessionId);
  }, [sessionId]);
  
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
  }, [volume, isSpeaking]);

  const audioPlayerNodeRef = useRef<AudioWorkletNode | null>(null);
  const audioPlayerContextRef = useRef<AudioContext | null>(null);
  const audioRecorderNodeRef = useRef<AudioWorkletNode | null>(null);
  const audioRecorderContextRef = useRef<AudioContext | null>(null);
  const eventSourceRef = useRef<AbortController | null>(null);
  const audioBufferRef = useRef<Uint8Array[]>([]);
  const speakingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Connect to SSE for real-time communication
  const connectSSE = useCallback((audioMode: boolean = true) => {
    // Abort existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.abort();
    }

    const sseUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/opensource-voice/events/${userId}?is_audio=${audioMode}`;
    console.log(`🔗 Connecting OpenSource Voice SSE with audio mode: ${audioMode}`);
    
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
          async           onopen(response) {
            if (response.ok) {
              console.log('🔗 OpenSource Voice SSE connection established');
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

  // Handle messages from server
  const handleServerMessage = useCallback((message: VoiceEvent) => {
    console.log('📨 Received OpenSource Voice server message:', message);
    
    // Handle session_created event
    if (message.type === 'session_created' && message.session_id) {
      console.log('🔍 Setting sessionId from:', message.session_id);
      setSessionId(message.session_id);
      sessionIdRef.current = message.session_id; // Also store in ref for immediate access
      console.log('✅ Voice session created:', message.session_id);
      return;
    }
    
    // Handle heartbeat event
    if (message.type === 'heartbeat') {
      console.log('💓 Heartbeat received');
      return;
    }
    
    // Handle error event
    if (message.type === 'error') {
      console.error('❌ Server error:', message.error || message.message);
      return;
    }
    
    if (message.type === 'text' && (message.data || message.text)) {
      const textContent = message.data || message.text || '';
      setLastResponse(textContent);
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
      
    } else if (message.type === 'audio' && message.data) {
      // Handle both PCM and MP3 audio formats
      const audioFormat = message.format || message.mime_type;
      
      if (audioFormat === "audio/pcm" || audioFormat === "pcm") {
        // Handle PCM audio (legacy Redis voice service)
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
      } else if (audioFormat === "mp3" || audioFormat === "audio/mp3") {
        // Handle MP3 audio (OpenSource voice service)
        try {
          setIsSpeaking(true);
          console.log('🎵 Playing MP3 audio from OpenSource service');
          
          // Convert base64 to blob and play with HTML5 audio
          const audioData = base64ToArray(message.data);
          const audioBlob = new Blob([audioData], { type: 'audio/mp3' });
          const audioUrl = URL.createObjectURL(audioBlob);
          
          const audio = new Audio(audioUrl);
          audio.onended = () => {
            setIsSpeaking(false);
            URL.revokeObjectURL(audioUrl);
            if (speakingTimeoutRef.current) {
              clearTimeout(speakingTimeoutRef.current);
              speakingTimeoutRef.current = null;
            }
            console.log('🔇 MP3 audio playback ended');
          };
          audio.onerror = () => {
            setIsSpeaking(false);
            URL.revokeObjectURL(audioUrl);
            console.error('❌ MP3 audio playback error');
          };
          
          audio.play().catch(error => {
            console.error('❌ Failed to play MP3 audio:', error);
            setIsSpeaking(false);
            URL.revokeObjectURL(audioUrl);
          });
          
          // Set a timeout to reset speaking state (fallback)
          if (speakingTimeoutRef.current) {
            clearTimeout(speakingTimeoutRef.current);
          }
          speakingTimeoutRef.current = setTimeout(() => {
            setIsSpeaking(false);
            console.log('🔇 MP3 Speaking timeout - resetting to listening');
          }, 15000); // 15 seconds timeout for MP3 (may be longer)
          
        } catch (error) {
          console.error('❌ Error handling MP3 audio:', error);
          setIsSpeaking(false);
        }
      } else {
        console.warn('⚠️ Unsupported audio format:', audioFormat);
      }
    }
  }, []);

  // Initialize audio system
  const initializeAudio = useCallback(async () => {
    try {
      console.log('🔧 Initializing audio system...');
      
      // Start audio output
      console.log('🔊 Starting audio player worklet...');
      const [playerNode, playerCtx] = await startAudioPlayerWorklet();
      audioPlayerNodeRef.current = playerNode as AudioWorkletNode;
      audioPlayerContextRef.current = playerCtx as AudioContext;
      console.log('✅ Audio player worklet started');

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
      console.log('🎤 Starting audio recorder worklet...');
      const [recorderNode, recorderCtx] = await startAudioRecorderWorklet(audioRecorderHandler);
      audioRecorderNodeRef.current = recorderNode as AudioWorkletNode;
      audioRecorderContextRef.current = recorderCtx as AudioContext;
      console.log('✅ Audio recorder worklet started');

      console.log('🎵 Audio system initialized successfully');
      return true;
    } catch (error) {
      console.error('❌ Failed to initialize audio system:', error);
      console.error('Error details:', error);
      return false;
    }
  }, []);

  // Send buffered audio to server
  const sendBufferedAudio = useCallback(async () => {
    const now = Date.now();
    const MIN_SEND_INTERVAL = 300; // Minimum 300ms between sends
    
    // Check if we're sending too frequently
    if (now - lastSendTimeRef.current < MIN_SEND_INTERVAL) {
      console.log('🚫 Sending too frequently, skipping this cycle');
      return;
    }
    
    console.log('🔍 sendBufferedAudio called - paused:', paused, 'isOpen:', isOpen, 'bufferLength:', audioBufferRef.current.length);
    
    // Use ref values to get current state (avoid closure issues)
    const currentPaused = pausedRef.current;
    const currentIsOpen = isOpenRef.current;
    
    console.log('🔍 sendBufferedAudio - ref values:', { currentPaused, currentIsOpen });
    console.log('🔍 sendBufferedAudio - closure values:', { paused, isOpen });
    
    if (currentPaused || !currentIsOpen) {
      console.log('🚫 Stopping send: paused or not open');
      isSendingRef.current = false;
      return;
    }
    
    const currentSessionId = sessionIdRef.current || sessionId;
    console.log('🔍 Current sessionId:', currentSessionId, 'State sessionId:', sessionId, 'Ref sessionId:', sessionIdRef.current);
    
    if (!currentSessionId) {
      console.warn('⚠️ No sessionId available, cannot send audio. State sessionId:', sessionId, 'Ref sessionId:', sessionIdRef.current);
      isSendingRef.current = false;
      return;
    }
    
    if (audioBufferRef.current.length === 0) {
      console.log('🔍 No audio data in buffer, stopping send');
      isSendingRef.current = false;
      return;
    }
    
    console.log('✅ All conditions passed, proceeding to send audio data');

    isSendingRef.current = true;
    lastSendTimeRef.current = now;

    // Combine all audio chunks into one
    const audioBufferToSend = [...audioBufferRef.current];
    audioBufferRef.current = []; // Clear the buffer immediately, ready to receive new audio

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
      // Use OpenSource Voice API endpoint with session_id
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/opensource-voice/send/${currentSessionId}`, {
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
      
      // Handle streaming response
      const reader = response.body?.getReader();
      if (reader) {
        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = new TextDecoder().decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.substring(6));
                  handleServerMessage(data);
                } catch {
                  console.warn('Failed to parse chunk:', line);
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
      // If there's an error, put the unsent audio back at the beginning of the buffer
      audioBufferRef.current = [...audioBufferToSend, ...audioBufferRef.current];
    } finally {
      // Reset sending flag
      isSendingRef.current = false;
      
      // Clear any existing timeout
      if (sendTimeoutRef.current) {
        clearTimeout(sendTimeoutRef.current);
        sendTimeoutRef.current = null;
      }
      
      // Only schedule another send if there's more data waiting
      if (audioBufferRef.current.length > 0 && isOpenRef.current && !pausedRef.current) {
        console.log('🔄 Scheduling next audio send cycle');
        sendTimeoutRef.current = setTimeout(() => {
          sendTimeoutRef.current = null;
          if (!isSendingRef.current) {
            sendBufferedAudio();
          }
        }, 200);
      } else {
        console.log('🛑 Not scheduling next send - buffer empty or component closed/paused');
      }
    }
  }, [sessionId, handleServerMessage]);

  // Handle audio data from recorder
  const audioRecorderHandler = useCallback((pcmData: ArrayBuffer) => {
    // Use ref values to get current state (avoid closure issues)
    const currentPaused = pausedRef.current;
    const currentIsOpen = isOpenRef.current;
    
    console.log(`🎤 Audio data received: ${pcmData.byteLength} bytes`);
    console.log(`🔍 Current ref values - paused: ${currentPaused}, isOpen: ${currentIsOpen}`);
    console.log(`🔍 Closure values (outdated) - paused: ${paused}, isOpen: ${isOpen}`);
    
    if (currentPaused || !currentIsOpen) {
      console.log('🚫 Audio data received but ignored (paused or closed)');
      return;
    }
    
    console.log(`📊 Adding to buffer. Current buffer size: ${audioBufferRef.current.length}, isSending: ${isSendingRef.current}`);
    audioBufferRef.current.push(new Uint8Array(pcmData));
    console.log(`📊 Buffer size after adding: ${audioBufferRef.current.length}`);
    
    // If the sending loop is not running and there's no pending timeout, start it
    if (!isSendingRef.current && !sendTimeoutRef.current) {
      console.log('🚀 Starting audio sending loop');
      sendBufferedAudio();
    } else {
      console.log('⏳ Sending loop already running or scheduled, data will be sent in next cycle');
    }
  }, [sendBufferedAudio]);
  
  // Debug when audioRecorderHandler is recreated
  useEffect(() => {
    console.log('🔄 audioRecorderHandler recreated');
  }, [audioRecorderHandler]);

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
          
          console.log('🎤 OpenSource voice mode starting...');
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
        // Clear any pending send timeout when pausing
        if (sendTimeoutRef.current) {
          clearTimeout(sendTimeoutRef.current);
          sendTimeoutRef.current = null;
        }
      } else {
        // When resuming, check and try to send again
        console.log('▶️ Voice resumed');
        // Give a small delay to ensure ref is updated
        setTimeout(() => {
          if (!isSendingRef.current && !sendTimeoutRef.current && audioBufferRef.current.length > 0) {
            sendBufferedAudio();
          }
        }, 50);
      }
      return newPaused;
    });
  };

  // Handle close
  const handleClose = useCallback(() => {
    console.log('🔚 handleClose called - Current isOpen prop:', isOpen);
    
    // Clear speaking timeout
    if (speakingTimeoutRef.current) {
      clearTimeout(speakingTimeoutRef.current);
      speakingTimeoutRef.current = null;
    }
    
    // Clear send timeout
    if (sendTimeoutRef.current) {
      clearTimeout(sendTimeoutRef.current);
      sendTimeoutRef.current = null;
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
    setSessionId(null);
    sessionIdRef.current = null;
    audioBufferRef.current = [];
    isSendingRef.current = false;

    console.log('🔚 Voice assistant cleaned up, calling parent onClose()');
    onClose();
  }, [onClose, isOpen]);

  // Cleanup on unmount
  useEffect(() => {
    console.log('🏗️ VoiceAssistantOverlay component mounted');
    return () => {
      console.log('🗑️ VoiceAssistantOverlay component unmounting, calling handleClose');
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
          {isConnected && !paused && !isSpeaking && sessionId && '🎤 Listening...'}
          {isConnected && !paused && !isSpeaking && !sessionId && '⏳ Waiting for session...'}
        </div>
        <button
          className="size-12 flex justify-center items-center rounded-full bg-black/20 hover:bg-black/40 text-white transition cursor-pointer relative z-10"
          onClick={() => {
            console.log('🔍 X button clicked, calling handleClose');
            handleClose();
          }}
          title="Close"
        >
          <FaTimes size={20} />
        </button>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center -mt-10">
        <div className="h-24 text-center">
          <p className={`text-2xl font-semibold transition-opacity duration-300 ${isDarkMode ? 'text-gray-200' : 'text-gray-800'}`}>
            {lastResponse}
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