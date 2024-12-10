import { getApps, initializeApp } from 'firebase/app';
import { connectAuthEmulator, getAuth } from 'firebase/auth';
import { getFirestore, connectFirestoreEmulator } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID
};

// Add debug logs
console.log('Current NODE_ENV:', process.env.NODE_ENV);
console.log('Is development?:', process.env.NODE_ENV === 'development');

// Initialize Firebase
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];
const auth = getAuth(app);
const db = getFirestore(app);

// Connect to emulators in development
if (process.env.NODE_ENV === 'development') {
  console.log('🔧 Using Firebase Emulators');
  
  // Auth Emulator
  auth.settings.appVerificationDisabledForTesting = true;
  connectAuthEmulator(auth, 'http://localhost:9099', { disableWarnings: true });
  
  // Firestore Emulator
  connectFirestoreEmulator(db, 'localhost', 8080);
  
  console.log('📝 Firestore Emulator: localhost:8080');
  console.log('🔐 Auth Emulator: localhost:9099');
} else {
  console.log('⚠️ Using Production Firebase');
}

export { app, auth, db };
