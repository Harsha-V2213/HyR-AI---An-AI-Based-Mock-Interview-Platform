import React, { useState, useEffect } from 'react';
import { auth } from '../firebase';
import { onAuthStateChanged, signOut } from 'firebase/auth';
import { useNavigate, Link } from 'react-router-dom';

const Navbar = () => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        // Listen for Firebase Auth state changes
        const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
            setUser(currentUser);
            setLoading(false); // Auth check is complete
        });
        return () => unsubscribe();
    }, []);

    const handleLogout = async () => {
        try {
            await signOut(auth);
            navigate('/login');
        } catch (error) {
            console.error("Logout Error:", error);
        }
    };

    return (
        <nav className="flex justify-between items-center p-6 bg-white shadow-sm">
            <Link to="/" className="text-2xl font-bold text-gray-900 tracking-tight">
                HyR AI
            </Link>
            
            <div className="flex gap-4">
                {/* Only show buttons once we know the login status */}
                {!loading && (
                    <>
                        {user ? (
                            <button 
                                onClick={handleLogout} 
                                className="px-5 py-2 rounded-lg font-semibold text-gray-700 hover:bg-gray-100 transition-all"
                            >
                                Log Out
                            </button>
                        ) : (
                            <Link 
                                to="/login" 
                                className="px-5 py-2 rounded-lg font-semibold bg-indigo-600 text-white hover:bg-indigo-700 transition-all"
                            >
                                Log In
                            </Link>
                        )}
                    </>
                )}
            </div>
        </nav>
    );
};

export default Navbar;