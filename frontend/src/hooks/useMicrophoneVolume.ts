import { useEffect, useRef, useState } from 'react';
// Source: https://developer.mozilla.org/en-US/docs/Web/API/AudioContext
// Source: https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API/Using_Web_Audio_API
// Source: https://dev.to/tooleroid/building-a-real-time-microphone-level-meter-using-web-audio-api-a-complete-guide-1e0b


export function useMicrophoneVolume(open: boolean) {
  const [volume, setVolume] = useState(0);
  const rafId = useRef<number | null>(null);

  useEffect(() => {
    let audioContext: AudioContext | null = null;
    let analyser: AnalyserNode | null = null;
    let microphone: MediaStreamAudioSourceNode | null = null;
    let mediaStream: MediaStream | null = null;

    if (!open) {
      setVolume(0);
      return;
    }

    navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
      audioContext = new (window.AudioContext || window.AudioContext)();
      analyser = audioContext.createAnalyser();
      analyser.fftSize = 512;
      microphone = audioContext.createMediaStreamSource(stream);
      microphone.connect(analyser);
      mediaStream = stream;

      const dataArray = new Uint8Array(analyser.frequencyBinCount);

      function updateVolume() {
        analyser!.getByteTimeDomainData(dataArray);
        // Calculate RMS (volume strength)
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          const value = dataArray[i] - 128;
          sum += value * value;
        }
        const rms = Math.sqrt(sum / dataArray.length) / 128;
        setVolume(rms); // 0 ~ 1
        rafId.current = requestAnimationFrame(updateVolume);
      }

      updateVolume();
    });

    return () => {
      if (rafId.current) cancelAnimationFrame(rafId.current);
      if (analyser) analyser.disconnect();
      if (microphone) microphone.disconnect();
      if (mediaStream) {
        mediaStream.getTracks().forEach((track) => track.stop());
      }
      if (audioContext) audioContext.close();
    };
  }, [open]);

  return volume;
}
