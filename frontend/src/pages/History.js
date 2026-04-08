import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { auth } from '../firebase';

export default function History() {
    const [loading, setLoading] = useState(true);
    const [pastInterviews, setPastInterviews] = useState([]);

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const token = await auth.currentUser.getIdToken();
                const response = await axios.get("http://localhost:5000/api/history", {
                    headers: { Authorization: `Bearer ${token}` }
                });
                setPastInterviews(response.data);
            } finally {
                setLoading(false);
            }
        };
        if (auth.currentUser) fetchHistory();
    }, []);

    return (
        <div className="max-w-6xl mx-auto pt-28 pb-12 px-6">
            <div className="mb-10">
                <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight">Session Analytics</h1>
                <p className="text-slate-500 font-medium mt-2 text-lg">Your historical performance and competency readiness index.</p>
            </div>

            <div className="bg-white/80 backdrop-blur-xl rounded-3xl border border-slate-200/60 shadow-xl shadow-slate-200/40 overflow-hidden relative z-10">
                {loading ? (
                    <div className="p-24 text-center">
                        <div className="inline-block w-8 h-8 border-4 border-slate-200 border-t-blue-600 rounded-full animate-spin mb-4"></div>
                        <p className="text-slate-500 font-medium">Retrieving archives...</p>
                    </div>
                ) : pastInterviews.length === 0 ? (
                    <div className="p-24 text-center text-slate-500 font-medium">
                        No sessions recorded yet. Time to start practicing!
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead className="bg-slate-50/80 border-b border-slate-200/60">
                                <tr>
                                    <th className="px-8 py-5 text-[11px] font-bold text-slate-500 uppercase tracking-widest">Date</th>
                                    <th className="px-8 py-5 text-[11px] font-bold text-slate-500 uppercase tracking-widest">Profile</th>
                                    <th className="px-8 py-5 text-center text-[11px] font-bold text-slate-500 uppercase tracking-widest">Semantic</th>
                                    <th className="px-8 py-5 text-center text-[11px] font-bold text-slate-500 uppercase tracking-widest">Behavioral</th>
                                    <th className="px-8 py-5 text-right text-[11px] font-bold text-slate-500 uppercase tracking-widest">Final CRI Score</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                                {pastInterviews.map((session) => (
                                    <tr key={session.id} className="hover:bg-slate-50/50 transition-colors">
                                        <td className="px-8 py-6 text-slate-500 font-medium text-sm whitespace-nowrap">
                                            {new Date(session.date).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}
                                        </td>
                                        <td className="px-8 py-6 font-bold text-slate-800 text-sm">
                                            {session.role}
                                        </td>
                                        <td className="px-8 py-6 text-center text-slate-500 font-semibold text-sm">
                                            {session.semantic_score}
                                        </td>
                                        <td className="px-8 py-6 text-center text-slate-500 font-semibold text-sm">
                                            {session.behavioral_score}
                                        </td>
                                        <td className="px-8 py-6 text-right">
                                            <span className={`inline-flex items-center justify-center px-3 py-1.5 rounded-lg text-xs font-bold shadow-sm ${
                                                session.overall_cri >= 80 
                                                ? "bg-emerald-50 border border-emerald-200 text-emerald-700" 
                                                : "bg-slate-100 border border-slate-200 text-slate-700"
                                            }`}>
                                                {session.overall_cri}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}