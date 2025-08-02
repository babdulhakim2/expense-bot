"use client";

import { PhoneNumberInput } from "@/components/shared/phone-input";
import { useToast } from "@/hooks/use-toast";
import { BUSINESS_CATEGORIES } from "@/lib/constants/business-categories";
import {
  SUPPORTED_CURRENCIES
} from "@/lib/constants/currency";
import {
  BusinessService,
  type Business,
} from "@/lib/firebase/services/business-service";
import { UserService, type User } from "@/lib/firebase/services/user-service";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";

type ExtendedSession = {
  user?: {
    id: string;
    name?: string | null;
    email?: string | null;
    phoneNumber?: string | null;
  } | null;
};

export function BusinessSettings() {
  const { data: session } = useSession() as { data: ExtendedSession };
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [userData, setUserData] = useState<Partial<User>>({
    name: "",
    email: "",
    phoneNumber: "",
    role: "",
  });
  const [business, setBusiness] = useState<Partial<Business>>({
    name: "",
    type: "",
    location: "",
    currency: "",
    businessNumber: "",
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
              name: user.name || session?.user?.name || "",
              email: user.email || session?.user?.email || "",
              phoneNumber: user.phoneNumber || "",
              role: user.role || "",
            });
          }

          // Fetch business data
          const userBusinesses = await BusinessService.getUserBusinesses(
            session.user.id
          );
          if (userBusinesses.length > 0) {
            const businessData = userBusinesses[0];
            console.log("Loaded business data:", businessData); // Debug log
            setBusiness({
              id: businessData.id,
              name: businessData.name,
              type: businessData.type,
              location: businessData.location || "",
              currency: businessData.currency || "",
              businessNumber: businessData.businessNumber || "",
            });
          }
        } catch (error) {
          console.error("Failed to fetch data:", error);
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
    console.log("Current business state:", business);
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
        if (business.businessNumber)
          businessUpdate.businessNumber = business.businessNumber;

        await BusinessService.updateBusiness(business.id, businessUpdate);
      }

      toast({
        title: "Success",
        description: "Settings updated successfully",
      });
    } catch (error) {
      console.error("Failed to update settings:", error);
      toast({
        title: "Error",
        description: "Failed to update settings",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleUserChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    setUserData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleBusinessChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    setBusiness((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handlePhoneChange = (value: string) => {
    setUserData((prev) => ({
      ...prev,
      phoneNumber: value,
    }));
  };

  // Helper function to get business category info
  const getBusinessCategoryInfo = (categoryId?: string) => {
    return BUSINESS_CATEGORIES.find((cat) => cat.id === categoryId);
  };

  // Helper function to get currency info
  const getCurrencyInfo = (currencyCode?: string) => {
    return SUPPORTED_CURRENCIES.find((curr) => curr.code === currencyCode);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {initialLoading ? (
        <div className="flex items-center justify-center p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <>
          {/* Current Business Overview */}
          {business.name && (
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200 shadow-sm">
              <div className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-4">
                      <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-2xl">
                          {getBusinessCategoryInfo(business.type)?.icon || "🏢"}
                        </span>
                      </div>
                      <div>
                        <h1 className="text-2xl font-bold text-gray-900">
                          {business.name}
                        </h1>
                        <p className="text-sm text-gray-600">
                          {getBusinessCategoryInfo(business.type)?.label ||
                            business.type}
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {business.location && (
                        <div className="flex items-center space-x-2 text-sm text-gray-600">
                          <span className="text-gray-400">📍</span>
                          <span>{business.location}</span>
                        </div>
                      )}

                      {business.currency && (
                        <div className="flex items-center space-x-2 text-sm text-gray-600">
                          <span className="text-gray-400">💰</span>
                          <span>
                            {getCurrencyInfo(business.currency)?.name ||
                              business.currency}
                            {getCurrencyInfo(business.currency)?.symbol &&
                              ` (${
                                getCurrencyInfo(business.currency)?.symbol
                              })`}
                          </span>
                        </div>
                      )}

                      {business.businessNumber && (
                        <div className="flex items-center space-x-2 text-sm text-gray-600">
                          <span className="text-gray-400">🆔</span>
                          <span>{business.businessNumber}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="ml-4">
                    <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                      Active Business
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Personal Information Section */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="p-6">
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                  <span className="text-lg">👤</span>
                </div>
                <h2 className="text-lg font-semibold text-gray-900">
                  Personal Information
                </h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Full Name
                  </label>
                  <input
                    type="text"
                    name="name"
                    value={userData.name || ""}
                    onChange={handleUserChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    placeholder="Enter your name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={userData.email || ""}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                    placeholder="Enter your email"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Phone Number
                  </label>
                  <PhoneNumberInput
                    value={userData.phoneNumber || ""}
                    onChange={handlePhoneChange}
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Role</label>
                  <select
                    name="role"
                    value={userData.role || ""}
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
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                  <span className="text-lg">🏢</span>
                </div>
                <h2 className="text-lg font-semibold text-gray-900">
                  Business Information
                </h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Business Name
                  </label>
                  <input
                    type="text"
                    name="name"
                    value={business.name || ""}
                    onChange={handleBusinessChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    placeholder="Enter business name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Business Type
                  </label>
                  <select
                    name="type"
                    value={business.type || ""}
                    onChange={handleBusinessChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="">Select a type</option>
                    {BUSINESS_CATEGORIES.map((category) => (
                      <option key={category.id} value={category.id}>
                        {category.icon} {category.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Business Location
                  </label>
                  <input
                    type="text"
                    name="location"
                    value={business.location || ""}
                    onChange={handleBusinessChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    placeholder="Enter business location"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Currency
                  </label>
                  <select
                    name="currency"
                    value={business.currency || ""}
                    onChange={handleBusinessChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="">Select currency</option>
                    {SUPPORTED_CURRENCIES.map((currency) => (
                      <option key={currency.code} value={currency.code}>
                        {currency.code} - {currency.name} ({currency.symbol})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Business Number (Optional)
                  </label>
                  <input
                    type="text"
                    name="businessNumber"
                    value={business.businessNumber || ""}
                    onChange={handleBusinessChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    placeholder="Enter business registration number"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Save Button */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="p-6">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  <p>Make sure all information is accurate before saving.</p>
                  <p className="text-xs mt-1">
                    Changes will be applied immediately to your business
                    profile.
                  </p>
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors duration-200 font-medium"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Saving...</span>
                    </>
                  ) : (
                    <>
                      <span>💾</span>
                      <span>Save Changes</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </form>
  );
}
