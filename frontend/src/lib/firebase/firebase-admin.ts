import { initializeApp, getApps, cert } from 'firebase-admin/app';
import { getAuth } from 'firebase-admin/auth';
import { getFirestore } from 'firebase-admin/firestore';

// Check if we're in build phase
const isBuildPhase = process.env.NEXT_PHASE === 'phase-production-build';

let adminAuth: ReturnType<typeof getAuth>;
let adminDb: ReturnType<typeof getFirestore>;

try {
  if (!getApps().length) {
    if (process.env.NODE_ENV === 'development') {
      process.env.FIREBASE_AUTH_EMULATOR_HOST = 'localhost:9099';
      process.env.FIRESTORE_EMULATOR_HOST = 'localhost:8080';

      initializeApp({
        projectId: 'expense-bot-9906c',
      });

      console.log('Firebase Admin initialized with emulator');
    } else {
      const privateKey = process.env.FIREBASE_PRIVATE_KEY?.replace(/\\n/g, '\n');
      const projectId = process.env.FIREBASE_PROJECT_ID;
      const clientEmail = process.env.FIREBASE_CLIENT_EMAIL;

      if (!privateKey || !projectId || !clientEmail) {
        // During build phase, use dummy values to prevent errors
        if (isBuildPhase || typeof window === 'undefined') {
          console.warn('Firebase Admin config missing during build. Using dummy configuration.');
          initializeApp({
            projectId: 'dummy-project',
          });
        } else {
          throw new Error('Missing required Firebase configuration. Check your environment variables.');
        }
      } else {
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
  }

  adminAuth = getAuth();
  adminDb = getFirestore();
} catch (error) {
  console.error('Failed to initialize Firebase Admin:', error);
  // For build time, export dummy functions
  if (isBuildPhase || typeof window === 'undefined') {
    adminAuth = {} as any; // eslint-disable-line @typescript-eslint/no-explicit-any
    adminDb = {} as any; // eslint-disable-line @typescript-eslint/no-explicit-any
  } else {
    throw error;
  }
}

export { adminAuth, adminDb };