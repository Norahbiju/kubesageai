"use client";

import { motion } from "framer-motion";
import { Cloud, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export default function LoginPage() {
  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background px-4">
      <motion.div
        className="absolute inset-0 bg-[radial-gradient(circle_at_35%_25%,rgba(92,225,230,.2),transparent_34%),radial-gradient(circle_at_70%_75%,rgba(183,245,102,.14),transparent_28%)]"
        animate={{ scale: [1, 1.05, 1], opacity: [.85, 1, .85] }}
        transition={{ duration: 8, repeat: Infinity }}
      />
      <div className="relative w-full max-w-md rounded-lg border border-line bg-panel/80 p-8 shadow-glow backdrop-blur">
        <div className="mb-8 flex items-center gap-3">
          <div className="rounded-md bg-cyan p-3 text-black">
            <Cloud size={22} />
          </div>
          <div>
            <h1 className="text-2xl font-semibold">KubeSage AI</h1>
            <p className="text-sm text-muted">AI-native AKS incident copilot</p>
          </div>
        </div>
        <div className="space-y-4">
          <div className="rounded-md border border-line bg-panel2 p-4 text-sm text-muted">
            Connect Azure, discover AKS clusters, stream Kubernetes failure analysis, and approve safe remediations.
          </div>
          <Button className="w-full" onClick={() => (window.location.href = api.loginUrl())}>
            <ShieldCheck size={17} /> Login with Azure
          </Button>
        </div>
      </div>
    </main>
  );
}
