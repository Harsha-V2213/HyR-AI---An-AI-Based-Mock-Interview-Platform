import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { auth } from '../firebase'; 

const InterviewSession = () => {
    const navigate = useNavigate();
    const API_BASE_URL = "http://localhost:5000"; 
    
    const [aiState, setAiState] = useState({
        status: "Connecting...",
        current_state: "IDLE",
        current_question: "Loading your interview...",
        is_busy: false,
    });
    const [behavior, setBehavior] = useState({ status: "Waiting for camera...", emotion: null });
    const [frameCount, setFrameCount] = useState(0);

    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const streamRef = useRef(null); 
    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);
    const frameIntervalRef = useRef(null);

    const stopAllHardware = () => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
        if (frameIntervalRef.current) {
            clearInterval(frameIntervalRef.current);
            frameIntervalRef.current = null;
        }
    };

    useEffect(() => {
        const startHardware = async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                streamRef.current = stream; 
                
                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                }

                const mediaRecorder = new MediaRecorder(stream);
                mediaRecorderRef.current = mediaRecorder;

                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) audioChunksRef.current.push(event.data);
                };

                mediaRecorder.onstop = async () => {
                    setAiState(prev => ({ ...prev, is_busy: true, status: "Analyzing response..." }));
                    const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
                    const formData = new FormData();
                    formData.append('audio', audioBlob, 'answer.wav');
                    audioChunksRef.current = []; 

                    try {
                        const token = await auth.currentUser.getIdToken();
                        await axios.post(`${API_BASE_URL}/api/process_audio`, formData, {
                            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'multipart/form-data' }
                        });
                        fetchSessionState();
                    } catch (error) {
                        setAiState(prev => ({ ...prev, is_busy: false, status: "Error in analysis." }));
                    }
                };

                startVideoProctor();
            } catch (err) {
                setBehavior({ status: "Hardware Blocked.", emotion: null });
            }
        };

        startHardware();
        fetchSessionState();

        return () => stopAllHardware();
    }, []);

    const startVideoProctor = () => {
        frameIntervalRef.current = setInterval(() => {
            if (videoRef.current && canvasRef.current && streamRef.current) {
                const canvas = canvasRef.current;
                const context = canvas.getContext('2d');
                context.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
                const base64Image = canvas.toDataURL('image/jpeg');
                setFrameCount(prev => prev + 1);

                axios.post(`${API_BASE_URL}/api/process_frame`, { 
                    image: base64Image, 
                    frame_counter: frameCount 
                })
                .then(res => setBehavior(res.data))
                .catch(err => console.error("Proctor Error", err));
            }
        }, 1000); 
    };

    const fetchSessionState = async () => {
        try {
            const token = await auth.currentUser?.getIdToken();
            const res = await axios.get(`${API_BASE_URL}/get_status`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            setAiState(res.data);
            
            if (res.data.current_state === "COMPLETE") {
                stopAllHardware();
            }
        } catch (error) {
            console.error(error);
        }
    };

    const handleStartRecording = () => {
        if (mediaRecorderRef.current) {
            mediaRecorderRef.current.start();
            setAiState(prev => ({ ...prev, current_state: "RECORDING", status: "Listening..." }));
        }
    };

    const handleStopRecording = () => {
        if (mediaRecorderRef.current?.state === "recording") {
            mediaRecorderRef.current.stop();
        }
    };

    return (
        // 1. Strict height constraint (h-screen) and disabled scrolling (overflow-hidden)
        <div className="h-screen bg-gray-50 flex flex-col items-center py-4 px-4 overflow-hidden">
            
            <h1 className="text-2xl font-extrabold text-gray-900 mb-4 flex-shrink-0">Live Mock Interview</h1>
            
            <div className="w-full max-w-4xl bg-white rounded-2xl shadow-xl p-6 flex flex-col items-center flex-1 min-h-0">
                
                {/* Status Badge */}
                <div className="mb-4 flex-shrink-0">
                    <span className="bg-indigo-100 text-indigo-800 text-xs font-bold px-3 py-1.5 rounded-full uppercase">
                        {aiState.status}
                    </span>
                </div>

                {/* 2. Video dynamically scales to fill available middle space */}
                <div className="relative w-full max-w-2xl bg-black rounded-xl overflow-hidden mb-4 border border-gray-200 flex-1 min-h-0 flex items-center justify-center">
                    <video ref={videoRef} autoPlay muted playsInline className="w-full h-full object-cover transform scale-x-[-1]" />
                    <canvas ref={canvasRef} width="640" height="480" className="hidden" />
                </div>

                {/* Behavior Stats */}
                <div className="w-full max-w-2xl flex justify-between px-6 py-2 bg-gray-50 rounded-lg text-sm font-semibold mb-6 flex-shrink-0">
                    <span className={behavior.status.includes("Lost") ? "text-red-500" : "text-emerald-600"}>{behavior.status}</span>
                    <span className="text-blue-600">Emotion: {behavior.emotion?.toUpperCase() || "ANALYZING..."}</span>
                </div>

                {/* 3. Question & Controls kept at the bottom (flex-shrink-0 stops them from being crushed) */}
                <div className="w-full max-w-2xl flex flex-col items-center text-center flex-shrink-0">
                    <h2 className="text-xl font-semibold text-gray-800 mb-6 leading-relaxed line-clamp-3">
                        {aiState.current_state === "COMPLETE" ? "Session Complete" : aiState.current_question}
                    </h2>
                    
                    {aiState.current_state === "COMPLETE" && aiState.results && (
                        <div className="bg-emerald-50 border border-emerald-200 p-4 rounded-xl mb-6 w-full">
                            <p className="font-bold text-emerald-800 text-md mb-2">Final Evaluation</p>
                            <div className="flex justify-around text-emerald-900 font-medium text-sm">
                                <p>CRI: {aiState.results.cri}/100</p>
                                <p>Semantic: {aiState.results.semantic}%</p>
                                <p>Behavior: {aiState.results.behavioral}%</p>
                            </div>
                        </div>
                    )}

                    <div className="w-full flex justify-center pb-2">
                        {aiState.is_busy ? (
                            <button disabled className="bg-gray-400 text-white px-8 py-3 rounded-lg font-bold flex items-center shadow-sm cursor-not-allowed">
                                <svg className="animate-spin h-5 w-5 mr-3 text-white" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Processing Response
                            </button>
                        ) : aiState.current_state === "COMPLETE" ? (
                            <button onClick={() => navigate('/history')} className="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-3 rounded-lg font-bold shadow-md w-full max-w-xs transition-colors">
                                View History
                            </button>
                        ) : aiState.current_state === "RECORDING" ? (
                            <button onClick={handleStopRecording} className="bg-red-600 hover:bg-red-700 text-white px-8 py-3 rounded-lg font-bold shadow-md animate-pulse w-full max-w-xs transition-colors">
                                Stop Answering
                            </button>
                        ) : (
                            <button onClick={handleStartRecording} className="bg-emerald-600 hover:bg-emerald-700 text-white px-8 py-3 rounded-lg font-bold shadow-md w-full max-w-xs transition-colors">
                                Start Answering
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default InterviewSession;