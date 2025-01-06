'use client';

import { useToast } from "@/hooks/use-toast";
import { BusinessService, type Business } from '@/lib/firebase/services/business-service';
import { useSession } from "next-auth/react";
import { useEffect, useState } from 'react';

export function BusinessSettings() {
  const { data: session } = useSession();
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [business, setBusiness] = useState<Partial<Business>>({
    name: '',
    type: '',
  });

  useEffect(() => {
    const fetchBusiness = async () => {
      if (session?.user?.id) {
        try {
          const userBusinesses = await BusinessService.getUserBusinesses(session.user.id);
          if (userBusinesses.length > 0) {
            setBusiness(userBusinesses[0]);
          }
        } catch (error) {
          console.error('Failed to fetch business:', error);
          toast({
            title: "Error",
            description: "Failed to load business data",
            variant: "destructive",
          });
        }
      }
    };
    
    fetchBusiness();
  }, [session]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!session?.user?.id || !business.id) return;

    setLoading(true);
    try {
      await BusinessService.updateBusiness(business.id, {
        name: business.name,
        type: business.type,
      });

      toast({
        title: "Success",
        description: "Business settings updated successfully",
      });
    } catch (error) {
      console.error('Failed to update business:', error);
      toast({
        title: "Error",
        description: "Failed to update business settings",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setBusiness(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="p-6">
          <h2 className="text-lg font-semibold mb-4">Business Profile</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Business Name</label>
              <input 
                type="text"
                name="name"
                value={business.name || ''}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="Enter business name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Business Type</label>
              <select 
                name="type"
                value={business.type || ''}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="">Select a type</option>
                <option value="retail">Retail</option>
                <option value="technology">Technology</option>
                <option value="services">Services</option>
                <option value="manufacturing">Manufacturing</option>
              </select>
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
    </form>
  );
} 