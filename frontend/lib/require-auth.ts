"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { getAccessToken } from "@/lib/auth";
import { clearLastDriverState, getDriverLandingState } from "@/lib/flow-state";

export function useRequireAuth(pathWithQuery?: string): boolean {
  const router = useRouter();
  const token = typeof window === "undefined" ? null : getAccessToken();

  useEffect(() => {
    if (!token) {
      router.replace("/");
    }
  }, [pathWithQuery, router, token]);

  return Boolean(token);
}

export function useRequireDriverFlow(
  expectedFlow: "start_shift" | "end_shift",
  pathWithQuery?: string
): boolean {
  const router = useRouter();
  const token = typeof window === "undefined" ? null : getAccessToken();
  const [isAllowed, setIsAllowed] = useState(false);

  useEffect(() => {
    let isMounted = true;

    if (!token) {
      router.replace("/");
      return;
    }

    void (async () => {
      try {
        const landingState = await getDriverLandingState();

        if (!isMounted) {
          return;
        }

        if (!landingState) {
          setIsAllowed(false);
          router.replace("/");
          return;
        }

        if (landingState.flow !== expectedFlow) {
          setIsAllowed(false);
          clearLastDriverState();
          router.replace(landingState.route);
          return;
        }

        setIsAllowed(true);
      } catch {
        if (isMounted) {
          // Keep the current page on transient backend errors instead of
          // bouncing the driver into the wrong flow.
          setIsAllowed(true);
        }
      }
    })();

    return () => {
      isMounted = false;
    };
  }, [expectedFlow, pathWithQuery, router, token]);

  return isAllowed;
}
