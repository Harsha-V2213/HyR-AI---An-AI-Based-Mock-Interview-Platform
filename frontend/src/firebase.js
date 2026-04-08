// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyCXngv5UGv00U3hi-fk5o3sWTcmLA8kqRo",
  authDomain: "mock-interview-platform-79f97.firebaseapp.com",
  projectId: "mock-interview-platform-79f97",
  storageBucket: "mock-interview-platform-79f97.firebasestorage.app",
  messagingSenderId: "1015682899113",
  appId: "1:1015682899113:web:c5501d978d028f2a5d9db8"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

export const auth = getAuth(app);