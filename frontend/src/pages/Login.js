import React, { useState } from 'react';
import { auth } from '../firebase';
import { 
    signInWithEmailAndPassword, 
    createUserWithEmailAndPassword,
    GoogleAuthProvider,
    signInWithPopup
} from 'firebase/auth';
import { useNavigate } from 'react-router-dom';

export default function Login() {
    const [isSignUp, setIsSignUp] = useState(false);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    // Standard Email/Password Handler
    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setLoading(true);
        try {
            if (isSignUp) await createUserWithEmailAndPassword(auth, email, password);
            else await signInWithEmailAndPassword(auth, email, password);
            navigate('/upload');
        } catch (err) {
            setError(err.message.replace("Firebase:", "System:"));
        } finally {
            setLoading(false);
        }
    };

    // NEW: Google Authentication Handler
    const handleGoogleSignIn = async () => {
        setError("");
        setLoading(true);
        const provider = new GoogleAuthProvider();
        try {
            await signInWithPopup(auth, provider);
            navigate('/upload');
        } catch (err) {
            setError(err.message.replace("Firebase:", "System:"));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-[420px] mx-auto pt-32 pb-12 px-4 relative z-10">
            {/* Background Glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full max-w-[400px] opacity-20 bg-gradient-to-r from-blue-400 to-indigo-400 blur-[80px] rounded-full pointer-events-none"></div>

            <div className="relative bg-white/70 backdrop-blur-xl p-8 md:p-10 rounded-3xl border border-slate-200/60 shadow-xl shadow-slate-200/40">
                <div className="mb-8 text-center">
                    <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
                        {isSignUp ? "Create an account" : "Welcome back"}
                    </h2>
                    <p className="text-sm text-slate-500 mt-2 font-medium">
                        Access your HyR-AI intelligence workspace.
                    </p>
                </div>

                {error && (
                    <div className="mb-6 p-3 bg-red-50 border border-red-100 text-red-600 text-xs font-medium rounded-xl text-center">
                        {error}
                    </div>
                )}

                {/* --- GOOGLE SIGN IN BUTTON --- */}
                <button 
                    onClick={handleGoogleSignIn}
                    disabled={loading}
                    className="w-full mb-6 py-3 px-4 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-bold rounded-xl shadow-sm hover:shadow-md transition-all duration-200 flex items-center justify-center gap-3"
                >
                    <svg className="w-5 h-5" viewBox="0 0 24 24">
                        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                        <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                    </svg>
                    Continue with Google
                </button>

                <div className="flex items-center mb-6">
                    <div className="flex-grow h-px bg-slate-200"></div>
                    <span className="px-3 text-xs font-bold text-slate-400 uppercase tracking-widest">Or email</span>
                    <div className="flex-grow h-px bg-slate-200"></div>
                </div>

                {/* Standard Form */}
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-1.5">
                        <label className="text-[11px] font-bold text-slate-500 uppercase tracking-widest">Email</label>
                        <input 
                            type="email" 
                            placeholder="name@company.com"
                            className="w-full p-3.5 bg-white/50 border border-slate-200 rounded-xl text-sm text-slate-800 font-medium focus:bg-white focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all shadow-sm"
                            onChange={(e) => setEmail(e.target.value)} 
                        />
                    </div>
                    <div className="space-y-1.5">
                        <label className="text-[11px] font-bold text-slate-500 uppercase tracking-widest">Password</label>
                        <input 
                            type="password" 
                            placeholder="••••••••"
                            className="w-full p-3.5 bg-white/50 border border-slate-200 rounded-xl text-sm text-slate-800 font-medium focus:bg-white focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all shadow-sm"
                            onChange={(e) => setPassword(e.target.value)} 
                        />
                    </div>
                    <button 
                        disabled={loading}
                        className="w-full py-3.5 mt-2 bg-gradient-to-r from-slate-800 to-slate-900 disabled:from-slate-400 disabled:to-slate-400 text-white font-bold rounded-xl shadow-lg shadow-slate-900/20 hover:shadow-slate-900/40 hover:-translate-y-0.5 transition-all duration-200 text-sm"
                    >
                        {loading ? "Authenticating..." : (isSignUp ? "Sign up" : "Sign in")}
                    </button>
                </form>

                <div className="mt-8 pt-6 border-t border-slate-200/60 text-center">
                    <button 
                        onClick={() => setIsSignUp(!isSignUp)}
                        className="text-xs font-bold text-slate-500 hover:text-blue-600 transition-colors uppercase tracking-widest"
                    >
                        {isSignUp ? "Already have an account? Sign in" : "Don't have an account? Sign up"}
                    </button>
                </div>
            </div>
        </div>
    );
}