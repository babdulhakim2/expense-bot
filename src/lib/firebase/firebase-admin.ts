import { initializeApp, getApps, cert } from 'firebase-admin/app';
import { getAuth } from 'firebase-admin/auth';

// Make sure private key is properly formatted
const formatPrivateKey = (key: string) => {
  return key.replace(/\\n/g, '\n');
};

if (!getApps().length) {
  if (process.env.NODE_ENV === 'development') {
    process.env.FIREBASE_AUTH_EMULATOR_HOST = 'localhost:9099';

    initializeApp({
      projectId: 'demo-project-id',
    });

    console.log('Firebase Admin initialized with emulator');
  } else {
    const privateKey = process.env.FIREBASE_PRIVATE_KEY?.replace(/\\n/g, '\n');
    const projectId = process.env.FIREBASE_PROJECT_ID;
    const clientEmail = process.env.FIREBASE_CLIENT_EMAIL;

    if (!privateKey || !projectId || !clientEmail) {
      throw new Error('Missing required Firebase configuration. Check your environment variables.');
    }

    try {
      const credential = cert({
        projectId,
        clientEmail,
        privateKey,
      });

      initializeApp({ credential });
      console.log('Firebase Admin initialized in production mode');
    } catch (error) {
      console.error('Error initializing Firebase Admin:', error);
      throw error;
    }
  }
}

export const adminAuth = getAuth(); 