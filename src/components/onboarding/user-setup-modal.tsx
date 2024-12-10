'use client';

import { useToast } from '@/hooks/use-toast';
import { db } from '@/lib/firebase/firebase';
import { collection, doc, setDoc } from 'firebase/firestore';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

type SetupStep = 'profile' | 'business';

interface UserProfile {
  name: string;
  email: string;
}

interface BusinessDetails {
  name: string;
  type: string;
}

export function UserSetupModal() {
  const router = useRouter();
  const { data: session, update } = useSession();
  const { toast } = useToast();
  const [step, setStep] = useState<SetupStep>('profile');
  
  const [profile, setProfile] = useState<UserProfile>({
    name: '',
    email: '',
  });

  const [business, setBusiness] = useState<BusinessDetails>({
    name: '',
    type: 'small_business',
  });

  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      // Create/update user document in Firestore
      const userRef = doc(db, 'users', session?.user?.id || '');
      await setDoc(userRef, {
        name: profile.name,
        email: profile.email,
        phoneNumber: session?.user?.phoneNumber,
        updatedAt: new Date(),
      }, { merge: true });

      // Update session with new user data
      await update({
        ...session,
        user: {
          ...session?.user,
          name: profile.name,
          email: profile.email,
        },
      });

      setStep('business');
    } catch (error) {
      console.error('Error saving profile:', error);
      toast({
        title: 'Error',
        description: 'Failed to save profile information. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleBusinessSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      // Create business in user's subcollection
      const businessRef = doc(collection(db, 'users', session?.user?.id || '', 'businesses'));
      await setDoc(businessRef, {
        id: businessRef.id,
        name: business.name,
        type: business.type,
        createdAt: new Date(),
        updatedAt: new Date(),
      });

      toast({
        title: 'Success',
        description: 'Your profile has been set up successfully!',
      });

      router.push('/dashboard');
    } catch (error) {
      console.error('Error saving business:', error);
      toast({
        title: 'Error',
        description: 'Failed to save business information. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
        {step === 'profile' ? (
          <form onSubmit={handleProfileSubmit} className="space-y-4">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold">Complete Your Profile</h2>
              <p className="text-gray-600">Please provide your information</p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={profile.name}
                  onChange={(e) => setProfile(p => ({ ...p, name: e.target.value }))}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="Enter your full name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Email Address</label>
                <input
                  type="email"
                  required
                  value={profile.email}
                  onChange={(e) => setProfile(p => ({ ...p, email: e.target.value }))}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="Enter your email"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {isSubmitting ? 'Saving...' : 'Continue'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleBusinessSubmit} className="space-y-4">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold">Set Up Your Business</h2>
              <p className="text-gray-600">Tell us about your business</p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Business Name</label>
                <input
                  type="text"
                  required
                  value={business.name}
                  onChange={(e) => setBusiness(b => ({ ...b, name: e.target.value }))}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="Enter business name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Business Type</label>
                <select
                  value={business.type}
                  onChange={(e) => setBusiness(b => ({ ...b, type: e.target.value }))}
                  className="w-full px-3 py-2 border rounded-md"
                >
                  <option value="small_business">Small Business</option>
                  <option value="freelancer">Freelancer</option>
                  <option value="startup">Startup</option>
                  <option value="enterprise">Enterprise</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {isSubmitting ? 'Creating Business...' : 'Complete Setup'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
} 