// src/app/page.tsx
'use client';

import { useState, useEffect, FormEvent } from 'react';
import { Bot, Phone, ArrowRight, Receipt, Shield, Sparkles, Github } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { signIn } from 'next-auth/react';
import { auth } from '@/lib/firebase';
import { signInWithPhoneNumber, RecaptchaVerifier } from 'firebase/auth';
import { useRouter } from 'next/navigation';
import Image from 'next/image';

declare module 'firebase/auth' {
  interface Window {
    recaptchaVerifier: RecaptchaVerifier | null;
  }
}

export default function Home() {
  const [step, setStep] = useState<1 | 2>(1);
  const [phone, setPhone] = useState<string>('');
  const [verificationCode, setVerificationCode] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [confirmationResult, setConfirmationResult] = useState<any>(null);
  const [error, setError] = useState<string>('');
  const [cooldownTime, setCooldownTime] = useState<number | null>(null);
  
  const { toast } = useToast();
  const router = useRouter();

  // Clean up reCAPTCHA on mount
  useEffect(() => {
    if (window.recaptchaVerifier) {
      window.recaptchaVerifier.clear();
      // window.recaptchaVerifier = null;
    }
  }, []);

  // Handle cooldown timer
  useEffect(() => {
    if (cooldownTime && Date.now() >= cooldownTime) {
      setCooldownTime(null);
    }

    const interval = setInterval(() => {
      if (cooldownTime && Date.now() >= cooldownTime) {
        setCooldownTime(null);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [cooldownTime]);

  const formatTimeRemaining = (milliseconds: number): string => {
    const seconds = Math.ceil(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const initializeRecaptcha = async () => {
    try {
      if (!window.recaptchaVerifier) {
        const recaptchaContainer = document.getElementById('recaptcha-container');
        if (!recaptchaContainer) {
          throw new Error('Recaptcha container not found');
        }

        window.recaptchaVerifier = new RecaptchaVerifier(
          recaptchaContainer,
          {
            size: 'normal',
            callback: () => {
              console.log('reCAPTCHA verified');
            },
            'expired-callback': () => {
              setError('reCAPTCHA expired. Please try again.');
              toast({
                title: "reCAPTCHA Expired",
                description: "Please try again",
                variant: "destructive",
              });
            }
          },
          auth
        );

        await window.recaptchaVerifier.render();
      }
    } catch (error: any) {
      console.error('Error initializing reCAPTCHA:', error);
      throw new Error(error.message || 'Error initializing reCAPTCHA');
    }
  };

  const formatPhoneNumber = (number: string): string => {
    let cleaned = number.replace(/[^\d+]/g, '');
    if (!cleaned.startsWith('+')) {
      cleaned = '+' + cleaned;
    }
    return cleaned;
  };

  const handlePhoneSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    // Check if there's a stored cooldown in localStorage
    const storedCooldown = localStorage.getItem('phoneAuthCooldown');
    if (storedCooldown) {
      const cooldownTimestamp = parseInt(storedCooldown);
      if (Date.now() < cooldownTimestamp) {
        const timeLeft = formatTimeRemaining(cooldownTimestamp - Date.now());
        toast({
          title: "Rate Limited",
          description: `Please wait ${timeLeft} before trying again`,
          variant: "destructive",
        });
        return;
      } else {
        localStorage.removeItem('phoneAuthCooldown');
      }
    }

    setLoading(true);
    setError('');

    try {
      const formattedPhone = formatPhoneNumber(phone);
      if (formattedPhone.length < 8) {
        throw new Error('Please enter a valid phone number');
      }

      // Clean up any existing reCAPTCHA verifier
      if (window.recaptchaVerifier) {
        try {
          await window.recaptchaVerifier.clear();
        } catch (e) {
          console.error('Error clearing reCAPTCHA:', e);
        }
        // window.recaptchaVerifier = null;
      }

      // Remove any existing reCAPTCHA iframes
      const iframes = document.querySelectorAll('iframe[src*="recaptcha"]');
      iframes.forEach(iframe => iframe.remove());

      await initializeRecaptcha();
      
      if (!window.recaptchaVerifier) {
        throw new Error('reCAPTCHA not initialized');
      }

      const confirmation = await signInWithPhoneNumber(
        auth,
        formattedPhone,
        window.recaptchaVerifier
      );
      
      setConfirmationResult(confirmation);
      setStep(2);
      toast({
        title: "Code Sent",
        description: "Please check your phone for the verification code",
      });
    } catch (error: any) {
      console.error('Error sending code:', error);
      
      let errorMessage = 'Failed to send verification code';
      let cooldownDuration = 0;
      
      switch (error.code) {
        case 'auth/too-many-requests':
          cooldownDuration = 5 * 60 * 1000; // 5 minutes cooldown
          const cooldownTimestamp = Date.now() + cooldownDuration;
          localStorage.setItem('phoneAuthCooldown', cooldownTimestamp.toString());
          setCooldownTime(cooldownTimestamp);
          errorMessage = `Too many attempts. Please wait 5 minutes before trying again.`;
          break;
        case 'auth/invalid-phone-number':
          errorMessage = 'Invalid phone number format. Please use UK format (+44...)';
          break;
        case 'auth/missing-verification-code':
          errorMessage = 'Please complete the reCAPTCHA verification';
          break;
        case 'auth/network-request-failed':
          cooldownDuration = 30 * 1000; // 30 seconds cooldown
          const networkCooldownTimestamp = Date.now() + cooldownDuration;
          localStorage.setItem('phoneAuthCooldown', networkCooldownTimestamp.toString());
          setCooldownTime(networkCooldownTimestamp);
          errorMessage = 'Network error. Please wait 30 seconds before trying again.';
          break;
        default:
          if (error.message?.includes('reCAPTCHA')) {
            errorMessage = 'reCAPTCHA verification failed. Please try again.';
          } else {
            errorMessage = error.message || 'Error sending verification code';
          }
      }

      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
      setError(errorMessage);

      // Clean up reCAPTCHA on error
      if (window.recaptchaVerifier) {
        window.recaptchaVerifier.clear();
        // window.recaptchaVerifier = null;
      }
    } finally {
      setLoading(false);
    }
  };

  const handleOTPSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const result = await confirmationResult.confirm(verificationCode);
      const idToken = await result.user.getIdToken();

      const response = await signIn('credentials', {
        token: idToken,
        redirect: false,
        callbackUrl: '/dashboard'
      });

      if (response?.error) {
        throw new Error(response.error);
      }

      toast({
        title: "Success",
        description: "Phone number verified successfully!",
      });
      router.push('/dashboard');
    } catch (error: any) {
      console.error('Error verifying code:', error);
      toast({
        title: "Verification Failed",
        description: error.message || 'Invalid verification code',
        variant: "destructive",
      });
      setError(error.message || 'Invalid verification code');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-background to-secondary">
      <div className="container mx-auto px-4 pt-20 pb-16">
        <div className="flex flex-col items-center text-center space-y-8">
          <div className="rounded-full bg-primary/10 p-4 mb-4">
            <Bot className="w-12 h-12 text-primary" />
            {/* <Image src="/logo.svg" alt="ExpenseBot Logo" width={64} height={64} /> */}
          </div>
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight">
            Your AI-Powered
            <span className="text-primary block">Bookkeeping Assistant</span>
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl">
            Simplify your bookkeeping with ExpenseBot. Just send your receipts via WhatsApp, 
            and let AI handle the rest.
          </p>
          
          {/* Authentication Forms */}
          {step === 1 && (
            <form onSubmit={handlePhoneSubmit} className="w-full max-w-md space-y-4">
              <div className="flex space-x-2">
                <div className="relative flex-1">
                  <Phone className="absolute left-3 top-2.5 h-5 w-5 text-muted-foreground" />
                  <Input
                    type="tel"
                    placeholder="Enter your UK WhatsApp number"
                    className="pl-10"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    disabled={loading}
                  />
                </div>
                <Button type="submit" disabled={loading || (cooldownTime ? Date.now() < cooldownTime : undefined)}>
                  {loading ? (
                    "Sending..."
                  ) : cooldownTime ? (
                    `Wait ${formatTimeRemaining(cooldownTime - Date.now())}`
                  ) : (
                    <>
                      Get Started <ArrowRight className="ml-2 h-4 w-4" />
                    </>
                  )}
                </Button>
              </div>
              <div id="recaptcha-container" className="flex justify-center"></div>
              {error && (
                <p className="text-sm text-destructive">{error}</p>
              )}
            </form>
          )}
          
          {step === 2 && (
            <form onSubmit={handleOTPSubmit} className="w-full max-w-md space-y-4">
              <Input
                type="text"
                placeholder="Enter verification code"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value)}
                disabled={loading}
                className="pl-3"
              />
              <Button type="submit" disabled={loading} className="w-full">
                {loading ? (
                  "Verifying..."
                ) : (
                  <>
                    Verify Code <ArrowRight className="ml-2 h-4 w-4" />
                  </>
                )}
              </Button>
              {error && (
                <p className="text-sm text-destructive">{error}</p>
              )}
            </form>
          )}
        </div>

        {/* Rest of your UI components... */}
        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-8 mt-20">
          <div className="bg-card p-6 rounded-lg border">
            <Receipt className="w-10 h-10 text-primary mb-4" />
            <h3 className="text-lg font-semibold mb-2">Smart Receipt Processing</h3>
            <p className="text-muted-foreground">
              Simply snap and send your receipts. Our AI extracts and categorizes all important information.
            </p>
          </div>
          <div className="bg-card p-6 rounded-lg border">
            <Shield className="w-10 h-10 text-primary mb-4" />
            <h3 className="text-lg font-semibold mb-2">Secure & Private</h3>
            <p className="text-muted-foreground">
              Your financial data is encrypted and protected. We prioritize your privacy and security.
            </p>
          </div>
          <div className="bg-card p-6 rounded-lg border">
            <Sparkles className="w-10 h-10 text-primary mb-4" />
            <h3 className="text-lg font-semibold mb-2">Real-time Insights</h3>
            <p className="text-muted-foreground">
              Get instant analysis and categorization of your expenses with AI-powered insights.
            </p>
          </div>
        </div>

        {/* Open Source Banner */}
        <div className="mt-20 text-center">
          <a
            href="https://github.com/babdulhakim2/expense-bot"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center space-x-2 text-muted-foreground hover:text-primary transition-colors"
          >
            <Github className="w-5 h-5" />
            <span>Open Source on GitHub</span>
          </a>
        </div>
      </div>
    </main>
  );
}