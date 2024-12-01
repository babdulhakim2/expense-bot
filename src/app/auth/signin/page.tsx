'use client';

import { signIn } from 'next-auth/react';
import { auth } from '@/lib/firebase';
import { signInWithPhoneNumber, RecaptchaVerifier } from 'firebase/auth';
import { useState } from 'react';

export default function SignIn() {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [confirmationResult, setConfirmationResult] = useState<any>(null);
  const [error, setError] = useState('');

  const initializeRecaptcha = () => {
    if (!(window as any).recaptchaVerifier) {
      (window as any).recaptchaVerifier = new RecaptchaVerifier(auth, 'recaptcha-container', {
        'size': 'normal',
        'callback': () => {
          // reCAPTCHA solved
        }
      });
    }
  };

  const sendVerificationCode = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      initializeRecaptcha();
      const confirmation = await signInWithPhoneNumber(
        auth, 
        phoneNumber, 
        (window as any).recaptchaVerifier
      );
      setConfirmationResult(confirmation);
    } catch (error) {
      console.error('Error sending code:', error);
      setError('Error sending verification code');
    }
  };

  const verifyCode = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const result = await confirmationResult.confirm(verificationCode);
      const idToken = await result.user.getIdToken();
      
      const response = await signIn('credentials', {
        token: idToken,
        redirect: true,
        callbackUrl: '/dashboard'
      });

      if (response?.error) {
        setError('Authentication failed');
      }
    } catch (error) {
      console.error('Error verifying code:', error);
      setError('Invalid verification code');
    }
  };

  return (
    <div className="container mx-auto p-4">
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-6">
        <h1 className="text-2xl font-bold mb-4">Sign In</h1>
        
        {!confirmationResult ? (
          <form onSubmit={sendVerificationCode} className="space-y-4">
            <div>
              <label className="block mb-2">Phone Number</label>
              <input
                type="tel"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                className="w-full p-2 border rounded"
                placeholder="+1234567890"
                required
              />
            </div>
            <div id="recaptcha-container"></div>
            <button
              type="submit"
              className="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600"
            >
              Send Code
            </button>
          </form>
        ) : (
          <form onSubmit={verifyCode} className="space-y-4">
            <div>
              <label className="block mb-2">Verification Code</label>
              <input
                type="text"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value)}
                className="w-full p-2 border rounded"
                required
              />
            </div>
            <button
              type="submit"
              className="w-full bg-green-500 text-white p-2 rounded hover:bg-green-600"
            >
              Verify Code
            </button>
          </form>
        )}
        
        {error && (
          <div className="mt-4 text-red-500">
            {error}
          </div>
        )}
      </div>
    </div>
  );
} 