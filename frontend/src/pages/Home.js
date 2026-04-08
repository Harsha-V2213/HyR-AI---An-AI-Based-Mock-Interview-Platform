import React from 'react';
import { Link } from 'react-router-dom';

export default function Home() {
    return (
        <div className="relative min-h-[90vh] flex flex-col items-center justify-center overflow-hidden bg-slate-50 pt-16">
            
            {/* Ambient Background Glows */}
            <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] md:w-[800px] h-[400px] opacity-40 bg-gradient-to-r from-blue-400 to-indigo-400 blur-[100px] rounded-full pointer-events-none mix-blend-multiply"></div>
            
            <div className="relative z-10 text-center px-4 max-w-4xl mx-auto">
                
                {/* Modern Status Pill */}
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/60 backdrop-blur-sm border border-slate-200/50 shadow-sm mb-8 animate-fade-in-up">
                    <span className="relative flex h-2.5 w-2.5">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-blue-600"></span>
                    </span>
                    <span className="text-sm font-semibold text-slate-700">MockPro v4.0 Intelligence Engine</span>
                </div>

                {/* Gradient Header */}
                <h1 className="text-5xl md:text-7xl font-extrabold text-slate-900 tracking-tight mb-8 leading-[1.1]">
                    Master your next <br />
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600">
                        career maneuver.
                    </span>
                </h1>

                <p className="text-lg md:text-xl text-slate-600 font-medium mb-12 leading-relaxed max-w-2xl mx-auto">
                    A professional-grade interview simulation platform. Analyze technical depth, monitor behavioral cues, and receive high-fidelity AI evaluations.
                </p>

                {/* Primary & Secondary Actions */}
                <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                    <Link 
                        to="/login" 
                        className="w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold rounded-xl shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50 hover:-translate-y-1 transition-all duration-300 text-base"
                    >
                        Start Your Session
                    </Link>
                    <Link 
                        to="/history" 
                        className="w-full sm:w-auto px-8 py-4 bg-white text-slate-700 font-bold rounded-xl shadow-sm border border-slate-200 hover:bg-slate-50 hover:shadow-md transition-all duration-300 text-base"
                    >
                        View Archives
                    </Link>
                </div>
            </div>

            {/* Bottom Grid Features */}
            <div className="relative z-10 mt-24 w-full max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8 px-6 pb-12">
                {[
                    { title: "Mistral Powered", desc: "Adaptive, scenario-based AI questioning." },
                    { title: "Real-time Metrics", desc: "Live behavioral and semantic analysis." },
                    { title: "Role Calibration", desc: "Tailored to your specific seniority level." }
                ].map((feature, idx) => (
                    <div key={idx} className="bg-white/60 backdrop-blur-md p-6 rounded-2xl border border-slate-200/60 shadow-sm hover:shadow-md transition-shadow">
                        <p className="text-lg font-bold text-slate-900 mb-1">{feature.title}</p>
                        <p className="text-sm text-slate-500 font-medium">{feature.desc}</p>
                    </div>
                ))}
            </div>
        </div>
    );
}