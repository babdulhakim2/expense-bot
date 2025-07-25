'use client';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';
import { auth } from '@/lib/firebase/firebase-config';
import { 
  GoogleAuthProvider, 
  signInWithRedirect,
  sendSignInLinkToEmail
} from 'firebase/auth';
import { ArrowRight } from 'lucide-react';
import React, { FormEvent, useState } from 'react';
import { Icons } from '@/components/shared/icons';
import Link from 'next/link';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const { toast } = useToast();

  const handleGoogleSignIn = async () => {
    setLoading(true);
    try {
      const provider = new GoogleAuthProvider();
      await signInWithRedirect(auth, provider);
      // Redirect will handle the rest
    } catch (error) {
      const err = error as { message?: string };
      toast({
        title: "Error",
        description: err.message || "Failed to initiate Google sign in",
        variant: "destructive",
      });
      setLoading(false);
    }
  };

  const handleEmailSignIn = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!email.trim()) return;

    setLoading(true);
    try {
      await sendSignInLinkToEmail(auth, email, {
        url: `${window.location.origin}/auth/callback?email=${encodeURIComponent(email)}`,
        handleCodeInApp: true
      });
      
      setEmailSent(true);
      toast({
        title: "Email Sent",
        description: "Check your email for the sign-in link",
      });
    } catch (error) {
      const err = error as { message?: string };
      toast({
        title: "Error",
        description: err.message || "Failed to send sign-in email",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <h2 className="text-lg font-semibold">ExpenseBot</h2>
          </Link>
        </div>
      </header>

      {/* Login Content */}
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="w-full max-w-sm space-y-8">
          <div className="text-center space-y-2">
            <h1 className="text-3xl font-bold tracking-tight">Welcome back</h1>
            <p className="text-muted-foreground">
              Sign in to your account to continue
            </p>
          </div>
          
          {/* Simple Auth Form */}
          <div className="bg-card border rounded-xl p-6 shadow-sm space-y-5">
            <div className="text-center space-y-2">
              <h3 className="text-lg font-semibold">Get Started</h3>
              <p className="text-sm text-muted-foreground">
                Sign in to organize your expenses with AI
              </p>
            </div>

            {/* Google Sign In */}
            <Button
              variant="outline"
              onClick={handleGoogleSignIn}
              disabled={loading}
              className="w-full h-11 hover:bg-muted/50 transition-colors"
            >
              {loading ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                  <span>Signing in...</span>
                </div>
              ) : (
                <>
                  <Icons.google className="mr-2 h-4 w-4" />
                  Continue with Google
                </>
              )}
            </Button>

            {/* Divider */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-card px-3 text-muted-foreground font-medium">
                  Or continue with email
                </span>
              </div>
            </div>

            {/* Email Sign In */}
            <form onSubmit={handleEmailSignIn} className="space-y-4">
              <div className="space-y-3">
                <Input
                  type="email"
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading || emailSent}
                  required
                  className="h-11"
                />
                {emailSent && (
                  <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4 text-center">
                    <p className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-1">
                      ✉️ Check your email for the sign-in link
                    </p>
                    <p className="text-xs text-blue-700 dark:text-blue-300">
                      We sent a secure sign-in link to <span className="font-medium">{email}</span>
                    </p>
                  </div>
                )}
              </div>

              <Button 
                type="submit" 
                disabled={loading || emailSent || !email.trim()}
                className="w-full h-11"
              >
                {loading ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin"></div>
                    <span>Sending...</span>
                  </div>
                ) : (
                  <>
                    Continue with Email <ArrowRight className="ml-2 h-4 w-4" />
                  </>
                )}
              </Button>
            </form>
            
            <div className="text-center">
              <p className="text-xs text-muted-foreground">
                By continuing, you agree to our terms of service
              </p>
            </div>
          </div>
          
          <div className="text-center text-sm">
            <span className="text-muted-foreground">New to ExpenseBot? </span>
            <Link href="/" className="font-medium hover:underline">
              Learn more
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}