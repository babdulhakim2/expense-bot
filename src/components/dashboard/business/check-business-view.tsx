"use client";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "@/hooks/use-toast";
import { BUSINESS_CATEGORIES } from "@/lib/constants/business-categories";
import { auth } from '@/lib/firebase/firebase';
import { BusinessService } from '@/lib/firebase/services/business-service';
import { useSession } from 'next-auth/react';
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

interface FormData {
  businessName: string;
  businessType: string;
}

export function CheckBusinessView() {
  const router = useRouter();
  const [showDialog, setShowDialog] = useState(false);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState<FormData>({
    businessName: "",
    businessType: "",
  });
  const { data: session } = useSession();
  const currentUser = session?.user;

  useEffect(() => {
    const checkBusinessProfile = async () => {
      try {
        if (!currentUser?.email) {
          throw new Error('No authenticated user found');
        }

        const business = await BusinessService.getBusinessByUserEmail(currentUser.email);
        
        if (business) {
          router.push('/dashboard');
        } else {
          setShowDialog(true);
        }
      } catch (error) {
        console.error('Error checking business profile:', error);
        toast({
          title: "Error",
          description: "Failed to load business profile",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    checkBusinessProfile();
  }, [currentUser?.email, router]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);

    try {
      const currentUser = auth.currentUser;
      if (!currentUser?.email) {
        throw new Error('No authenticated user found');
      }

      await BusinessService.createBusiness(
        currentUser.uid,
        currentUser.email,
        {
          name: formData.businessName,
          type: formData.businessType,
        }
      );

      setShowDialog(false);
      router.push('/dashboard');
    } catch (error) {
      console.error('Error creating business:', error);
      toast({
        title: "Error",
        description: "Failed to create business profile",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <>
      <div className="flex flex-col items-center space-y-8">
       
      </div>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Complete Your Profile</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="businessName">Business Name</Label>
              <input
                id="businessName"
                value={formData.businessName}
                onChange={(e) => setFormData(prev => ({ ...prev, businessName: e.target.value }))}
                className="w-full p-2 border rounded"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="businessType">Business Category</Label>
              <Select
                value={formData.businessType}
                onValueChange={(value) => setFormData(prev => ({ ...prev, businessType: value }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select business category" />
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
            <Button type="submit" className="w-full">
              Save Profile & Continue
            </Button>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
} 