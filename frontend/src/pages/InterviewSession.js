import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import AudioVisualizer from '../components/AudioVisualizer';

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
            <div className="w-full lg:w-[55%] flex flex-col">
                <div className="relative rounded-3xl overflow-hidden border border-slate-200/60 shadow-xl shadow-slate-200/50 bg-slate-900 aspect-video flex-grow">
                    <img src="http://localhost:5000/video_feed" className="w-full h-full object-cover" alt="Session Feed" />
                    <div className="absolute top-4 left-4 bg-slate-900/60 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/10 flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${status.current_state === "RECORDING" ? "bg-red-500 animate-pulse" : "bg-emerald-400"}`}></span> 
                        <span className="text-[10px] font-bold text-white uppercase tracking-widest">
                            {status.current_state === "RECORDING" ? "Recording Active" : "Camera Live"}
                        </span>
                    </div>
                </div>
            </div>

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
                    
                    {status.current_state === "COMPLETE" && status.results ? (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-2">
                            <div className="bg-blue-50/50 border border-blue-100 p-4 rounded-2xl text-center">
                                <p className="text-[10px] font-bold text-blue-500 uppercase tracking-widest mb-1">Semantic</p>
                                <p className="text-3xl font-extrabold text-slate-800">{status.results.semantic}</p>
                            </div>
                            <div className="bg-indigo-50/50 border border-indigo-100 p-4 rounded-2xl text-center">
                                <p className="text-[10px] font-bold text-indigo-500 uppercase tracking-widest mb-1">Behavioral</p>
                                <p className="text-3xl font-extrabold text-slate-800">{status.results.behavioral}</p>
                            </div>
                            <div className="bg-emerald-50/50 border border-emerald-100 p-4 rounded-2xl text-center">
                                <p className="text-[10px] font-bold text-emerald-500 uppercase tracking-widest mb-1">Overall CRI</p>
                                <p className="text-3xl font-extrabold text-slate-800">{status.results.cri}</p>
                            </div>
                        </div>
                    ) : (
                        <div className="flex flex-col space-y-6">
                            <p className="text-2xl lg:text-3xl font-bold text-slate-800 leading-tight">
                                "{status.current_question || "Establishing connection with AI Engine..."}"
                            </p>
                            
                            {status.current_state === "RECORDING" && (
                                <AudioVisualizer isRecording={true} />
                            )}
                        </div>
                    )}
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
                     : status.current_state === "COMPLETE" ? "View Full Archives" 
                     : "Start Response"}
                </button>
            </div>
        </div>
    );
}