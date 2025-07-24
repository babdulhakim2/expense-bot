"use client";

import { motion } from 'framer-motion';
import { Receipt, Shield, Sparkles } from 'lucide-react';
import { useInView } from 'react-intersection-observer';

const features = [
  {
    icon: <Receipt className="w-10 h-10 text-primary mb-4" />,
    title: "Smart Receipt Processing",
    description: "Simply snap and send your receipts. Our AI extracts and categorizes all important information."
  },
  {
    icon: <Shield className="w-10 h-10 text-primary mb-4" />,
    title: "Secure & Private",
    description: "Your financial data within your control. Deploy directly to your cloud or run on-premise."
  },
  {
    icon: <Sparkles className="w-10 h-10 text-primary mb-4" />,
    title: "Real-time Insights",
    description: "Get instant analysis and categorization of your expenses with AI-powered insights."
  }
];

export function FeaturesGrid() {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1
  });

  return (
    <motion.div 
      ref={ref}
      className="grid md:grid-cols-3 gap-8 mt-20"
    >
      {features.map((feature, index) => (
        <motion.div
          key={index}
          initial={{ y: 50, opacity: 0 }}
          animate={inView ? { y: 0, opacity: 1 } : {}}
          transition={{ delay: index * 0.2, duration: 0.5 }}
          whileHover={{ scale: 1.03, transition: { duration: 0.2 } }}
          className="bg-card p-6 rounded-lg border hover:border-primary/50 transition-colors duration-300"
        >
          {feature.icon}
          <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
          <p className="text-muted-foreground">{feature.description}</p>
        </motion.div>
      ))}
    </motion.div>
  );
} 