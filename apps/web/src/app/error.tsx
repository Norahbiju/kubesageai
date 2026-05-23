"use client";

import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function ErrorBoundary({ reset }: { error: Error; reset: () => void }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-md rounded-lg border border-line bg-panel p-6 text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-md bg-rose/15 text-rose">
          <AlertTriangle size={22} />
        </div>
        <h1 className="text-xl font-semibold">Analysis surface failed</h1>
        <p className="mt-2 text-sm text-muted">The dashboard hit an unexpected client-side error.</p>
        <Button className="mt-5" onClick={reset}>
          Retry
        </Button>
      </div>
    </main>
  );
}
