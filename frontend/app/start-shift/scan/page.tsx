"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";

import QrScanner from "@/components/qr-scanner";
import { clearSession } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/config";
import { clearLastDriverState, saveStartQrScannedState } from "@/lib/flow-state";
import { useRequireDriverFlow } from "@/lib/require-auth";

export default function StartShiftScanPage() {
  const router = useRouter();
  const isAuthorized = useRequireDriverFlow("start_shift", "/start-shift/scan");

  const [errorMessage, setErrorMessage] = useState("");
  const [isValidating, setIsValidating] = useState(false);
  const [scannerResetKey, setScannerResetKey] = useState(0);

  const continueWithPlate = useCallback(
    (rawPlate: string) => {
      const normalizedPlate = rawPlate.trim();
      if (!normalizedPlate) return;

      saveStartQrScannedState(normalizedPlate);
      router.push(
        `/start-shift/dashboard-photo?plate_number=${encodeURIComponent(
          normalizedPlate
        )}`
      );
    },
    [router]
  );

  const restartScannerWithDelay = useCallback(() => {
    setTimeout(() => {
      setScannerResetKey((prev) => prev + 1);
    }, 1500);
  }, []);

  const validateQrAndContinue = useCallback(
    async (rawQrValue: string) => {
      const normalizedQrValue = rawQrValue.trim();
      if (!normalizedQrValue) return;

      setErrorMessage("");
      setIsValidating(true);

      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/cars/validate-qr`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            qr_value: normalizedQrValue,
          }),
        });

        const data = await response.json();

        if (!response.ok) {
          setErrorMessage("تعذر التحقق من السيارة.");
          restartScannerWithDelay();
          return;
        }

        if (!data.is_valid || !data.plate_number) {
          setErrorMessage("هذه السيارة غير مسجلة في الأسطول. حاول مرة أخرى.");
          restartScannerWithDelay();
          return;
        }

        continueWithPlate(data.plate_number);
      } catch {
        setErrorMessage("تعذر الاتصال بالخادم.");
        restartScannerWithDelay();
      } finally {
        setIsValidating(false);
      }
    },
    [continueWithPlate, restartScannerWithDelay]
  );

  const handleQrSuccess = useCallback(
    async (decodedText: string) => {
      await validateQrAndContinue(decodedText);
    },
    [validateQrAndContinue]
  );

  const handleQrError = useCallback((message: string) => {
    setErrorMessage(message);
  }, []);

  if (!isAuthorized) {
    return null;
  }

  function handleLogout() {
    clearSession();
    clearLastDriverState();
    router.push("/");
  }

  return (
    <main className="min-h-screen bg-neutral-100 text-black">
      <div className="mx-auto min-h-screen w-full max-w-[430px] bg-white px-5 py-6">
        <div className="mb-8">
          <div className="mb-6 flex items-center justify-between gap-4">
            <button
              type="button"
              onClick={handleLogout}
              className="text-sm font-medium text-neutral-500 transition hover:text-black"
            >
              تسجيل الخروج
            </button>

            <button
              type="button"
              onClick={() => router.push("/start-shift")}
              className="text-sm font-medium text-neutral-500 transition hover:text-black"
            >
              رجوع
            </button>
          </div>

          <p className="text-xs font-semibold tracking-wide text-neutral-500">
            بدء الوردية · مسح السيارة
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">
            امسح QR السيارة
          </h1>
          <p className="mt-2 text-sm text-neutral-600">
            وجّه الكاميرا نحو QR الخاص بالسيارة للمتابعة.
          </p>
        </div>

        <div className="space-y-5">
          <div className="rounded-2xl border border-black/10 bg-neutral-50 p-3">
            <QrScanner
              onScanSuccess={handleQrSuccess}
              onScanError={handleQrError}
              resetKey={scannerResetKey}
            />
          </div>

          {isValidating ? (
            <div className="rounded-2xl border border-black/10 bg-neutral-50 px-4 py-3 text-sm text-neutral-700">
              جاري التحقق من السيارة...
            </div>
          ) : null}

          {errorMessage ? (
            <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {errorMessage}
            </div>
          ) : null}
        </div>
      </div>
    </main>
  );
}
