import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { auth } from '../firebase';
import { signOut } from 'firebase/auth';

export default function Navbar({ user }) {
    const navigate = useNavigate();
    
    const handleSignOut = async () => { 
        await signOut(auth); 
        navigate('/login'); 
    };

    return (
        <nav className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-md border-b border-slate-200/60 transition-all">
            {/* Glassmorphism effect applied to nav wrapper above */}
            <div className="max-w-7xl mx-auto px-6 h-16 flex justify-between items-center">
                <Link to="/" className="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/30">
                        <span className="text-white text-sm">AI</span>
                    </div>
                    HyR-AI
                </Link>
                
                <div className="flex items-center gap-8 text-sm font-medium">
                    {user ? (
                        <>
                            <Link to="/upload" className="text-slate-600 hover:text-blue-600 transition-colors">New Interview</Link>
                            <Link to="/history" className="text-slate-600 hover:text-blue-600 transition-colors">History</Link>
                            <div className="h-4 w-px bg-slate-200"></div>
                            <button onClick={handleSignOut} className="text-slate-400 hover:text-red-500 transition-colors">Log out</button>
                        </>
                    ) : (
                        <Link to="/login" className="px-5 py-2.5 bg-slate-900 text-white rounded-lg hover:bg-slate-800 hover:shadow-xl hover:-translate-y-0.5 transition-all duration-200">
                            Sign in
                        </Link>
                    )}
                </div>
            </div>
        </nav>
    );
}