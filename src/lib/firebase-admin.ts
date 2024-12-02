import { initializeApp, getApps, cert } from 'firebase-admin/app';
import { getAuth } from 'firebase-admin/auth';

// Make sure private key is properly formatted
const formatPrivateKey = (key: string) => {
  return key.replace(/\\n/g, '\n');
};

if (!getApps().length) {
  if (process.env.NODE_ENV === 'development') {
    // Use emulator in development
    process.env.NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_HOST = 'localhost:9099';
    
    initializeApp({
      projectId: 'demo-project-id',
    });
    
    console.log('Firebase Admin initialized with emulator');
  } else {
    // Use production credentials
    const privateKey = process.env.NEXT_PUBLIC_FIREBASE_PRIVATE_KEY;
    if (!privateKey) {
      throw new Error('FIREBASE_PRIVATE_KEY is not set in environment variables');
    }

    try {
      initializeApp({
        credential: cert({
          projectId: process.env.FIREBASE_PROJECT_ID,
          clientEmail: process.env.FIREBASE_CLIENT_EMAIL,
          privateKey: process.env.FIREBASE_PRIVATE_KEY?.replace(/\\n/g, "\n"),
        }),
      });
      console.log('Firebase Admin initialized in production mode');
    } catch (error) {
      console.error('Error initializing Firebase Admin:', error);
      throw error;
    }
  }
}

export const adminAuth = getAuth(); 