/**
 * Audio processing service - Handle audio blob conversion and chunking
 */

export class AudioProcessor {
  /**
   * Convert audio Blob to base64 string
   */
  static async blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        if (typeof reader.result === 'string') {
          // Remove data:audio/wav;base64, prefix, return only base64 content
          const base64 = reader.result.split(',')[1];
          resolve(base64);
        } else {
          reject(new Error('Failed to convert blob to base64'));
        }
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  /**
   * Get audio file information
   */
  static getAudioInfo(blob: Blob): { size: number; type: string } {
    return {
      size: blob.size,
      type: blob.type
    };
  }

  /**
   * Split audio into chunks (for future streaming processing)
   */
  static splitAudioBlob(blob: Blob, chunkSize: number = 1024 * 10): Blob[] {
    const chunks: Blob[] = [];
    let offset = 0;

    while (offset < blob.size) {
      const chunk = blob.slice(offset, offset + chunkSize);
      chunks.push(chunk);
      offset += chunkSize;
    }

    return chunks;
  }

  /**
   * Validate audio format
   */
  static isValidAudioType(blob: Blob): boolean {
    const validTypes = ['audio/wav', 'audio/webm', 'audio/mp4', 'audio/ogg'];
    return validTypes.includes(blob.type);
  }
}

// PCM player processor code (from official pcm-player-processor.js)
export const PCM_PLAYER_PROCESSOR_CODE = `
class PCMPlayerProcessor extends AudioWorkletProcessor {
  constructor() {
    super();

    // Init buffer
    this.bufferSize = 24000 * 180;  // 24kHz x 180 seconds
    this.buffer = new Float32Array(this.bufferSize);
    this.writeIndex = 0;
    this.readIndex = 0;

    // Handle incoming messages from main thread
    this.port.onmessage = (event) => {
      // Reset the buffer when 'endOfAudio' message received
      if (event.data.command === 'endOfAudio') {
        this.readIndex = this.writeIndex; // Clear the buffer
        console.log("endOfAudio received, clearing the buffer.");
        return;
      }

      // Decode the base64 data to int16 array.
      const int16Samples = new Int16Array(event.data);

      // Add the audio data to the buffer
      this._enqueue(int16Samples);
    };
  }

  // Push incoming Int16 data into our ring buffer.
  _enqueue(int16Samples) {
    for (let i = 0; i < int16Samples.length; i++) {
      // Convert 16-bit integer to float in [-1, 1]
      const floatVal = int16Samples[i] / 32768;

      // Store in ring buffer for left channel only (mono)
      this.buffer[this.writeIndex] = floatVal;
      this.writeIndex = (this.writeIndex + 1) % this.bufferSize;

      // Overflow handling (overwrite oldest samples)
      if (this.writeIndex === this.readIndex) {
        this.readIndex = (this.readIndex + 1) % this.bufferSize;
      }
    }
  }

  // The system calls process() ~128 samples at a time (depending on the browser).
  // We fill the output buffers from our ring buffer.
  process(inputs, outputs, parameters) {

    // Write a frame to the output
    const output = outputs[0];
    const framesPerBlock = output[0].length;
    for (let frame = 0; frame < framesPerBlock; frame++) {

      // Write the sample(s) into the output buffer
      output[0][frame] = this.buffer[this.readIndex]; // left channel
      if (output.length > 1) {
        output[1][frame] = this.buffer[this.readIndex]; // right channel
      }

      // Move the read index forward unless underflowing
      if (this.readIndex != this.writeIndex) {
        this.readIndex = (this.readIndex + 1) % this.bufferSize;
      }
    }

    // Returning true tells the system to keep the processor alive
    return true;
  }
}

registerProcessor('pcm-player-processor', PCMPlayerProcessor);
`;

