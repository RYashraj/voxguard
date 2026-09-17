"use client";

import { useRef, useCallback } from "react";

export function useMicrophone(onAudioChunk: (pcmBytes: Int16Array) => void) {
  const audioContextRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const bufferRef = useRef<Int16Array>(new Int16Array(0));

  const start = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
      audioContextRef.current = audioContext;
      
      const source = audioContext.createMediaStreamSource(stream);
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;
      
      source.connect(processor);
      processor.connect(audioContext.destination);
      
      const CHUNK_SIZE = 16000 * 3; // 3 seconds at 16kHz
      
      processor.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);
        const pcm16 = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
            let s = Math.max(-1, Math.min(1, inputData[i]));
            pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        
        // Append to buffer
        const newBuffer = new Int16Array(bufferRef.current.length + pcm16.length);
        newBuffer.set(bufferRef.current, 0);
        newBuffer.set(pcm16, bufferRef.current.length);
        bufferRef.current = newBuffer;
        
        // If we have enough for a chunk, send it and slide window by 1 second (16000 samples)
        if (bufferRef.current.length >= CHUNK_SIZE) {
            onAudioChunk(bufferRef.current.slice(0, CHUNK_SIZE));
            // Slide the window by 1 second (16000 samples)
            bufferRef.current = bufferRef.current.slice(16000);
        }
      };
    } catch (err) {
      console.error("Microphone access error:", err);
      throw err;
    }
  }, [onAudioChunk]);

  const stop = useCallback(() => {
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    bufferRef.current = new Int16Array(0);
  }, []);

  return { start, stop };
}
