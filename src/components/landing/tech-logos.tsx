"use client";

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
    src: "/images/tech/g-cloud.png",
    alt: "Google Cloud",
    link: "https://cloud.google.com",
    className: "w-11 h-11"
  }
];

export function TechLogos() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-6 sm:gap-10 py-8">
      {logos.map((logo) => (
        <a
          key={logo.alt}
          href={logo.link}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center hover:scale-110 transition-transform duration-200"
        >
          <div className="bg-background/80 backdrop-blur-sm rounded-lg p-3.5 sm:p-4 shadow-lg border border-border/50 hover:border-primary/50 transition-colors">
            <Image
              src={logo.src}
              alt={logo.alt}
              width={48}
              height={48}
              className="w-auto h-auto"
            />
          </div>
        </a>
      ))}
    </div>
  );
} 