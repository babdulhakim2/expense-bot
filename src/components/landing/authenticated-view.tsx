"use client";

import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { LogOut, MessageCircle } from "lucide-react";
import { signOut } from 'next-auth/react';
import Image from "next/image";
import { useRouter } from "next/navigation";
import { QRCodeSVG } from "qrcode.react";

const WHATSAPP_NUMBER = "447949366218";
const WHATSAPP_MESSAGE = "Hi! I'd like to start tracking my expenses.";

export function AuthenticatedView() {
  const router = useRouter();
  
  const handleWhatsAppRedirect = () => {
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    const webUrl = `https://web.whatsapp.com/send?phone=${WHATSAPP_NUMBER}&text=${encodeURIComponent(WHATSAPP_MESSAGE)}`;
    const mobileUrl = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(WHATSAPP_MESSAGE)}`;
    window.open(isMobile ? mobileUrl : webUrl, '_blank');
  };
  
  const qrWhatsappUrl = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(WHATSAPP_MESSAGE)}`;

  return (
    <div className="max-w-2xl mx-auto mt-5">
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
          Welcome back! 👋
        </p>
        </div>
          <h2 className="text-2xl font-bold">Track Your Expenses with Whatsapp screenshots</h2>
          <p className="text-muted-foreground">
            Scan the QR code to connect with <strong>phone</strong> or click the button for <strong>web</strong>
          </p>
        </div>

        {/* QR Code */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="p-4 bg-white rounded-lg shadow-md"
        >
          <QRCodeSVG 
            value={qrWhatsappUrl}
            size={240}
            level="H"
            includeMargin={true}
          />
        </motion.div>

        <div className="flex flex-col sm:flex-row gap-4">
          {/* Direct WhatsApp Link Button */}
          <Button
            className="flex items-center space-x-2 bg-[#25D366] hover:bg-[#128C7E]"
            size="lg"
            onClick={handleWhatsAppRedirect}
          >
            <MessageCircle className="w-5 h-5" />
            <span>Use on the Web</span>
          </Button>

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
  );
} 