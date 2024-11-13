"use client";

import { useState } from "react";
import { Phone, Bot, Receipt, ArrowRight, Github, Shield, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";

export default function Home() {
  const [phone, setPhone] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!phone.match(/^\+?[1-9]\d{1,14}$/)) {
      toast.error("Please enter a valid phone number");
      return;
    }
    // Format phone number for WhatsApp
    const formattedPhone = phone.replace(/\D/g, "");
    window.location.href = `https://wa.me/${formattedPhone}`;
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-background to-secondary">
      {/* Hero Section */}
      <div className="container mx-auto px-4 pt-20 pb-16">
        <div className="flex flex-col items-center text-center space-y-8">
          <div className="rounded-full bg-primary/10 p-4 mb-4">
            <Bot className="w-12 h-12 text-primary" />
          </div>
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight">
            Your AI-Powered
            <span className="text-primary block">Bookkeeping Assistant</span>
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl">
            Simplify your bookkeeping with ExpenseBot. Just send your receipts via WhatsApp, 
            and let AI handle the rest.
          </p>
          
          {/* Phone Input Form */}
          <form onSubmit={handleSubmit} className="w-full max-w-md space-y-4">
            <div className="flex space-x-2">
              <div className="relative flex-1">
                <Phone className="absolute left-3 top-2.5 h-5 w-5 text-muted-foreground" />
                <Input
                  type="tel"
                  placeholder="Enter your WhatsApp number"
                  className="pl-10"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                />
              </div>
              <Button type="submit">
                Get Started <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </form>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-8 mt-20">
          <div className="bg-card p-6 rounded-lg border">
            <Receipt className="w-10 h-10 text-primary mb-4" />
            <h3 className="text-lg font-semibold mb-2">Smart Receipt Processing</h3>
            <p className="text-muted-foreground">
              Simply snap and send your receipts. Our AI extracts and categorizes all important information.
            </p>
          </div>
          <div className="bg-card p-6 rounded-lg border">
            <Shield className="w-10 h-10 text-primary mb-4" />
            <h3 className="text-lg font-semibold mb-2">Secure & Private</h3>
            <p className="text-muted-foreground">
              Your financial data is encrypted and protected. We prioritize your privacy and security.
            </p>
          </div>
          <div className="bg-card p-6 rounded-lg border">
            <Sparkles className="w-10 h-10 text-primary mb-4" />
            <h3 className="text-lg font-semibold mb-2">Real-time Insights</h3>
            <p className="text-muted-foreground">
              Get instant analysis and categorization of your expenses with AI-powered insights.
            </p>
          </div>
        </div>

        {/* Open Source Banner */}
        <div className="mt-20 text-center">
          <a
            href="https://github.com/babdulhakim2/expense-bot"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center space-x-2 text-muted-foreground hover:text-primary transition-colors"
          >
            <Github className="w-5 h-5" />
            <span>Open Source on GitHub</span>
          </a>
        </div>
      </div>
    </main>
  );
}