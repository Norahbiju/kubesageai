"use client";

import { useSearchParams } from "next/navigation";
import { useEffect } from "react";

export function AuthBootstrap() {
  const searchParams = useSearchParams();

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) return;
    window.localStorage.setItem("kubesage_token", token);
    const url = new URL(window.location.href);
    url.searchParams.delete("token");
    window.history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
  }, [searchParams]);

  return null;
}
