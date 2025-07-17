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
  const [transcript, setTranscript] = useState<string>('');
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

  // 音量检测逻辑：决定何时开始/停止录制
  useEffect(() => {
    const VOLUME_THRESHOLD = 0.05;  // 音量阈值
    const SILENCE_TIMEOUT = 1500;   // 静音1.5秒后发送
    
    // 如果组件未打开或正在暂停，不处理
    if (!isOpen || paused || isSpeaking) {
      return;
    }
    
    if (volume > VOLUME_THRESHOLD) {
      // 检测到说话
      if (!isRecordingRef.current) {
        console.log('🎤 开始录制语音 - 音量:', volume.toFixed(3));
        isRecordingRef.current = true;
        // Clear transcript when user starts speaking
        setTranscript('');
      }
      
      // 清除静音超时
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
        silenceTimeoutRef.current = null;
      }
    } else {
      // 检测到静音
      if (isRecordingRef.current && !silenceTimeoutRef.current) {
        console.log('🔇 检测到静音，启动超时计时器 - 音量:', volume.toFixed(3));
        
        // 设置静音超时
        silenceTimeoutRef.current = setTimeout(async () => {
          if (isRecordingRef.current && audioBufferRef.current.length > 0) {
            console.log('📤 静音超时，发送音频数据');
            isRecordingRef.current = false;
            
            // 直接在这里发送音频数据，避免useCallback依赖问题
            const currentSessionId = sessionIdRef.current;
            if (currentSessionId && audioBufferRef.current.length > 0) {
              try {
                // 获取缓冲的音频数据
                const audioBufferToSend = [...audioBufferRef.current];
                audioBufferRef.current = []; // 清空缓冲区
                
                const totalLength = audioBufferToSend.reduce((acc, chunk) => acc + chunk.length, 0);
                const combinedArray = new Uint8Array(totalLength);
                let offset = 0;
                for (const chunk of audioBufferToSend) {
                  combinedArray.set(chunk, offset);
                  offset += chunk.length;
                }
                
                const base64Data = btoa(String.fromCharCode(...combinedArray));
                console.log(`🎤 Sending voice activity audio: ${base64Data.length} chars`);
                
                const token = await getAccessToken();
                const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/opensource-voice/send/${currentSessionId}`, {
                  method: 'POST',
                  headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                  },
                  body: JSON.stringify({ mime_type: 'audio/pcm', data: base64Data }),
                });
                
                if (response.ok) {
                  // 处理流式响应
                  const reader = response.body?.getReader();
                  if (reader) {
                    while (true) {
                      const { done, value } = await reader.read();
                      if (done) break;
                      
                      const chunk = new TextDecoder().decode(value);
                      const lines = chunk.split('\n');
                      
                      for (const line of lines) {
                        if (line.startsWith('data: ')) {
                          try {
                            const data = JSON.parse(line.substring(6));
                            console.log('🔍 Parsed SSE data in timeout:', data);
                            handleServerMessage(data);
                          } catch (e) {
                            console.warn('Failed to parse chunk:', line, 'Error:', e);
                          }
                        } else if (line.trim() && !line.startsWith(':')) {
                          console.log('🔍 Non-data SSE line in timeout:', line);
                        }
                      }
                    }
                    reader.releaseLock();
                  }
                }
              } catch (error) {
                console.error('Voice activity send failed:', error);
              }
            }
          }
          silenceTimeoutRef.current = null;
        }, SILENCE_TIMEOUT);
      }
    }
     }, [volume, isOpen, paused, isSpeaking]);

  const audioPlayerNodeRef = useRef<AudioWorkletNode | null>(null);
  const audioPlayerContextRef = useRef<AudioContext | null>(null);
  const audioRecorderNodeRef = useRef<AudioWorkletNode | null>(null);
  const audioRecorderContextRef = useRef<AudioContext | null>(null);
  const eventSourceRef = useRef<AbortController | null>(null);
  const audioBufferRef = useRef<Uint8Array[]>([]);
  const speakingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isRecordingRef = useRef(false);  // 是否正在录制语音
  const silenceTimeoutRef = useRef<NodeJS.Timeout | null>(null);  // 静音超时

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
          async onopen(response) {
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
    console.log('🔍 Message type:', message.type);
    console.log('🔍 Message keys:', Object.keys(message));
    
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
      
      // Check if this is a transcript message (from Whisper)
      const transcriptMatch = textContent.match(/^👤 You said: "(.+)"$/);
      if (transcriptMatch) {
        const transcriptText = transcriptMatch[1];
        setTranscript(transcriptText);
        console.log('🎤 Transcript received:', transcriptText);
        return;
      }
      
      // Skip all other text messages - we only want to show transcript
      console.log('🔄 Text message ignored (not transcript):', textContent);
      return;
      
    } else if (message.type === 'audio' && message.data) {
      // Handle both PCM and MP3 audio formats
      const audioFormat = message.format || message.mime_type;
      console.log('🎵 Received audio message!');
      console.log('🔍 Audio format detected:', audioFormat);
      console.log('🔍 Audio data exists:', !!message.data);
      console.log('🔍 Audio data length:', message.data?.length || 0);
      
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
          console.log('🎵 Attempting to play MP3 audio from OpenSource service');
          console.log('🔍 Audio data length:', message.data.length, 'characters');
          
          // Convert base64 to blob and play with HTML5 audio
          const audioData = base64ToArray(message.data);
          console.log('🔍 Converted audio data size:', audioData.byteLength, 'bytes');
          
          const audioBlob = new Blob([audioData], { type: 'audio/mpeg' });
          console.log('🔍 Audio blob size:', audioBlob.size, 'bytes');
          
          const audioUrl = URL.createObjectURL(audioBlob);
          console.log('🔍 Audio URL created:', audioUrl);
          
          const audio = new Audio(audioUrl);
          
          // More detailed event handlers
          audio.onloadstart = () => console.log('🔄 Audio loading started');
          audio.oncanplaythrough = () => console.log('✅ Audio can play through');
          audio.onplay = () => console.log('▶️ Audio playback started');
          audio.onpause = () => console.log('⏸️ Audio playback paused');
          audio.onended = () => {
            setIsSpeaking(false);
            URL.revokeObjectURL(audioUrl);
            if (speakingTimeoutRef.current) {
              clearTimeout(speakingTimeoutRef.current);
              speakingTimeoutRef.current = null;
            }
            console.log('🔇 MP3 audio playback ended naturally');
          };
          audio.onerror = (e) => {
            setIsSpeaking(false);
            URL.revokeObjectURL(audioUrl);
            console.error('❌ MP3 audio playback error:', e);
            console.error('❌ Audio error details:', audio.error);
          };
          
          // Try to play with proper error handling
          console.log('🎯 Attempting to play audio...');
          audio.play()
            .then(() => {
              console.log('✅ Audio playback started successfully');
            })
            .catch(error => {
              console.error('❌ Failed to play MP3 audio:', error);
              console.error('❌ Error type:', error.name);
              console.error('❌ Error message:', error.message);
              
              // Check if it's an autoplay policy issue
              if (error.name === 'NotAllowedError') {
                console.warn('⚠️ Audio blocked by autoplay policy - user interaction required');
                // Create a user-interaction-triggered play mechanism
                const playButton = document.createElement('button');
                playButton.textContent = '🔊 Click to hear audio response';
                playButton.style.cssText = `
                  position: fixed;
                  top: 50%;
                  left: 50%;
                  transform: translate(-50%, -50%);
                  z-index: 10000;
                  background: blue;
                  color: white;
                  border: none;
                  padding: 15px 30px;
                  border-radius: 10px;
                  font-size: 16px;
                  cursor: pointer;
                `;
                playButton.onclick = () => {
                  audio.play();
                  document.body.removeChild(playButton);
                };
                document.body.appendChild(playButton);
                
                // Auto-remove after 10 seconds
                setTimeout(() => {
                  if (document.body.contains(playButton)) {
                    document.body.removeChild(playButton);
                  }
                }, 10000);
              }
              
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
    } else {
      // Debug what we actually received
      console.log('🔍 Message not processed - type:', message.type, 'has data:', !!message.data);
      if (message.type === 'audio') {
        console.log('❌ Audio message rejected - no data field');
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
    }
  }, [sessionId, handleServerMessage]);

  // Handle audio data from recorder
  const audioRecorderHandler = useCallback((pcmData: ArrayBuffer) => {
    // Use ref values to get current state (avoid closure issues)
    const currentPaused = pausedRef.current;
    const currentIsOpen = isOpenRef.current;
    const currentlyRecording = isRecordingRef.current;
    
    console.log(`🎤 Audio data received: ${pcmData.byteLength} bytes - Recording: ${currentlyRecording}`);
    
    if (currentPaused || !currentIsOpen) {
      console.log('🚫 Audio data received but ignored (paused or closed)');
      return;
    }
    
    // 只有在检测到语音活动时才收集音频数据
    if (currentlyRecording) {
      console.log(`📊 Adding to buffer. Current buffer size: ${audioBufferRef.current.length}`);
      audioBufferRef.current.push(new Uint8Array(pcmData));
      console.log(`📊 Buffer size after adding: ${audioBufferRef.current.length}`);
    } else {
      console.log('🔇 Audio data ignored - not currently recording (no voice detected)');
    }
  }, []);
  
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
          
          console.log('🎤 OpenSource voice mode starting with voice activity detection...');
        } catch (error) {
          console.error('❌ Failed to start voice mode:', error);
        }
      };

      startAudioMode();
    }
  }, [isOpen]);

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
        // Clear silence timeout when pausing
        if (silenceTimeoutRef.current) {
          clearTimeout(silenceTimeoutRef.current);
          silenceTimeoutRef.current = null;
        }
        // Reset recording state
        isRecordingRef.current = false;
      } else {
        // When resuming
        console.log('▶️ Voice resumed');
        // Recording will restart automatically when voice is detected
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
    
    // Clear silence timeout
    if (silenceTimeoutRef.current) {
      clearTimeout(silenceTimeoutRef.current);
      silenceTimeoutRef.current = null;
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
    setTranscript('');
    setSessionId(null);
    sessionIdRef.current = null;
    audioBufferRef.current = [];
    isSendingRef.current = false;
    isRecordingRef.current = false;

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
          {/* Display transcript from Whisper */}
          {transcript && (
            <p
              className={`
                rounded-sm bg-black/50 px-2 py-2
                text-l font-medium text-white shadow-lg
                transition-opacity duration-300
                whitespace-pre-wrap
              `}
            >
              <span className="mr-2">🗣️</span>
              {transcript}
            </p>
          )}
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