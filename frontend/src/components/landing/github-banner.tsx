"use client";

import { Github } from 'lucide-react';

export function GithubBanner() {
  return (
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
  );
} 