"use client";

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';
import { auth } from '@/lib/firebase/firebase';
import { 
  GoogleAuthProvider, 
  signInWithPopup,
  sendSignInLinkToEmail,
  isSignInWithEmailLink,
  signInWithEmailLink
} from 'firebase/auth';
import { ArrowRight } from 'lucide-react';
import { signIn, useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import React, { FormEvent, useEffect, useState } from 'react';
import { Icons } from '@/components/shared/icons';

const actionCodeSettings = {
  url: process.env.NEXT_PUBLIC_AUTH_REDIRECT_URL,
  handleCodeInApp: true
};

export function AuthForms() {
  const { data: session } = useSession();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const { toast } = useToast();

  // Handle email link sign in on component mount
  useEffect(() => {
    const handleEmailLink = async () => {
      // Check if the URL contains a sign-in link
      if (isSignInWithEmailLink(auth, window.location.href)) {
        setLoading(true);
        try {
          // Get the email from localStorage
          let emailForSignIn = window.localStorage.getItem('emailForSignIn');
          
          if (!emailForSignIn) {
            // If email is not in storage, prompt user
            emailForSignIn = window.prompt('Please provide your email for confirmation');
          }

          if (!emailForSignIn) {
            throw new Error('Email is required to complete sign in');
          }

          // Complete the sign in process
          const result = await signInWithEmailLink(
            auth,
            emailForSignIn,
            window.location.href
          );

          // Clear the email from storage
          window.localStorage.removeItem('emailForSignIn');

          // Get the ID token
          const idToken = await result.user.getIdToken();

          // Sign in with NextAuth
          const response = await signIn('credentials', {
            token: idToken,
            redirect: false,
          });

          if (response?.error) {
            throw new Error(response.error);
          }

          // Show success message
          toast({
            title: "Success",
            description: "Signed in successfully!",
          });

          // Clear the URL parameters
          window.history.replaceState({}, document.title, window.location.pathname);

        } catch (error: any) {
          console.error('Error completing email link sign in:', error);
          toast({
            title: "Error",
            description: error.message || "Failed to complete sign in",
            variant: "destructive",
          });
        } finally {
          setLoading(false);
        }
      }
    };

    handleEmailLink();
  }, [toast]);

  if (session) return null;

  const handleGoogleSignIn = async () => {
    setLoading(true);
    try {
      const provider = new GoogleAuthProvider();
      const result = await signInWithPopup(auth, provider);
      const idToken = await result.user.getIdToken();

      await signIn('credentials', {
        token: idToken,
        redirect: false,
      });

    } catch (error: any) {
      console.error('Google sign in error:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to sign in with Google",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleEmailSignIn = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Save the email for later use
      window.localStorage.setItem('emailForSignIn', email);

      await sendSignInLinkToEmail(auth, email, actionCodeSettings as any);
      setEmailSent(true);
      
      toast({
        title: "Email Sent",
        description: "Check your email for the sign-in link",
      });
    } catch (error: any) {
      console.error('Email sign in error:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to send sign-in email",
        variant: "destructive",
      });
      window.localStorage.removeItem('emailForSignIn');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-sm space-y-5">
      <Button
        variant="outline"
        onClick={handleGoogleSignIn}
        disabled={loading}
        className="w-full"
      >
        {loading ? (
          "Signing in..."
        ) : (
          <>
            <Icons.google className="mr-2 h-4 w-4" />
            Continue with Google
          </>
        )}
      </Button>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-background px-2 text-muted-foreground">
            Or
          </span>
        </div>
      </div>

      <form onSubmit={handleEmailSignIn} className="space-y-4">
        <div className="space-y-2">
          <Input
            type="email"
            placeholder="name@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={loading || emailSent}
            required
          />
          {emailSent && (
            <p className="text-sm text-muted-foreground text-center">
              Check your email for the sign-in link
            </p>
          )}
        </div>

        <Button 
          type="submit" 
          disabled={loading || emailSent || !email}
          className="w-full"
        >
          {loading ? "Sending..." : (
            <>
              Continue with Email <ArrowRight className="ml-2 h-4 w-4" />
            </>
          )}
        </Button>
      </form>
    </div>
  );
} 