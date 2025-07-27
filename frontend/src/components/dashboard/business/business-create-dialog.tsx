"use client";

import { useState } from "react";
import { useBusiness } from "@/app/providers/BusinessProvider";
import { BUSINESS_CATEGORIES } from "@/lib/constants/business-categories";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Building2Icon, Loader2 } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { Business } from "@/lib/firebase/services/business-service";

interface BusinessCreateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: (business: Business) => void;
}

interface NewBusinessData {
  name: string;
  type: string;
  location: string;
}

export function BusinessCreateDialog({
  open,
  onOpenChange,
  onSuccess,
}: BusinessCreateDialogProps) {
  const { createAndSelectBusiness, loadingStates } = useBusiness();
  const [newBusinessData, setNewBusinessData] = useState<NewBusinessData>({
    name: "",
    type: "",
    location: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!newBusinessData.name.trim() || !newBusinessData.type) {
      toast({
        title: "Missing Information",
        description: "Please fill in both business name and category",
        variant: "destructive",
      });
      return;
    }

    try {
      const business = await createAndSelectBusiness({
        name: newBusinessData.name.trim(),
        type: newBusinessData.type,
        location: newBusinessData.location.trim() || undefined,
      });

      toast({
        title: "Business Created",
        description: `${business.name} has been created and selected`,
      });

      // Reset form
      setNewBusinessData({ name: "", type: "", location: "" });
      
      // Close dialog
      onOpenChange(false);
      
      // Call success callback
      onSuccess?.(business);
    } catch (error) {
      console.error("Failed to create business:", error);
      toast({
        title: "Error",
        description: "Failed to create business. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleCancel = () => {
    setNewBusinessData({ name: "", type: "", location: "" });
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Building2Icon className="h-5 w-5" />
            Create New Business
          </DialogTitle>
          <DialogDescription>
            Set up a new business profile to manage your expenses separately.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="businessName">Business Name *</Label>
            <Input
              id="businessName"
              value={newBusinessData.name}
              onChange={(e) =>
                setNewBusinessData((prev) => ({
                  ...prev,
                  name: e.target.value,
                }))
              }
              placeholder="Enter your business name"
              disabled={loadingStates.creating}
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
              disabled={loadingStates.creating}
            >
              <SelectTrigger>
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
            <Input
              id="businessLocation"
              value={newBusinessData.location}
              onChange={(e) =>
                setNewBusinessData((prev) => ({
                  ...prev,
                  location: e.target.value,
                }))
              }
              placeholder="e.g., London, UK"
              disabled={loadingStates.creating}
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={loadingStates.creating}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={
                loadingStates.creating ||
                !newBusinessData.name.trim() ||
                !newBusinessData.type
              }
            >
              {loadingStates.creating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                "Create Business"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}