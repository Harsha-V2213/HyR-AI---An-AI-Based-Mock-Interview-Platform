import React, { useEffect, useRef, useState } from 'react';

export default function AudioVisualizer({ isRecording }) {
    const [volume, setVolume] = useState(0);
    const audioContextRef = useRef(null);
    const analyzerRef = useRef(null);
    const sourceRef = useRef(null);
    const requestRef = useRef(null);

    useEffect(() => {
        if (isRecording) {
            const startMicrophone = async () => {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
                    analyzerRef.current = audioContextRef.current.createAnalyser();
                    analyzerRef.current.fftSize = 256;
                    
                    sourceRef.current = audioContextRef.current.createMediaStreamSource(stream);
                    sourceRef.current.connect(analyzerRef.current);

                    const dataArray = new Uint8Array(analyzerRef.current.frequencyBinCount);

                    const updateVolume = () => {
                        analyzerRef.current.getByteFrequencyData(dataArray);
                        const sum = dataArray.reduce((a, b) => a + b, 0);
                        const avg = sum / dataArray.length;
                        setVolume(avg);
                        requestRef.current = requestAnimationFrame(updateVolume);
                    };
                    updateVolume();
                } catch (err) {
                    console.error("Mic access denied for visualizer", err);
                }
            };
            startMicrophone();
        } else {
            if (requestRef.current) cancelAnimationFrame(requestRef.current);
            if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
                audioContextRef.current.close();
            }
            setVolume(0);
        }

        return () => {
            if (requestRef.current) cancelAnimationFrame(requestRef.current);
            if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
                audioContextRef.current.close();
            }
        };
    }, [isRecording]);

    const scale = 1 + (volume / 100) * 0.6;

    return (
        <div className="flex flex-col items-center justify-center py-8">
            <div className="relative flex items-center justify-center w-20 h-20">
                <div 
                    className="absolute inset-0 bg-blue-500 rounded-full opacity-30 blur-xl transition-transform duration-75 ease-out"
                    style={{ transform: `scale(${scale * 1.5})` }}
                ></div>
                <div 
                    className="absolute inset-0 bg-gradient-to-tr from-blue-600 to-indigo-500 rounded-full shadow-lg shadow-blue-500/40 transition-transform duration-75 ease-out flex items-center justify-center"
                    style={{ transform: `scale(${scale})` }}
                >
                    <svg className="w-8 h-8 text-white relative z-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                    </svg>
                </div>
            </div>
            <p className="mt-6 text-[11px] font-bold text-blue-500 uppercase tracking-widest animate-pulse">
                Listening to your response...
            </p>
        </div>
    );
}