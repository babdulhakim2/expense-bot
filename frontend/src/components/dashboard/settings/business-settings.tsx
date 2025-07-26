'use client';

import { useToast } from "@/hooks/use-toast";
import { BusinessService, type Business } from '@/lib/firebase/services/business-service';
import { UserService, type User } from '@/lib/firebase/services/user-service';
import { useSession } from "next-auth/react";
import { useEffect, useState } from 'react';
import { PhoneNumberInput } from "@/components/shared/phone-input";

type ExtendedSession = {
  user?: {
    id: string;
    name?: string | null;
    email?: string | null;
    phoneNumber?: string | null;
  } | null;
}

export function BusinessSettings() {
  const { data: session } = useSession() as { data: ExtendedSession };
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [userData, setUserData] = useState<Partial<User>>({
    name: '',
    email: '',
    phoneNumber: '',
    role: '',
  });
  const [business, setBusiness] = useState<Partial<Business>>({
    name: '',
    type: '',
    location: '',
    currency: '',
    businessNumber: '',
  });
  const [initialLoading, setInitialLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      if (session?.user?.id) {
        setInitialLoading(true);
        try {
          // Fetch user data
          const user = await UserService.getUser(session.user.id);
          if (user) {
            setUserData({
              name: user.name || session?.user?.name || '',
              email: user.email || session?.user?.email || '',
              phoneNumber: user.phoneNumber || '',
              role: user.role || '',
            });
          }

          // Fetch business data
          const userBusinesses = await BusinessService.getUserBusinesses(session.user.id);
          if (userBusinesses.length > 0) {
            const businessData = userBusinesses[0];
            console.log('Loaded business data:', businessData); // Debug log
            setBusiness({
              id: businessData.id,
              name: businessData.name,
              type: businessData.type,
              location: businessData.location || '',
              currency: businessData.currency || '',
              businessNumber: businessData.businessNumber || '',
            });
          }
        } catch (error) {
          console.error('Failed to fetch data:', error);
          toast({
            title: "Error",
            description: "Failed to load settings data",
            variant: "destructive",
          });
        } finally {
          setInitialLoading(false);
        }
      }
    };
    
    fetchData();
  }, [session, toast]);

  // Add a debug effect to monitor business state changes
  useEffect(() => {
    console.log('Current business state:', business);
  }, [business]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!session?.user?.id) return;

    setLoading(true);
    try {
      // Update user profile
      if (userData.name || userData.phoneNumber || userData.role) {
        await UserService.createOrUpdateUser({
          id: session.user.id,
          ...userData,
        });
      }

      // Update business if business ID exists
      if (business.id) {
        // Only include fields that have values
        const businessUpdate: Partial<Business> = {};
        
        if (business.name) businessUpdate.name = business.name;
        if (business.type) businessUpdate.type = business.type;
        if (business.location) businessUpdate.location = business.location;
        if (business.currency) businessUpdate.currency = business.currency;
        if (business.businessNumber) businessUpdate.businessNumber = business.businessNumber;

        await BusinessService.updateBusiness(business.id, businessUpdate);
      }

      toast({
        title: "Success",
        description: "Settings updated successfully",
      });
    } catch (error) {
      console.error('Failed to update settings:', error);
      toast({
        title: "Error",
        description: "Failed to update settings",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleUserChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setUserData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleBusinessChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setBusiness(prev => ({
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
      {initialLoading ? (
        <div className="flex items-center justify-center p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <>
          {/* Personal Information Section */}
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
                    onChange={handleUserChange}
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
                    onChange={handleUserChange}
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

          {/* Business Information Section */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="p-6">
              <h2 className="text-lg font-semibold mb-4">Business Information</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Business Name</label>
                  <input 
                    type="text"
                    name="name"
                    value={business.name || ''}
                    onChange={handleBusinessChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    placeholder="Enter business name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Business Type</label>
                  <select 
                    name="type"
                    value={business.type || ''}
                    onChange={handleBusinessChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="">Select a type</option>
                    <option value="retail">Retail</option>
                    <option value="technology">Technology</option>
                    <option value="services">Services</option>
                    <option value="manufacturing">Manufacturing</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Business Location</label>
                  <input 
                    type="text"
                    name="location"
                    value={business.location || ''}
                    onChange={handleBusinessChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    placeholder="Enter business location"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Currency</label>
                  <select 
                    name="currency"
                    value={business.currency || ''}
                    onChange={handleBusinessChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="">Select currency</option>
                    <option value="USD">USD - US Dollar</option>
                    <option value="GBP">GBP - British Pound</option>
                    <option value="CAD">CAD - Canadian Dollar</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Business Number (Optional)</label>
                  <input 
                    type="text"
                    name="businessNumber"
                    value={business.businessNumber || ''}
                    onChange={handleBusinessChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    placeholder="Enter business registration number"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Save Button */}
          <div className="flex justify-end">
            <button 
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </>
      )}
    </form>
  );
} 