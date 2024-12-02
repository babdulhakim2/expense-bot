import { getApps, initializeApp } from 'firebase/app';
import { connectAuthEmulator, getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID
};

// Add debug logs
console.log('Current NODE_ENV:', process.env.NEXT_PUBLIC_NODE_ENV);
console.log('Is development?:', process.env.NEXT_PUBLIC_NODE_ENV === 'development');

// Initialize Firebase
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];
const auth = getAuth(app);

// Connect to emulator in development
if (process.env.NEXT_PUBLIC_NODE_ENV !== 'development') {
  console.log('🔧 Using Firebase Auth Emulator');
  auth.settings.appVerificationDisabledForTesting = true;
  connectAuthEmulator(auth, 'http://localhost:9099', { disableWarnings: true });
} else {
  console.log('⚠️ Not using Firebase Auth Emulator');
}

export { app, auth };
