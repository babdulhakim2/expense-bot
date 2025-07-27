"use client";

import { useBusiness } from "@/app/providers/BusinessProvider";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "@/hooks/use-toast";
import { BUSINESS_CATEGORIES } from "@/lib/constants/business-categories";
import { Business, GoogleDriveConfig } from "@/lib/firebase/services/business-service";
import { ArrowRight, Building, CheckCircle, Loader2, Plus } from "lucide-react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { signOut } from "next-auth/react";
import { GoogleDriveSetup } from "@/components/setup/google-drive-setup";

interface NewBusinessData {
  name: string;
  type: string;
  location: string;
}

export default function SetupPage() {
  const router = useRouter();
  const { data: session, status } = useSession();
  const {
    currentBusiness,
    isInitialized,
    loadingStates,
    selectBusiness,
    createAndSelectBusiness,
    getUserBusinesses,
  } = useBusiness();

  const [userBusinesses, setUserBusinesses] = useState<Business[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showGoogleDriveSetup, setShowGoogleDriveSetup] = useState(false);
  const [selectedBusinessForGDrive, setSelectedBusinessForGDrive] = useState<Business | null>(null);
  const [newBusinessData, setNewBusinessData] = useState<NewBusinessData>({
    name: "",
    type: "",
    location: "",
  });

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/");
    }
  }, [status, router]);

  // Check for Google Drive connection success
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('google_drive') === 'connected') {
      toast({
        title: "Google Drive Connected!",
        description: "Your Google Drive is now connected to your business.",
      });
      // Remove the query parameter from URL
      const newUrl = window.location.pathname;
      window.history.replaceState({}, '', newUrl);
    }
  }, []);

  useEffect(() => {
    async function loadUserBusinesses() {
      if (!(session?.user as any)?.id || !isInitialized) return; // eslint-disable-line @typescript-eslint/no-explicit-any

      try {
        const userBiz = await getUserBusinesses();
        setUserBusinesses(userBiz);

        // If no businesses, show create form immediately
        if (userBiz.length === 0) {
          setShowCreateForm(true);
        }
      } catch (error) {
        console.error("Failed to load user businesses:", error);
      } finally {
      }
    }

    loadUserBusinesses();
  }, [
    (session?.user as any)?.id, // eslint-disable-line @typescript-eslint/no-explicit-any
    isInitialized,
    currentBusiness,
    getUserBusinesses,
    router,
  ]);

  const handleBusinessSelect = async (business: Business) => {
    try {
      await selectBusiness(business);
      toast({
        title: "Business Selected",
        description: `Now managing ${business.name}`,
      });
      
      // Show Google Drive setup if not already connected
      if (!business.googleDrive?.accessToken) {
        setSelectedBusinessForGDrive(business);
        setShowGoogleDriveSetup(true);
      } else {
        router.push("/dashboard");
      }
    } catch (error) {
      console.error("Failed to select business:", error);
      toast({
        title: "Error",
        description: "Failed to select business",
        variant: "destructive",
      });
    }
  };

  const handleCreateBusiness = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!newBusinessData.name || !newBusinessData.type) return;

    try {
      const newBusiness = await createAndSelectBusiness({
        name: newBusinessData.name,
        type: newBusinessData.type,
        location: newBusinessData.location,
      });

      toast({
        title: "Success!",
        description: `Created ${newBusiness.name}`,
      });

      // Refetch user businesses to show updated list
      const updatedBusinesses = await getUserBusinesses();
      setUserBusinesses(updatedBusinesses);

      // Reset form
      setNewBusinessData({ name: "", type: "", location: "" });
      setShowCreateForm(false);

      // Show Google Drive setup for new business
      setSelectedBusinessForGDrive(newBusiness);
      setShowGoogleDriveSetup(true);
    } catch (error) {
      console.error("Failed to create business:", error);
      toast({
        title: "Error",
        description: "Failed to create business",
        variant: "destructive",
      });
    }
  };

  const handleGoogleDriveComplete = (config: GoogleDriveConfig) => {
    toast({
      title: "Setup Complete!",
      description: "Your business is ready to process expenses.",
    });
    router.push("/dashboard");
  };

  const handleGoogleDriveSkip = () => {
    router.push("/dashboard");
  };

  // Loading state
  if (status === "loading" || !isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto" />
          <div className="space-y-2">
            <h2 className="text-xl font-semibold text-gray-900">
              Setting up your workspace...
            </h2>
            <p className="text-gray-600">
              Please wait while we prepare your business dashboard
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Not authenticated
  if (status === "unauthenticated") {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {showGoogleDriveSetup && selectedBusinessForGDrive ? (
          <div className="bg-white rounded-lg shadow-sm border p-6 space-y-6">
            {/* Header */}
            <div className="text-center space-y-2">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto">
                <Building className="h-8 w-8 text-primary" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900">
                Setup Complete! 🎉
              </h1>
              <p className="text-gray-600">
                {selectedBusinessForGDrive.name} is ready. Would you like to connect Google Drive?
              </p>
            </div>

            <GoogleDriveSetup 
              businessId={selectedBusinessForGDrive.id}
              onComplete={handleGoogleDriveComplete}
              onSkip={handleGoogleDriveSkip}
            />
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm border p-6 space-y-6">
            {/* Header */}
            <div className="text-center space-y-2">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto">
                <Building className="h-8 w-8 text-primary" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900">
                {userBusinesses.length > 0 && !showCreateForm
                  ? "Select Business"
                  : "Create Your Business"}
              </h1>
              <p className="text-gray-600">
                {userBusinesses.length > 0 && !showCreateForm
                  ? "Choose which business you'd like to manage"
                  : "Set up your business profile to get started with ExpenseBot"}
              </p>
            </div>

          {/* Multiple businesses - selection view */}
          {userBusinesses.length > 0 && !showCreateForm && (
            <div className="space-y-4">
              <div className="space-y-2">
                {userBusinesses.map((business) => {
                  const category =
                    BUSINESS_CATEGORIES.find(
                      (cat) => cat.id === business.type
                    ) || BUSINESS_CATEGORIES[0];

                  return (
                    <button
                      key={business.id}
                      onClick={() => handleBusinessSelect(business)}
                      disabled={loadingStates.selecting}
                      className="w-full p-4 border border-gray-200 rounded-lg hover:border-primary hover:bg-primary/5 transition-colors text-left group disabled:opacity-50"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                            <span className="text-lg">{category.icon}</span>
                          </div>
                          <div>
                            <div className="font-medium text-gray-900">
                              {business.name}
                            </div>
                            <div className="text-sm text-gray-500">
                              {category.label}
                            </div>
                          </div>
                        </div>
                        {loadingStates.selecting ? (
                          <Loader2 className="h-4 w-4 animate-spin text-primary" />
                        ) : (
                          <ArrowRight className="h-4 w-4 text-gray-400 group-hover:text-primary transition-colors" />
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* Create new business option */}
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t border-gray-200" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-white px-2 text-gray-500">Or</span>
                </div>
              </div>

              <Button
                variant="outline"
                onClick={() => setShowCreateForm(true)}
                className="w-full h-12"
              >
                <Plus className="h-4 w-4 mr-2" />
                Create New Business
              </Button>
            </div>
          )}

          {/* Create business form */}
          {(userBusinesses.length === 0 || showCreateForm) && (
            <form onSubmit={handleCreateBusiness} className="space-y-4">
              {/* Back button for multi-business users */}
              {userBusinesses.length > 0 && (
                <div className="text-center">
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowCreateForm(false)}
                    className="text-sm"
                  >
                    ← Back to business selection
                  </Button>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="businessName">Business Name *</Label>
                <input
                  id="businessName"
                  type="text"
                  value={newBusinessData.name}
                  onChange={(e) =>
                    setNewBusinessData((prev) => ({
                      ...prev,
                      name: e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50"
                  placeholder="Enter your business name"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="businessType">Business Category *</Label>
                <Select
                  value={newBusinessData.type}
                  onValueChange={(value) =>
                    setNewBusinessData((prev) => ({ ...prev, type: value }))
                  }
                >
                  <SelectTrigger className="h-10">
                    <SelectValue placeholder="Select your business category" />
                  </SelectTrigger>
                  <SelectContent>
                    {BUSINESS_CATEGORIES.map((category) => (
                      <SelectItem key={category.id} value={category.id}>
                        <span className="flex items-center gap-2">
                          {category.icon} {category.label}
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="businessLocation">Location (Optional)</Label>
                <input
                  id="businessLocation"
                  type="text"
                  value={newBusinessData.location}
                  onChange={(e) =>
                    setNewBusinessData((prev) => ({
                      ...prev,
                      location: e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50"
                  placeholder="e.g., London, UK"
                />
              </div>

              <Button
                type="submit"
                disabled={
                  loadingStates.creating ||
                  !newBusinessData.name ||
                  !newBusinessData.type
                }
                className="w-full h-12"
              >
                {loadingStates.creating ? (
                  <div className="flex items-center space-x-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Creating Business...</span>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4" />
                    <span>Create Business & Continue</span>
                    <ArrowRight className="h-4 w-4" />
                  </div>
                )}
              </Button>
            </form>
          )}

          {/* Footer */}
          <div className="text-center text-xs text-gray-500">
            You can change or add more businesses later in settings
          </div>

          {/*  Back to home */}
          <div className="text-center">
            <Button
              variant="link"
              size="sm"
              onClick={() => router.push("/")}
              className="text-xs text-gray-500 hover:text-gray-700"
            >
              ← Back to Home
            </Button>

            {/* add logout here  */}
            <Button
              variant="link"
              size="sm"
              onClick={() => signOut()}
              className="text-xs text-gray-500 hover:text-gray-700 ml-2"
            >
              Logout
            </Button>
          </div>
          </div>
        )}
      </div>
    </div>
  );
}
