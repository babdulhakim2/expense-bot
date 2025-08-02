"use client";

import { motion } from 'framer-motion';
import { FolderSync, Shield, MessageSquare, FileSpreadsheet } from 'lucide-react';
import { useInView } from 'react-intersection-observer';

const features = [
  {
    icon: <FileSpreadsheet className="w-10 h-10 text-green-600 mb-4" />,
    title: "Google Sheets Magic",
    description: "Harness the full power of Google Sheets for expense tracking. Automatic categorization, formulas, and charts - all in your familiar spreadsheet environment.",
    color: "green"
  },
  {
    icon: <MessageSquare className="w-10 h-10 text-blue-600 mb-4" />,
    title: "Ask Anything",
    description: "Simply ask questions about your expenses in plain English. 'How much did I spend on restaurants?' - get instant AI-powered answers.",
    color: "blue"
  },
  {
    icon: <FolderSync className="w-10 h-10 text-purple-600 mb-4" />,
    title: "Smart Organization",
    description: "AI automatically categorizes and sorts your financial documents into intuitive folder structures within your Google Drive.",
    color: "purple"
  },
  {
    icon: <Shield className="w-10 h-10 text-amber-600 mb-4" />,
    title: "Your Data, Your Drive",
    description: "Everything stays in your familiar Google Drive ecosystem. No external servers, no data privacy concerns - complete control.",
    color: "amber"
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
      className="mt-20"
    >
      {/* Section header */}
      <div className="text-center mb-16">
        <motion.h2
          initial={{ y: 20, opacity: 0 }}
          animate={inView ? { y: 0, opacity: 1 } : {}}
          transition={{ duration: 0.5 }}
          className="text-3xl sm:text-4xl font-bold mb-4"
        >
          Why Choose ExpenseBot?
        </motion.h2>
        <motion.p
          initial={{ y: 20, opacity: 0 }}
          animate={inView ? { y: 0, opacity: 1 } : {}}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="text-lg text-muted-foreground max-w-2xl mx-auto"
        >
          Combine the power of Google Sheets with AI to transform how you manage expenses
        </motion.p>
      </div>

      {/* Features grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
        {features.map((feature, index) => (
          <motion.div
            key={index}
            initial={{ y: 50, opacity: 0 }}
            animate={inView ? { y: 0, opacity: 1 } : {}}
            transition={{ delay: index * 0.1 + 0.4, duration: 0.5 }}
            whileHover={{ y: -5, transition: { duration: 0.2 } }}
            className="bg-card p-6 rounded-xl border hover:shadow-lg transition-all duration-300"
          >
            <div className="text-center">
              {feature.icon}
              <h3 className="text-lg font-semibold mb-3">{feature.title}</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">{feature.description}</p>
            </div>
          </motion.div>
        ))}
      </div>

    </motion.div>
  );
} 