"use client";

import Image from "next/image";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { API_BASE_URL, DEMO_MODE } from "@/lib/config";
import { clearSession } from "@/lib/auth";
import { clearLastDriverState, resolveLatestDriverRoute } from "@/lib/flow-state";

export default function LoginPage() {
  const router = useRouter();

  const [driverCode, setDriverCode] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("access_token");

    if (!token) {
      clearSession();
      clearLastDriverState();
      return;
    }

    void (async () => {
      const nextRoute = await resolveLatestDriverRoute();
      router.replace(nextRoute);
    })();
  }, [router]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage("");
    setIsSubmitting(true);

    // Reset any previously saved driver before starting a new login attempt.
    clearSession();
    clearLastDriverState();

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/drivers/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          driver_code: driverCode,
          password,
          remember_me: rememberMe,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setErrorMessage(data.detail || "فشل تسجيل الدخول.");
        return;
      }

      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("driver_code", data.driver.driver_code);
      localStorage.setItem("driver_name", data.driver.driver_name);

      const nextRoute = await resolveLatestDriverRoute();
      router.push(nextRoute);
    } catch {
      setErrorMessage("تعذر الاتصال بالخادم.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-neutral-100 text-black">
      <div className="mx-auto flex min-h-screen w-full max-w-[430px] flex-col bg-white px-5 py-6">
        {DEMO_MODE ? (
          <div
            dir="ltr"
            className="mb-4 rounded-2xl border border-black/10 bg-neutral-50 px-4 py-3 text-xs leading-relaxed text-neutral-700"
          >
            <span className="font-semibold text-neutral-900">Demo mode</span> — Gemini OCR
            is disabled here since this public demo ships without private API keys. In
            production, dashboard photos are read automatically. See the README for how the
            OCR pipeline works.
          </div>
        ) : null}

        <div className="flex flex-1 flex-col justify-center">
          <div className="mb-10 flex flex-col items-center text-center">
            <Image
              src="/TUT_Logo-03.png"
              alt="TUT Logo"
              width={180}
              height={70}
              className="mb-6 h-auto w-40"
              priority
            />
            <h1 className="text-3xl font-bold tracking-tight">تسجيل دخول السائق</h1>
            <p className="mt-2 text-sm text-neutral-600">
              سجّل الدخول لبدء أو إنهاء الوردية.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label
                htmlFor="driverCode"
                className="mb-2 block text-sm font-medium text-neutral-800"
              >
                كود السائق
              </label>
              <input
                id="driverCode"
                name="driverCode"
                type="text"
                placeholder="أدخل كود السائق"
                value={driverCode}
                onChange={(event) => setDriverCode(event.target.value)}
                className="w-full rounded-2xl border border-black/15 px-4 py-4 text-base outline-none transition focus:border-black"
                required
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="mb-2 block text-sm font-medium text-neutral-800"
              >
                كلمة المرور
              </label>
              <input
                id="password"
                name="password"
                type="password"
                placeholder="أدخل كلمة المرور"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="w-full rounded-2xl border border-black/15 px-4 py-4 text-base outline-none transition focus:border-black"
                required
              />
            </div>

            <label className="flex items-center gap-3 text-sm text-neutral-700">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-black/20"
                checked={rememberMe}
                onChange={(event) => setRememberMe(event.target.checked)}
              />
              <span>تذكرني</span>
            </label>

            {errorMessage ? (
              <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {errorMessage}
              </div>
            ) : null}

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full rounded-2xl bg-black px-4 py-4 text-base font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting ? "جاري تسجيل الدخول..." : "تسجيل الدخول"}
            </button>
          </form>
        </div>
      </div>
    </main>
  );
}
