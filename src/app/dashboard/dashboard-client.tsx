"use client";

import { Session } from "next-auth";
import { signOut } from "next-auth/react";
import { QRCodeSVG } from "qrcode.react";
import { MessageCircle, Home, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

const WHATSAPP_NUMBER = "447949366218";
const WHATSAPP_MESSAGE = "Hi! I'd like to start tracking my expenses.";

export default function DashboardClient({ session }: { session: Session }) {
  const router = useRouter();
  
  const handleSignOut = async () => {
    await signOut({ 
      redirect: true,
      callbackUrl: '/' 
    });
  };
  
  const handleWhatsAppRedirect = () => {
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    const webUrl = `https://web.whatsapp.com/send?phone=${WHATSAPP_NUMBER}&text=${encodeURIComponent(WHATSAPP_MESSAGE)}`;
    const mobileUrl = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(WHATSAPP_MESSAGE)}`;
    window.open(isMobile ? mobileUrl : webUrl, '_blank');
  };
  
  const qrWhatsappUrl = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(WHATSAPP_MESSAGE)}`;

  return (
    <div className="container mx-auto p-8">
      <div className="flex justify-between items-center mb-8">
        <Button
          variant="ghost"
          onClick={() => router.push('/')}
          className="flex items-center gap-2"
        >
          <Home className="w-4 h-4" />
          Home
        </Button>

        <Button
          variant="ghost"
          onClick={handleSignOut}
          className="flex items-center gap-2 text-destructive hover:text-destructive"
        >
          <LogOut className="w-4 h-4" />
          Sign Out
        </Button>
      </div>

      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold mb-4 text-center">
          Welcome to ExpenseBot!
        </h1>
        
        <div className="bg-card shadow-lg rounded-lg p-8 mt-6">
          <div className="space-y-2 mb-8">
            {/* <p><strong>User ID:</strong> {session?.user?.id || 'Not available'}</p> */}
            <p><strong>Phone:</strong> {session?.user?.phoneNumber || 'Not available'}</p>
          </div>

          <div className="border-t pt-8">
            <h2 className="text-2xl font-semibold mb-6 text-center">
              Start Tracking Your Expenses
            </h2>
            
            <div className="flex flex-col items-center space-y-8">
              {/* QR Code */}
              <div className="p-4 bg-white rounded-lg shadow-md">
                <QRCodeSVG 
                  value={qrWhatsappUrl}
                  size={200}
                  level="H"
                  includeMargin={true}
                />
              </div>
              
              <p className="text-center text-muted-foreground">
                Scan this QR code with your phone's camera <br/> 
                or click the button below to start chatting
              </p>

              {/* Direct WhatsApp Link Button */}
              <Button
                className="flex items-center space-x-2 bg-[#25D366] hover:bg-[#128C7E]"
                size="lg"
                onClick={handleWhatsAppRedirect}
              >
                <MessageCircle className="w-5 h-5" />
                <span>Chat on WhatsApp</span>
              </Button>
            </div>
          </div>
        </div>

        <p className="text-center text-muted-foreground mt-8">
          Simply send your receipts to our WhatsApp bot and we'll handle the rest!
        </p>
      </div>
    </div>
  );
} 