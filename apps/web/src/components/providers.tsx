"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { Suspense, useState } from "react";
import { AuthBootstrap } from "@/components/auth-bootstrap";

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());
  return (
    <QueryClientProvider client={queryClient}>
      <Suspense fallback={null}>
        <AuthBootstrap />
      </Suspense>
      {children}
    </QueryClientProvider>
  );
}
