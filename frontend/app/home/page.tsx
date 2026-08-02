"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { clearSession } from "@/lib/auth";
import { clearLastDriverState, resolveCurrentDriverRoute } from "@/lib/flow-state";

export default function HomePage() {
  const router = useRouter();

  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  const loadHomeData = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage("");

    try {
      const nextRoute = await resolveCurrentDriverRoute();

      if (nextRoute === "/") {
        router.replace("/");
        return;
      }

      router.replace(nextRoute);
    } catch {
      setErrorMessage("Couldn't determine shift status right now.");
    } finally {
      setIsLoading(false);
    }
  }, [router]);

  useEffect(() => {
    void loadHomeData();
  }, [loadHomeData]);

  function handleLogout() {
    clearSession();
    clearLastDriverState();
    router.push("/");
  }

  if (isLoading) {
    return (
      <main className="min-h-screen bg-neutral-100 text-black">
        <div className="mx-auto min-h-screen w-full max-w-[430px] bg-white px-5 py-6">
          <div className="mb-8">
            <div className="mb-6 h-5 w-24 animate-pulse rounded bg-neutral-200" />
            <div className="h-8 w-32 animate-pulse rounded bg-neutral-200" />
            <div className="mt-3 h-6 w-40 animate-pulse rounded bg-neutral-200" />
            <div className="mt-2 h-4 w-24 animate-pulse rounded bg-neutral-200" />
          </div>

          <div className="space-y-4">
            <div className="h-24 animate-pulse rounded-2xl bg-neutral-100" />
            <div className="h-14 animate-pulse rounded-2xl bg-neutral-200" />
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-neutral-100 text-black">
      <div className="mx-auto min-h-screen w-full max-w-[430px] bg-white px-5 py-6">
        <div className="mb-8">
          <button
            type="button"
            onClick={handleLogout}
            className="mb-6 text-sm font-medium text-neutral-500 transition hover:text-black"
          >
            Log Out
          </button>

          <p className="text-xs font-semibold tracking-wide text-neutral-500">
            Home
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">Determining your current status</h1>
          <p className="mt-3 text-sm text-neutral-600">
            You&apos;ll be redirected to the right step automatically.
          </p>
        </div>

        {errorMessage ? (
          <div className="space-y-4">
            <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {errorMessage}
            </div>

            <button
              type="button"
              onClick={loadHomeData}
              className="w-full rounded-2xl bg-black px-4 py-4 text-base font-semibold text-white transition hover:opacity-90"
            >
              Retry
            </button>

            <button
              type="button"
              onClick={handleLogout}
              className="w-full rounded-2xl border border-black/15 px-4 py-4 text-base font-medium text-black transition hover:bg-neutral-50"
            >
              Log Out
            </button>
          </div>
        ) : null}
      </div>
    </main>
  );
}
