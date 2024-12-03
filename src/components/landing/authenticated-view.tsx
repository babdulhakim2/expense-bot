"use client";

import { WhatsAppQR } from '@/components/shared/whatsapp-qr';
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useBusiness } from '@/contexts/business-context';
import { toast } from "@/hooks/use-toast";
import { BUSINESS_CATEGORIES } from "@/lib/constants/business-categories";
import { db } from "@/lib/firebase";
import { collection, doc, getDoc, setDoc } from "firebase/firestore";
import { motion } from "framer-motion";
import { LogOut } from "lucide-react";
import { signOut, useSession } from 'next-auth/react';
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

interface FormData {
  name: string;
  email: string;
  businessName: string;
  businessType: string;
}

export function AuthenticatedView() {
  const router = useRouter();
  const { data: session, status } = useSession();
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState<FormData>({
    name: '',
    email: '',
    businessName: '',
    businessType: BUSINESS_CATEGORIES[0].id
  });
  const { addBusiness, setCurrentBusiness } = useBusiness();

  useEffect(() => {
    const checkUserProfile = async () => {
      if (status === 'loading') return;
      if (!session?.user?.id) return;

      try {
        const userRef = doc(db, 'users', session.user.id);
        const userSnap = await getDoc(userRef);

        if (!userSnap.exists()) {
          setShowOnboarding(true);
          setFormData(prev => ({
            ...prev,
            name: (session.user as any)?.name || '',
          }));
        }
      } catch (error) {
        console.error('Error checking user profile:', error);
        toast({
          title: "Error",
          description: "Failed to load user profile",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    checkUserProfile();
  }, [session, status]);

  const handleSubmitProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!session?.user?.id) return;

    try {
      // Create user profile
      const userRef = doc(db, 'users', session.user.id);
      await setDoc(userRef, {
        id: session.user.id,
        name: formData.name,
        email: formData.email,
        createdAt: new Date(),
        updatedAt: new Date(),
      });

      // Create business and update context
      const businessRef = doc(collection(db, 'businesses'));
      const businessData = {
        id: businessRef.id,
        name: formData.businessName,
        type: formData.businessType,
        ownerId: session.user.id,
        createdAt: new Date(),
        updatedAt: new Date(),
      };
      
      await setDoc(businessRef, businessData);
      
      // Update business context
      setCurrentBusiness(businessData);

      setShowOnboarding(false);
      toast({
        title: "Success",
        description: "Profile and business created successfully",
      });
    } catch (error) {
      console.error('Error saving profile:', error);
      toast({
        title: "Error",
        description: "Failed to save profile",
        variant: "destructive",
      });
    }
  };

  if (status === 'loading') {
    return <div className="flex items-center justify-center min-h-[400px]">
      <p className="text-lg text-muted-foreground">Loading...</p>
    </div>;
  }

  if (!session?.user) {
    router.push('/');
    return null;
  }

  return (
    <>
      <div className="max-w-2xl mx-auto">
        <div className="flex flex-col items-center space-y-8">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="relative"
          >
            <Image 
              src="/logo.png" 
              alt="ExpenseBot Logo" 
              width={120} 
              height={120}
              className="rounded-full shadow-lg"
              priority
            />
          </motion.div>

          <div className="text-center space-y-2">
            <div className="flex flex-col items-center justify-center w-full mt-5 space-y-6">
              <p className="text-xl text-muted-foreground">
                Welcome back!
              </p>
            </div>
            <h2 className="text-2xl font-bold">Track Your Expenses with WhatsApp</h2>
            <p className="text-muted-foreground">
              Scan the QR code with your phone's camera or click below to open WhatsApp
            </p>
          </div>

          {/* QR Code */}
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="flex justify-center w-full"
          >
            <WhatsAppQR size={240} />
          </motion.div>

          <div className="flex flex-col sm:flex-row gap-4">
            <Button
              variant="outline"
              size="lg"
              onClick={() => router.push('/dashboard')}
            >
              Go to Dashboard
            </Button>
            <Button 
              size="lg"
              variant="outline"
              onClick={() => signOut({ callbackUrl: '/' })}
              className="min-w-[200px]"
            >
              Sign Out <LogOut className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      <Dialog 
        open={showOnboarding} 
        onOpenChange={() => {}} // Disable closing
      >
        <DialogContent onPointerDownOutside={(e) => e.preventDefault()}>
          <DialogHeader>
            <DialogTitle>Complete Your Profile</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmitProfile} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Full Name</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                required
                placeholder="John Doe"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email Address</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                required
                placeholder="john@example.com"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="businessName">Business Name</Label>
              <Input
                id="businessName"
                value={formData.businessName}
                onChange={(e) => setFormData(prev => ({ ...prev, businessName: e.target.value }))}
                required
                placeholder="My Awesome Business"
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