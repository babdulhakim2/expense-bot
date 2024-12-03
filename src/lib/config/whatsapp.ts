export const WHATSAPP_CONFIG = {
  phoneNumber: "447949366218", // Your WhatsApp business number
  defaultMessage: "Hi! I'd like to start tracking my expenses.",
  getWhatsAppUrl: (message: string = "") => {
    const baseNumber = WHATSAPP_CONFIG.phoneNumber;
    const encodedMessage = encodeURIComponent(message || WHATSAPP_CONFIG.defaultMessage);
    
    // Return mobile-friendly wa.me link for QR code scanning
    return `https://wa.me/${baseNumber}?text=${encodedMessage}`;
  }
}; 