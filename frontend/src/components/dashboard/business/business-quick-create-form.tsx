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
import { X, Loader2, Building2Icon } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { Business } from "@/lib/firebase/services/business-service";

interface BusinessQuickCreateFormProps {
  onSuccess: (business: Business) => void;
  onCancel: () => void;
  isCreating?: boolean;
}

export function BusinessQuickCreateForm({
  onSuccess,
  onCancel,
  isCreating = false,
}: BusinessQuickCreateFormProps) {
  const { createAndSelectBusiness } = useBusiness();
  const [formData, setFormData] = useState({
    name: "",
    type: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!formData.name.trim() || !formData.type) {
      toast({
        title: "Missing Information",
        description: "Please fill in both business name and category",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const business = await createAndSelectBusiness({
        name: formData.name.trim(),
        type: formData.type,
      });

      onSuccess(business);
    } catch (error) {
      console.error("Failed to create business:", error);
      toast({
        title: "Error",
        description: "Failed to create business. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const isLoading = isCreating || isSubmitting;

  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Building2Icon className="h-5 w-5 text-gray-400" />
          <h3 className="text-sm font-medium text-gray-200">Create Business</h3>
        </div>
        <button
          onClick={onCancel}
          disabled={isLoading}
          className="text-gray-400 hover:text-gray-200 transition-colors disabled:opacity-50"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="businessName" className="text-xs text-gray-300">
            Business Name
          </Label>
          <Input
            id="businessName"
            value={formData.name}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, name: e.target.value }))
            }
            placeholder="Enter business name"
            disabled={isLoading}
            className="h-9 text-sm bg-gray-900 border-gray-600"
            required
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="businessType" className="text-xs text-gray-300">
            Category
          </Label>
          <Select
            value={formData.type}
            onValueChange={(value) =>
              setFormData((prev) => ({ ...prev, type: value }))
            }
            disabled={isLoading}
          >
            <SelectTrigger className="h-9 text-sm bg-gray-900 border-gray-600">
              <SelectValue placeholder="Select category" />
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

        <div className="flex space-x-2 pt-2">
          <Button
            type="submit"
            disabled={isLoading || !formData.name.trim() || !formData.type}
            className="flex-1 h-9 text-sm"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Creating...
              </>
            ) : (
              "Create & Select"
            )}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={isLoading}
            className="h-9 text-sm"
          >
            Cancel
          </Button>
        </div>
      </form>
    </div>
  );
}
