import { initializeApp } from "firebase/app";
import { getAuth, connectAuthEmulator } from "firebase/auth";
import { firebaseConfig } from "./config";

// Initialize Firebase
export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);

// Connect to emulators in development
if (process.env.NEXT_PUBLIC_USE_FIREBASE_EMULATOR === "true") {
  console.log("Using Firebase Auth Emulator");
  connectAuthEmulator(auth, "http://localhost:9099", { disableWarnings: true });
} 