// PCM recorder processor code (from official pcm-recorder-processor.js)
export const PCM_RECORDER_PROCESSOR_CODE = `
class PCMProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
  }

  process(inputs, outputs, parameters) {
    if (inputs.length > 0 && inputs[0].length > 0) {
      // Use the first channel
      const inputChannel = inputs[0][0];
      // Copy the buffer to avoid issues with recycled memory
      const inputCopy = new Float32Array(inputChannel);
      this.port.postMessage(inputCopy);
    }
    return true;
  }
}

registerProcessor("pcm-recorder-processor", PCMProcessor);
`;

// Audio player worklet startup (from official audio-player.js)
export async function startAudioPlayerWorklet() {
  // 1. Create an AudioContext
  const audioContext = new AudioContext({
    sampleRate: 24000
  });

  // 2. Load your custom processor code
  const blob = new Blob([PCM_PLAYER_PROCESSOR_CODE], { type: 'application/javascript' });
  const workletURL = URL.createObjectURL(blob);
  await audioContext.audioWorklet.addModule(workletURL);

  // 3. Create an AudioWorkletNode   
  const audioPlayerNode = new AudioWorkletNode(audioContext, 'pcm-player-processor');

  // 4. Connect to the destination
  audioPlayerNode.connect(audioContext.destination);

  // Clean up
  URL.revokeObjectURL(workletURL);

  // The audioPlayerNode.port is how we send messages (audio data) to the processor
  return [audioPlayerNode, audioContext];
}

// Convert Float32 samples to 16-bit PCM (from official audio-recorder.js)
function convertFloat32ToPCM(inputData: Float32Array): ArrayBuffer {
  // Create an Int16Array of the same length.
  const pcm16 = new Int16Array(inputData.length);
  for (let i = 0; i < inputData.length; i++) {
    // Multiply by 0x7fff (32767) to scale the float value to 16-bit PCM range.
    pcm16[i] = inputData[i] * 0x7fff;
  }
  // Return the underlying ArrayBuffer.
  return pcm16.buffer;
}

// Audio recorder worklet startup (from official audio-recorder.js)
export async function startAudioRecorderWorklet(audioRecorderHandler: (pcmData: ArrayBuffer) => void) {
  // Create an AudioContext
  const audioRecorderContext = new AudioContext({ sampleRate: 16000 });
  console.log("AudioContext sample rate:", audioRecorderContext.sampleRate);

  // Load the AudioWorklet module
  const blob = new Blob([PCM_RECORDER_PROCESSOR_CODE], { type: 'application/javascript' });
  const workletURL = URL.createObjectURL(blob);
  await audioRecorderContext.audioWorklet.addModule(workletURL);

  // Request access to the microphone
  const micStream = await navigator.mediaDevices.getUserMedia({
    audio: { channelCount: 1 },
  });
  const source = audioRecorderContext.createMediaStreamSource(micStream);

  // Create an AudioWorkletNode that uses the PCMProcessor
  const audioRecorderNode = new AudioWorkletNode(
    audioRecorderContext,
    "pcm-recorder-processor"
  );

  // Connect the microphone source to the worklet.
  source.connect(audioRecorderNode);
  audioRecorderNode.port.onmessage = (event) => {
    // Convert to 16-bit PCM
    const pcmData = convertFloat32ToPCM(event.data);

    // Send the PCM data to the handler.
    audioRecorderHandler(pcmData);
  };

  // Clean up
  URL.revokeObjectURL(workletURL);

  return [audioRecorderNode, audioRecorderContext, micStream];
}

// Stop the microphone (from official audio-recorder.js)
export function stopMicrophone(micStream: MediaStream) {
  micStream.getTracks().forEach((track) => track.stop());
  console.log("stopMicrophone(): Microphone stopped.");
}

// Base64 to ArrayBuffer (from official app.js)
export function base64ToArray(base64: string): ArrayBuffer {
  const binaryString = window.atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
}

// ArrayBuffer to Base64 (from official app.js)
export function arrayBufferToBase64(buffer: ArrayBuffer): string {
  let binary = '';
  const bytes = new Uint8Array(buffer);
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
} 