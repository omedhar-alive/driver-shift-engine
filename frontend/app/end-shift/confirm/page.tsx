"use client";

import { useRouter } from "next/navigation";
import { clearSession } from "@/lib/auth";
import { clearLastDriverState } from "@/lib/flow-state";
import { useRequireDriverFlow } from "@/lib/require-auth";

export default function EndShiftConfirmPage() {
  const router = useRouter();
  const isAuthorized = useRequireDriverFlow("end_shift", "/end-shift/confirm");

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
              Log Out
            </button>

            <button
              type="button"
              onClick={() => router.push("/end-shift")}
              className="text-sm font-medium text-neutral-500 transition hover:text-black"
            >
              Back
            </button>
          </div>

          <p className="text-xs font-semibold tracking-wide text-neutral-500">
            End Shift · Confirm
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">Confirm End of Shift</h1>
          <p className="mt-2 text-sm text-neutral-600">
            Are you sure you want to end your shift?
          </p>
        </div>

        <div className="space-y-4">
          <button
            type="button"
            onClick={() => router.push("/end-shift/dashboard-photo")}
            className="w-full rounded-2xl bg-black px-4 py-4 text-base font-semibold text-white transition hover:opacity-90"
          >
            Yes, End Shift
          </button>

          <button
            type="button"
            onClick={() => router.push("/home")}
            className="w-full rounded-2xl border border-black/15 px-4 py-4 text-base font-medium text-black transition hover:bg-neutral-50"
          >
            Cancel
          </button>
        </div>
      </div>
    </main>
  );
}
