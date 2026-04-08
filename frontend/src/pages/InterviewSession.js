import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

export default function InterviewSession() {
    const [status, setStatus] = useState({});
    const navigate = useNavigate();
    
    useEffect(() => {
        const interval = setInterval(async () => {
            try {
                const res = await axios.get("http://localhost:5000/get_status");
                setStatus(res.data);
            } catch(e) {
                console.error(e);
            }
        }, 1000);
        return () => clearInterval(interval);
    }, []);

    const handleAction = async () => {
        if (status.current_state === "COMPLETE") {
            navigate('/history');
            return;
        }
        await axios.post("http://localhost:5000/next_action");
    };

    return (
        <div className="max-w-7xl mx-auto pt-24 pb-12 px-6 flex flex-col lg:flex-row gap-8 items-stretch relative z-10">
            {/* Left: Video Feed */}
            <div className="w-full lg:w-[55%] flex flex-col">
                <div className="relative rounded-3xl overflow-hidden border border-slate-200/60 shadow-xl shadow-slate-200/50 bg-slate-900 aspect-video flex-grow">
                    <img src="http://localhost:5000/video_feed" className="w-full h-full object-cover" alt="Session Feed" />
                    
                    {/* Floating Status Pill */}
                    <div className="absolute top-4 left-4 bg-slate-900/60 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/10 flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${status.current_state === "RECORDING" ? "bg-red-500 animate-pulse" : "bg-emerald-400"}`}></span> 
                        <span className="text-[10px] font-bold text-white uppercase tracking-widest">
                            {status.current_state === "RECORDING" ? "Recording Active" : "Camera Live"}
                        </span>
                    </div>
                </div>
            </div>

            {/* Right: AI Interface */}
            <div className="w-full lg:w-[45%] flex flex-col space-y-6">
                <div className="flex-grow bg-white/70 backdrop-blur-xl p-8 lg:p-10 rounded-3xl border border-slate-200/60 shadow-xl shadow-slate-200/40 flex flex-col justify-center">
                    <div className="flex justify-between items-center mb-6">
                        <span className="text-[11px] font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600 uppercase tracking-widest">
                            {status.current_state === "COMPLETE" ? "Session Complete" : "Interviewer Output"}
                        </span>
                        <span className="text-[10px] font-mono font-semibold text-slate-400 bg-slate-100 px-2 py-1 rounded-md">
                            {status.status}
                        </span>
                    </div>
                    
                    <p className="text-2xl lg:text-3xl font-bold text-slate-800 leading-tight">
                        "{status.current_question || "Establishing connection with AI Engine..."}"
                    </p>
                </div>
                
                <button 
                    onClick={handleAction}
                    disabled={status.is_busy || status.current_state === "ANALYZING"}
                    className={`w-full py-5 rounded-2xl font-bold text-lg transition-all duration-300 ${
                        status.current_state === "RECORDING" 
                        ? "bg-red-500 text-white shadow-lg shadow-red-500/30 hover:bg-red-600 hover:-translate-y-0.5" 
                        : status.current_state === "ANALYZING" || status.is_busy
                        ? "bg-slate-200 text-slate-500 cursor-not-allowed border border-slate-300/50" 
                        : status.current_state === "COMPLETE"
                        ? "bg-slate-900 text-white shadow-xl shadow-slate-900/20 hover:bg-slate-800 hover:-translate-y-0.5"
                        : "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-xl shadow-blue-500/30 hover:shadow-blue-500/50 hover:-translate-y-0.5"
                    }`}
                >
                    {status.current_state === "RECORDING" ? "Stop Recording & Submit" 
                     : status.current_state === "ANALYZING" || status.is_busy ? "Evaluating Semantics..."
                     : status.current_state === "COMPLETE" ? "View Session Analytics" 
                     : "Start Response"}
                </button>
            </div>
        </div>
    );
}