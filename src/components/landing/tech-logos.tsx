"use client";

import { motion } from 'framer-motion';
import Image from 'next/image';

const logos = [
  {
    src: "/images/tech/google-gemma.webp",
    alt: "Gemma AI",
    link: "https://blog.google/technology/developers/gemma-open-models/",
    className: "w-10 h-10"
  },
  {
    src: "/images/tech/google-drive.png",
    alt: "Google Drive",
    link: "https://drive.google.com",
    className: "w-12 h-12"
  },
  {
    src: "/images/tech/whatsapp.png",
    alt: "WhatsApp",
    link: "https://www.whatsapp.com",
    className: "w-10 h-10"
  },
  {
    src: "/images/tech/firebase.png",
    alt: "Firebase",
    link: "https://firebase.google.com",
    className: "w-11 h-11"
  },
  {
    src: "/images/tech/twilio.webp",
    alt: "Twilio",
    link: "https://www.twilio.com",
    className: "w-10 h-10"
  }
];

export function TechLogos() {
  return (
    <div className="absolute inset-0 w-full h-full">
      {logos.map((logo, index) => {
        // Calculate position in a circle
        const angle = (index * (360 / logos.length) + 0) * (Math.PI / 180);
        const radius = 100; // Distance from center

        return (
          <motion.a
            key={logo.alt}
            href={logo.link}
            target="_blank"
            rel="noopener noreferrer"
            initial={{ opacity: 0, scale: 0 }}
            animate={{ 
              opacity: 1,
              scale: 1,
            }}
            transition={{
              type: "spring",
              stiffness: 260,
              damping: 20,
              delay: index * 0.1,
            }}
            whileHover={{ 
              scale: 1.2,
              rotate: 360,
              transition: { duration: 0.6 }
            }}
            className="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2"
            style={{
              transform: `translate(-50%, -50%) rotate(${angle}rad) translateY(-${radius}px)`,
              animation: `orbit ${20 + index * 2}s linear infinite`
            }}
          >
            <div className="bg-background/80 backdrop-blur-sm rounded-lg p-2 shadow-lg border border-border/50 hover:border-primary/50 transition-colors">
              <Image
                src={logo.src}
                alt={logo.alt}
                width={32}
                height={32}
                className="w-auto h-auto"
              />
            </div>
          </motion.a>
        );
      })}
    </div>
  );
} 