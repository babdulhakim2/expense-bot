'use client';

import { UserIcon, PhoneIcon, AtSignIcon, ShieldIcon } from "lucide-react";
import { useState, useEffect } from 'react';
import { useSession } from "next-auth/react";
import { UserService, type User } from '@/lib/firebase/services/user-service';
import { useToast } from "@/hooks/use-toast";
import { PhoneNumberInput } from "@/components/shared/phone-input";

type ExtendedSession = {
  user?: {
    id: string;
    name?: string | null;
    email?: string | null;
    phoneNumber?: string | null;
  } | null;
}

export function ProfileSettings() {
  const { data: session } = useSession() as { data: ExtendedSession };
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [userData, setUserData] = useState<Partial<User>>({
    name: '',
    email: '',
    phoneNumber: '',
    role: '',
  });

  useEffect(() => {
    const fetchUser = async () => {
      if (session?.user?.id) {
        try {
          const user = await UserService.getUser(session.user.id);
          if (user) {
            setUserData({
              name: user.name || session?.user?.name || '',
              email: user.email || session?.user?.email || '',
              phoneNumber: user.phoneNumber || '',
              role: user.role || '',
            });
          } else if (session?.user) {
            // If no user document exists yet, use session data
            setUserData({
              name: session.user.name || '',
              email: session.user.email || '',
            });
          }
        } catch (error) {
          console.error('Failed to fetch user:', error);
          toast({
            title: "Error",
            description: "Failed to load user data",
            variant: "destructive",
          });
        }
      }
    };

    fetchUser();
  }, [session]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!session?.user?.id) return;

    setLoading(true);
    try {
      await UserService.createOrUpdateUser({
        id: session.user.id,
        ...userData,
      });

      toast({
        title: "Success",
        description: "Profile updated successfully",
      });
    } catch (error) {
      console.error('Failed to update profile:', error);
      toast({
        title: "Error",
        description: "Failed to update profile",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setUserData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handlePhoneChange = (value: string) => {
    setUserData(prev => ({
      ...prev,
      phoneNumber: value
    }));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="p-6">
          <h2 className="text-lg font-semibold mb-4">Personal Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Full Name</label>
              <input 
                type="text"
                name="name"
                value={userData.name || ''}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="Enter your name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Email Address</label>
              <input 
                type="email"
                name="email"
                value={userData.email || ''}
                readOnly
                className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                placeholder="Enter your email"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Phone Number</label>
              <PhoneNumberInput
                value={userData.phoneNumber || ''}
                onChange={handlePhoneChange}
                className="w-full"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Role</label>
              <select 
                name="role"
                value={userData.role || ''}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="">Select a role</option>
                <option value="Business Owner">Business Owner</option>
                <option value="Accountant">Accountant</option>
                <option value="Manager">Manager</option>
                <option value="Employee">Employee</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <button 
          type="submit"
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </form>
  );
} 