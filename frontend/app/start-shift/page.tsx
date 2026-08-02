"use client";

import { useRouter } from "next/navigation";

import { clearSession } from "@/lib/auth";
import { clearLastDriverState } from "@/lib/flow-state";
import { useRequireDriverFlow } from "@/lib/require-auth";

export default function StartShiftPage() {
  const router = useRouter();
  const isAuthorized = useRequireDriverFlow("start_shift", "/start-shift");

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
              onClick={() => router.push("/home")}
              className="text-sm font-medium text-neutral-500 transition hover:text-black"
            >
              رجوع
            </button>
          </div>

          <div className="mb-8">
            <p className="text-xs font-semibold tracking-wide text-neutral-500">
              بدء الوردية
            </p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight">ابدأ الشيفت</h1>
            <p className="mt-3 text-sm text-neutral-600">
              اضغط للانتقال إلى مسح QR السيارة ثم استكمال خطوات بدء الوردية.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => router.push("/start-shift/scan")}
          className="w-full rounded-2xl bg-black px-4 py-4 text-base font-semibold text-white transition hover:opacity-90"
        >
          ابدا الشيفت
        </button>
      </div>
    </main>
  );
}
