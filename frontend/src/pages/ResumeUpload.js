import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { auth } from '../firebase';

export default function ResumeUpload() {
    const [file, setFile] = useState(null);
    const [interviewType, setInterviewType] = useState('Technical');
    const [difficulty, setDifficulty] = useState('Entry Level');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleUpload = async (e) => {
        e.preventDefault();
        setLoading(true);
        const formData = new FormData();
        formData.append('resume', file);
        formData.append('interviewType', interviewType);
        formData.append('difficulty', difficulty);

        const token = await auth.currentUser.getIdToken();
        await axios.post('http://localhost:5000/api/upload_resume', formData, {
            headers: { Authorization: `Bearer ${token}` }
        });
        navigate('/interview');
    };

    return (
        <div className="max-w-2xl mx-auto pt-28 pb-12 px-4 relative z-10">
            {/* Background Glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full max-w-[600px] opacity-30 bg-gradient-to-r from-blue-400 to-indigo-400 blur-[100px] rounded-full pointer-events-none"></div>

            <div className="relative bg-white/70 backdrop-blur-xl p-8 md:p-12 rounded-3xl border border-slate-200/60 shadow-xl shadow-slate-200/40">
                <div className="text-center mb-10">
                    <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight mb-2">Session Configuration</h2>
                    <p className="text-slate-500 font-medium">Calibrate the AI engine with your resume and preferred parameters.</p>
                </div>
                
                <form onSubmit={handleUpload} className="space-y-8">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Seniority Dropdown */}
                        <div className="space-y-2">
                            <label className="text-[11px] font-bold text-slate-500 uppercase tracking-widest">Seniority Level</label>
                            <select 
                                value={difficulty} 
                                onChange={(e) => setDifficulty(e.target.value)} 
                                className="w-full p-3.5 rounded-xl border border-slate-200 bg-white/50 text-slate-700 text-sm font-medium focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all shadow-sm"
                            >
                                <option value="Entry Level">Entry Level / Junior</option>
                                <option value="Experienced">Experienced / Senior</option>
                            </select>
                        </div>

                        {/* Interview Focus Dropdown */}
                        <div className="space-y-2">
                            <label className="text-[11px] font-bold text-slate-500 uppercase tracking-widest">Interview Focus</label>
                            <select 
                                value={interviewType} 
                                onChange={(e) => setInterviewType(e.target.value)} 
                                className="w-full p-3.5 rounded-xl border border-slate-200 bg-white/50 text-slate-700 text-sm font-medium focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all shadow-sm"
                            >
                                <option value="Technical">Technical Assessment</option>
                                <option value="HR / Behavioral">Behavioral Evaluation</option>
                            </select>
                        </div>
                    </div>

                    {/* File Upload Zone */}
                    <div className="group relative p-12 border-2 border-dashed border-slate-300 rounded-2xl bg-slate-50/50 text-center hover:bg-blue-50/50 hover:border-blue-400 transition-all cursor-pointer">
                        <input type="file" accept=".pdf" onChange={(e) => setFile(e.target.files[0])} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" />
                        <div className="flex flex-col items-center justify-center space-y-3 pointer-events-none">
                            <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-sm text-blue-500 group-hover:scale-110 transition-transform">
                                📄
                            </div>
                            <span className="text-sm font-semibold text-slate-600">Click or drag PDF resume here</span>
                            {file && <p className="mt-2 text-blue-600 text-sm font-bold bg-blue-50 px-3 py-1 rounded-full shadow-sm">{file.name}</p>}
                        </div>
                    </div>

                    <button 
                        type="submit" 
                        disabled={!file || loading} 
                        className="w-full py-4 bg-gradient-to-r from-blue-600 to-indigo-600 disabled:from-slate-300 disabled:to-slate-300 disabled:text-slate-500 disabled:shadow-none text-white font-bold rounded-xl shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50 hover:-translate-y-0.5 transition-all duration-300 text-base"
                    >
                        {loading ? "Calibrating Neural Engine..." : "Initialize Session"}
                    </button>
                </form>
            </div>
        </div>
    );
}