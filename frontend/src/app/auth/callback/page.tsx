"use client";

import { auth } from "@/lib/firebase/firebase-config";
import { UserService } from "@/lib/firebase/services/user-service";
import {
  getRedirectResult,
  isSignInWithEmailLink,
  signInWithEmailLink,
} from "firebase/auth";
import { AlertCircle, CheckCircle, Loader2 } from "lucide-react";
import { signIn } from "next-auth/react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

export default function AuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    async function handleAuthCallback() {
      try {
        const href = window.location.href;

        const redirectResult = await getRedirectResult(auth);
        if (redirectResult) {
          const idToken = await redirectResult.user.getIdToken();
          const result = await signIn("credentials", {
            token: idToken,
            redirect: false,
          });

          if (result?.error) {
            setError("Failed to complete Google sign in");
            return;
          }

          console.log("✅ User signed in with NextAuth:", redirectResult);

          try {
            await UserService.createOrUpdateUser({
              id: redirectResult.user.uid,
              email: redirectResult.user.email || "",
              name: redirectResult.user.displayName || "",
            });
            console.log("✅ User created/updated in Firestore");
          } catch (userError) {
            console.error("❌ Failed to create user in Firestore:", userError);
            // Continue with auth even if user creation fails
          }

          setSuccess(true);
          setTimeout(() => {
            router.push("/setup");
          }, 1500);
          return;
        }

        if (!isSignInWithEmailLink(auth, href)) {
          setError("Invalid or expired sign-in link");
          return;
        }

        let email = searchParams.get("email");

        if (!email) {
          // Prompt user if email not in URL (should not happen with proper email links)
          email = window.prompt("Please provide your email for confirmation");
        }

        if (!email) {
          setError("Email is required to complete sign-in");
          return;
        }

        const userCredential = await signInWithEmailLink(auth, email, href);
        const idToken = await userCredential.user.getIdToken();

        // Sign in with NextAuth using the Firebase token
        const result = await signIn("credentials", {
          token: idToken,
          redirect: false,
        });

        if (result?.error) {
          setError("Failed to complete authentication");
          return;
        }
        console.log("✅ User signed in with NextAuth:", userCredential);
        // Create/update user in Firestore (client-side)
        try {
          await UserService.createOrUpdateUser({
            id: userCredential.user.uid,
            email: userCredential.user.email || "",
            name: userCredential.user.displayName || "",
          });
          console.log("✅ User created/updated in Firestore");
        } catch (userError) {
          console.error("❌ Failed to create user in Firestore:", userError);
          // Continue with auth even if user creation fails
        }

        setSuccess(true);

        // Small delay to show success, then redirect to setup
        setTimeout(() => {
          router.push("/setup");
        }, 1500);
      } catch (error) {
        console.error("Auth callback error:", error);
        let errorMessage = "Failed to complete sign-in";

        if (error && typeof error === 'object' && 'code' in error) {
          if (error.code === "auth/invalid-email") {
            errorMessage = "Invalid email address";
          } else if (error.code === "auth/expired-action-code") {
            errorMessage = "Sign-in link has expired";
          } else if (error.code === "auth/invalid-action-code") {
            errorMessage = "Invalid sign-in link";
          }
        }

        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    }

    handleAuthCallback();
  }, [router, searchParams]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto" />
          <div className="space-y-2">
            <h2 className="text-xl font-semibold text-gray-900">
              Completing sign-in...
            </h2>
            <p className="text-gray-600">
              Please wait while we authenticate your account
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center space-y-4">
          <CheckCircle className="h-12 w-12 text-green-500 mx-auto" />
          <div className="space-y-2">
            <h2 className="text-xl font-semibold text-gray-900">Welcome!</h2>
            <p className="text-gray-600">
              Redirecting you to setup your business...
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full mx-4">
          <div className="bg-white rounded-lg shadow-sm border p-6 text-center space-y-4">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto" />
            <div className="space-y-2">
              <h2 className="text-xl font-semibold text-gray-900">
                Sign-in Failed
              </h2>
              <p className="text-gray-600">{error}</p>
            </div>
            <div className="space-y-2">
              <button
                onClick={() => router.push("/")}
                className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
              >
                Return to Home
              </button>
              <p className="text-xs text-gray-500">
                Need help? Try requesting a new sign-in link
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
