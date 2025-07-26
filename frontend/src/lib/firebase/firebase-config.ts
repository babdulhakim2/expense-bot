import { getApps, initializeApp } from "firebase/app";
import { connectAuthEmulator, getAuth } from "firebase/auth";
import { getFirestore, connectFirestoreEmulator } from "firebase/firestore";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
  measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID,
};

// Check if required config is missing and use dummy config for build time
const isConfigMissing = !firebaseConfig.apiKey || !firebaseConfig.authDomain || !firebaseConfig.projectId;

if (isConfigMissing && typeof window === 'undefined') {
  // Use dummy config during build time to prevent errors
  console.warn('Firebase config missing during build. Using dummy configuration.');
  firebaseConfig.apiKey = 'dummy-api-key';
  firebaseConfig.authDomain = 'dummy.firebaseapp.com';
  firebaseConfig.projectId = 'dummy-project';
  firebaseConfig.appId = 'dummy-app-id';
}

// Add debug logs
console.log("Current NODE_ENV:", process.env.NODE_ENV);
console.log("Is development?:", process.env.NODE_ENV === "development");

// Initialize Firebase
let app;
try {
  app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];
} catch (error) {
  console.error('Firebase initialization error:', error);
  // Create a minimal app for build time
  if (typeof window === 'undefined') {
    throw new Error('Firebase initialization failed during build');
  }
  throw error;
}
const auth = getAuth(app);
const db = getFirestore(app);

// Track if emulators are already connected
let emulatorsConnected = false;

// Connect to emulators in development (only once)
if (process.env.NODE_ENV === "development" && !emulatorsConnected) {
  console.log("🔧 Using Firebase Emulators");

  try {
    // Check if auth emulator is already connected
    if (
      !("_delegate" in auth && auth._delegate && "_emulator" in (auth._delegate as any)) // eslint-disable-line @typescript-eslint/no-explicit-any
    ) {
      console.log("🔐 Connecting to Auth Emulator...");

      // Set emulator-specific settings without iframe blocking

      connectAuthEmulator(auth, "http://localhost:9099", {
        disableWarnings: true,
      });

      // Enable app verification disabled for testing in emulator
      if (typeof window !== "undefined") {
        Object.assign(auth, {
          settings: {
            appVerificationDisabledForTesting: true,
          },
        });
      }
    }

    // Check if firestore emulator is already connected
    if (
      !(
        "_delegate" in db &&
        db._delegate &&
        "_databaseId" in (db._delegate as any) && // eslint-disable-line @typescript-eslint/no-explicit-any
        (db._delegate as any)._databaseId?.host?.includes("localhost") // eslint-disable-line @typescript-eslint/no-explicit-any
      )
    ) {
      console.log("📝 Connecting to Firestore Emulator...");
      connectFirestoreEmulator(db, "localhost", 8080);
    }

    emulatorsConnected = true;
  } catch (error) {
    console.warn(
      "⚠️ Emulator connection error (might already be connected):",
      error
    );
    emulatorsConnected = true; // Assume already connected
  }
} else if (process.env.NODE_ENV !== "development") {
  console.log("⚠️ Using Production Firebase");
}

// Add connection error handlers
auth.onAuthStateChanged((user) => {
  if (process.env.NODE_ENV === "development") {
    console.log(
      "🔐 Auth state changed:",
      user ? `User: ${user.email}` : "No user"
    );
  }
});

export { app, auth, db };
