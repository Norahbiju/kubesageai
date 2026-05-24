"use client";

import { motion } from "framer-motion";
import { Cloud, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export default function LoginPage() {
  const [hasLoginError, setHasLoginError] = useState(false);

  useEffect(() => {
    setHasLoginError(new URLSearchParams(window.location.search).has("error"));
  }, []);

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background px-4 grid-bg">
      <motion.div
        className="absolute inset-x-0 top-0 h-px bg-cyan/70"
        animate={{ opacity: [.45, 1, .45] }}
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
          {hasLoginError ? (
            <div className="rounded-md border border-red-400/40 bg-red-950/40 p-3 text-sm text-red-100">
              Azure login failed. Check the redirect URI and Entra app registration.
            </div>
          ) : null}
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
