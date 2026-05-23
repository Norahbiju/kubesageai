"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect } from "react";

export function AuthBootstrap() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) return;
    window.localStorage.setItem("kubesage_token", token);
    const url = new URL(window.location.href);
    url.searchParams.delete("token");
    router.replace(`${url.pathname}${url.search}`);
  }, [router, searchParams]);

  return null;
}
