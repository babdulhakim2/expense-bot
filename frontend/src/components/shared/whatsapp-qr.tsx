'use client';

import { Button } from "@/components/ui/button";
import { WHATSAPP_CONFIG } from '@/utils/whatsapp.config';
import { MessageCircle } from "lucide-react";
import { QRCodeSVG } from 'qrcode.react';
import { useEffect, useState } from 'react';

interface WhatsAppQRProps {
  size?: number;
  message?: string;
  showWebOption?: boolean;
  className?: string;
}

export function WhatsAppQR({ size = 240, message, showWebOption = true, className }: WhatsAppQRProps) {
  const [isMounted, setIsMounted] = useState(false);
  const qrUrl = WHATSAPP_CONFIG.getWhatsAppUrl(message);
  
  useEffect(() => {
    setIsMounted(true);
  }, []);
  
  const handleWhatsAppRedirect = () => {
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    const baseNumber = WHATSAPP_CONFIG.phoneNumber;
    const encodedMessage = encodeURIComponent(message || WHATSAPP_CONFIG.defaultMessage);
    
    if (isMobile) {
      // Mobile devices: Use wa.me link
      window.open(`https://wa.me/${baseNumber}?text=${encodedMessage}`, '_blank', 'noopener,noreferrer');
    } else {
      // Desktop: Use WhatsApp Web link
      window.open(
        `https://web.whatsapp.com/send?phone=${baseNumber}&text=${encodedMessage}`,
        '_blank',
        'noopener,noreferrer'
      );
    }
  };

  if (!isMounted) {
    return null;
  }

  return (
    <div className={`flex flex-col items-center space-y-4 ${className}`}>
      <div className="p-4 bg-white rounded-lg shadow-md">
        <QRCodeSVG 
          value={qrUrl}
          size={size}
          level="H"
          includeMargin={true}
        />
      </div>
      
      {showWebOption && (
        <Button
          className="flex items-center space-x-2 bg-[#25D366] hover:bg-[#128C7E] text-white"
          size="lg"
          onClick={handleWhatsAppRedirect}
        >
          <MessageCircle className="w-5 h-5 mr-2" />
          <span>Continue on WhatsApp Web</span>
        </Button>
      )}
    </div>
  );
} 