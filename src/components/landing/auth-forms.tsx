"use client";

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';
import { auth } from '@/lib/firebase';
import { RecaptchaVerifier, signInWithPhoneNumber } from 'firebase/auth';
import { ArrowRight, Flag } from 'lucide-react';
import { signIn, useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import React, { FormEvent, useEffect, useState } from 'react';

declare global {
  interface Window {
    recaptchaVerifier: RecaptchaVerifier;
  }
}

type OTPInputProps = {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
};

function OTPInput({ value, onChange, disabled }: OTPInputProps) {
  const inputRefs = Array(6).fill(0).map(() => React.useRef<HTMLInputElement>(null));

  const handleChange = (index: number, inputValue: string) => {
    if (!/^\d*$/.test(inputValue)) return;

    const newValue = value.split('');
    newValue[index] = inputValue;
    const combinedValue = newValue.join('');
    onChange(combinedValue);

    // Auto-focus next input
    if (inputValue && index < 5) {
      inputRefs[index + 1].current?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !value[index] && index > 0) {
      inputRefs[index - 1].current?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/[^\d]/g, '').slice(0, 6);
    onChange(pastedData);
    
    // Focus appropriate input after paste
    const lastIndex = Math.min(pastedData.length, 5);
    inputRefs[lastIndex].current?.focus();
  };

  return (
    <div className="flex justify-between gap-2">
      {Array(6).fill(0).map((_, index) => (
        <input
          key={index}
          ref={inputRefs[index]}
          type="text"
          maxLength={1}
          className="w-12 h-12 text-center text-lg font-semibold rounded-md border border-input bg-transparent focus:border-primary focus:ring-1 focus:ring-primary disabled:opacity-50"
          value={value[index] || ''}
          onChange={(e) => handleChange(index, e.target.value)}
          onKeyDown={(e) => handleKeyDown(index, e)}
          onPaste={handlePaste}
          disabled={disabled}
        />
      ))}
    </div>
  );
}

export function AuthForms() {
  // Move ALL hooks to the top, before any conditional returns
  const { data: session } = useSession();
  const router = useRouter();
  const [step, setStep] = useState<1 | 2>(1);
  const [phone, setPhone] = useState<string>('');
  const [verificationCode, setVerificationCode] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [confirmationResult, setConfirmationResult] = useState<any>(null);
  const [error, setError] = useState<string>('');
  const [cooldownTime, setCooldownTime] = useState<number | null>(null);
  const { toast } = useToast();

  // useEffect hooks should also be at the top level
  useEffect(() => {
    return () => {
      if (window.recaptchaVerifier) {
        try {
          window.recaptchaVerifier.clear();
          window.recaptchaVerifier = undefined as unknown as RecaptchaVerifier;
        } catch (error) {
          console.error('Error clearing reCAPTCHA:', error);
        }
      }
      const iframes = document.querySelectorAll('iframe[src*="recaptcha"]');
      iframes.forEach(iframe => iframe.remove());
    };
  }, []);

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

  // Now we can have conditional renders
  if (session) {
    return (
      null
    );
  }

  const formatTimeRemaining = (milliseconds: number): string => {
    const seconds = Math.ceil(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const initializeRecaptcha = async () => {
    try {
      // Clear any existing verifier
      if (window.recaptchaVerifier) {
        try {
          await window.recaptchaVerifier.clear();
          window.recaptchaVerifier = undefined as unknown as RecaptchaVerifier;
        } catch (error) {
          console.error('Error clearing reCAPTCHA:', error);
        }
      }

      // Remove any existing reCAPTCHA iframes
      const iframes = document.querySelectorAll('iframe[src*="recaptcha"]');
      iframes.forEach(iframe => iframe.remove());

      // Create new verifier
      window.recaptchaVerifier = new RecaptchaVerifier(
        'recaptcha-container',
        {
          size: 'invisible',
          callback: (response: any) => {
            console.log('reCAPTCHA resolved:', response);
          },
          'expired-callback': () => {
            setError('reCAPTCHA expired. Please try again.');
            if (window.recaptchaVerifier) {
              try {
                window.recaptchaVerifier.clear();
                window.recaptchaVerifier = undefined as unknown as RecaptchaVerifier;
              } catch (error) {
                console.error('Error clearing reCAPTCHA:', error);
              }
            }
            toast({
              title: "reCAPTCHA Expired",
              description: "Please try again",
              variant: "destructive",
            });
          }
        },
        auth
      );

      // Render the reCAPTCHA
      await window.recaptchaVerifier.render();
    } catch (error: any) {
      console.error('Error initializing reCAPTCHA:', error);
      throw new Error(error.message || 'Error initializing reCAPTCHA');
    }
  };
  

  const formatPhoneNumber = (number: string): string => {
    let cleaned = number.replace(/[^\d+]/g, '');
    if (!cleaned.startsWith('+')) {
      cleaned = '+44' + cleaned;
    }
    return cleaned;
  };

  const formatPhoneDisplay = (input: string): string => {
    const numbers = input.replace(/[^\d]/g, '');
    if (numbers.length <= 4) return numbers;
    if (numbers.length <= 7) return `${numbers.slice(0, 4)} ${numbers.slice(4)}`;
    return `${numbers.slice(0, 4)} ${numbers.slice(4, 7)} ${numbers.slice(7)}`;
  };

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const input = e.target.value.replace(/[^\d]/g, '');
    setPhone(input);
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
          window.recaptchaVerifier = undefined as unknown as RecaptchaVerifier;
        } catch (error) {
          console.error('Error clearing reCAPTCHA:', error);
        }
      }

      // Remove any existing reCAPTCHA iframes
      const iframes = document.querySelectorAll('iframe[src*="recaptcha"]');
      iframes.forEach(iframe => iframe.remove());

      await initializeRecaptcha();
      
      if (!window.recaptchaVerifier) {
        throw new Error('reCAPTCHA not initialized');
      }

      console.log('Sending verification code to:', formattedPhone);
      
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
        try {
          window.recaptchaVerifier.clear();
          window.recaptchaVerifier = undefined as unknown as RecaptchaVerifier;
        } catch (error) {
          console.error('Error clearing reCAPTCHA:', error);
        }
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
      if (!confirmationResult) {
        throw new Error('No confirmation result found');
      }

      const result = await confirmationResult.confirm(verificationCode);
      const idToken = await result.user.getIdToken();

      const response = await signIn('credentials', {
        token: idToken,
        redirect: false,
      });

      if (response?.error) {
        throw new Error(response.error);
      }

      toast({
        title: "Success",
        description: "Phone number verified successfully!",
      });

      router.replace('/dashboard');
    // window.location.href = '/dashboard';
    } catch (error: any) {
      console.error('Error verifying code:', error);
      const errorMessage = error.code === 'auth/invalid-verification-code' 
        ? 'Invalid verification code. Please try again.'
        : error.message || 'Error verifying code';
        
      toast({
        title: "Verification Failed",
        description: errorMessage,
        variant: "destructive",
      });
      setError(errorMessage);
      // Add a manual redirect link when automatic redirect fails
      toast({
        title: "Verification Success",
        description: (
          <div className="space-y-2">
            <p>{errorMessage}</p>
            <a 
              href="/dashboard" 
              className="text-primary hover:underline block"
            >
              Click here to go to dashboard manually →
            </a>
          </div>
        ),
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center w-full mt-8">
      {step === 1 && (
        <form onSubmit={handlePhoneSubmit} className="w-full max-w-md space-y-4 mx-auto">
          <div className="flex space-x-2">
            <div className="relative flex-1">
              <div className="absolute left-3 top-2.5 flex items-center gap-1.5">
                <Flag className="w-4 h-4 text-primary" />
                <span className="text-sm font-medium text-muted-foreground">+44</span>
              </div>
              <Input
                type="tel"
                placeholder="7911 123456"
                className="pl-20"
                value={formatPhoneDisplay(phone)}
                onChange={handlePhoneChange}
                disabled={loading}
                maxLength={13} // Accounts for spaces in formatting
              />
            </div>
            <Button 
              type="submit" 
              disabled={loading || (cooldownTime ? Date.now() < cooldownTime : undefined)}
              className="min-w-[120px]"
            >
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
        <form onSubmit={handleOTPSubmit} className="w-full max-w-md space-y-6 mx-auto">
          <div className="space-y-4">
            <div className="text-center">
              <h3 className="text-lg font-semibold">Verify your phone</h3>
              <p className="text-sm text-muted-foreground mt-1">
                Enter the 6-digit code sent to {formatPhoneNumber(phone)}
              </p>
            </div>
            
            <OTPInput
              value={verificationCode}
              onChange={setVerificationCode}
              disabled={loading}
            />
          </div>

          <div className="space-y-4">
            <Button type="submit" disabled={loading || verificationCode.length !== 6} className="w-full">
              {loading ? (
                "Verifying..."
              ) : (
                <>
                  Verify Code <ArrowRight className="ml-2 h-4 w-4" />
                </>
              )}
            </Button>

            <div className="text-center">
              <button
                type="button"
                onClick={() => {
                  setStep(1);
                  setVerificationCode('');
                  setError('');
                }}
                className="text-sm text-primary hover:underline disabled:opacity-50"
                disabled={loading}
              >
                Use a different number
              </button>
            </div>
          </div>

          {error && (
            <p className="text-sm text-destructive text-center">{error}</p>
          )}
        </form>
      )}
    </div>
  );
} 