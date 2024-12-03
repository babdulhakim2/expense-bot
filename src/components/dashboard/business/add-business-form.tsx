'use client';

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { BUSINESS_CATEGORIES } from "@/lib/constants/business-categories";
import { useBusiness } from "@/contexts/business-context";
import { doc, collection, setDoc } from "firebase/firestore";
import { db } from "@/lib/firebase";
import { useSession } from "next-auth/react";
import { toast } from "@/hooks/use-toast";
import { useRouter } from "next/navigation";

interface FormData {
  name: string;
  type: string;
}

export function AddBusinessForm() {
  const router = useRouter();
  const { data: session } = useSession();
  const { businesses, setBusinesses, setCurrentBusiness } = useBusiness();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState<FormData>({
    name: '',
    type: BUSINESS_CATEGORIES[0].id
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!session?.user?.id) return;
    
    setLoading(true);
    try {
      const businessRef = doc(collection(db, 'businesses'));
      const businessData = {
        id: businessRef.id,
        name: formData.name,
        type: formData.type,
        ownerId: session.user.id,
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      await setDoc(businessRef, businessData);
      
      // Update both current business and businesses list
      setCurrentBusiness(businessData);
      setBusinesses([...businesses, businessData]);

      toast({
        title: "Success",
        description: "Business created successfully",
      });

      // Small delay to show the toast before redirecting
      setTimeout(() => {
        router.push('/dashboard');
      }, 500);
    } catch (error) {
      console.error('Error creating business:', error);
      toast({
        title: "Error",
        description: "Failed to create business",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="name">Business Name</Label>
          <Input
            id="name"
            placeholder="Enter business name"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            required
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="type">Business Category</Label>
          <Select
            value={formData.type}
            onValueChange={(value) => setFormData(prev => ({ ...prev, type: value }))}
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
      </div>

      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? "Creating..." : "Create Business"}
      </Button>
    </form>
  );
} 