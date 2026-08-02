"use client";

import { ChangeEvent, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { API_BASE_URL } from "@/lib/config";
import { clearSession, getAccessToken } from "@/lib/auth";
import {
  clearLastDriverState,
  saveShiftStartedSuccessfullyState,
  saveStartDashboardPhotoTakenState,
} from "@/lib/flow-state";
import { useRequireDriverFlow } from "@/lib/require-auth";

export const dynamic = "force-dynamic";

export default function StartShiftDashboardPhotoPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const plateNumber = searchParams.get("plate_number") || "";
  const isAuthorized = useRequireDriverFlow(
    "start_shift",
    plateNumber
      ? `/start-shift/dashboard-photo?plate_number=${encodeURIComponent(plateNumber)}`
      : "/start-shift/dashboard-photo"
  );
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [dashboardImage, setDashboardImage] = useState<File | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isAuthorized) {
    return null;
  }

  function handleLogout() {
    clearSession();
    clearLastDriverState();
    router.push("/");
  }

  function clearSelectedImage() {
    setDashboardImage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  function handleImageChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] || null;
    setDashboardImage(file);
    setErrorMessage("");
    setSuccessMessage("");

    if (file && plateNumber) {
      saveStartDashboardPhotoTakenState(plateNumber);
    }
  }

  async function handleSubmit() {
    const token = getAccessToken();

    if (!token) {
      router.push("/");
      return;
    }

    if (!plateNumber) {
      setErrorMessage("رقم اللوحة غير موجود.");
      return;
    }

    if (!dashboardImage) {
      setErrorMessage("يرجى اختيار صورة للتابلوه.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const formData = new FormData();
      formData.append("file", dashboardImage);

      const uploadResponse = await fetch(`${API_BASE_URL}/api/v1/uploads/image`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      const uploadData = await uploadResponse.json();

      if (!uploadResponse.ok) {
        setErrorMessage(uploadData.detail || "تعذر رفع الصورة.");
        return;
      }

      const shiftStartResponse = await fetch(`${API_BASE_URL}/api/v1/shift-starts/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          plate_number: plateNumber,
          start_dashboard_image: uploadData.file_path,
        }),
      });

      const shiftStartData = await shiftStartResponse.json();

      if (!shiftStartResponse.ok) {
        const detail =
          typeof shiftStartData.detail === "string"
            ? shiftStartData.detail
            : "تعذر بدء الوردية.";

        const requiresRetake = Boolean(shiftStartData.requires_retake);

        if (requiresRetake) {
          clearSelectedImage();
          setErrorMessage(
            detail || "الصورة غير واضحة. يرجى التقاط صورة أوضح للتابلوه."
          );
          return;
        }

        if (detail.toLowerCase().includes("open shift")) {
          setErrorMessage("لديك وردية نشطة بالفعل. جارٍ التحويل...");
          setTimeout(() => {
            router.replace("/home");
          }, 700);
          return;
        }

        setErrorMessage(detail);
        return;
      }

      if (shiftStartData.status === "pending_ocr_quota") {
        setSuccessMessage(
          "خدمة OCR غير متاحة مؤقتًا. تم حفظ الطلب وسيتم معالجته قريبًا."
        );
      } else {
        setSuccessMessage("تم بدء الوردية بنجاح.");
      }

      saveShiftStartedSuccessfullyState();
      setTimeout(() => {
        router.replace("/home");
      }, 700);
    } catch {
      setErrorMessage("تعذر الاتصال بالخادم.");
    } finally {
      setIsSubmitting(false);
    }
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
            تسجيل الخروج
          </button>

          <p className="text-xs font-semibold tracking-wide text-neutral-500">
            بدء الوردية · صورة التابلوه
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">
            التقط صورة التابلوه
          </h1>
          <p className="mt-2 text-sm text-neutral-600">
            التقط أو ارفع صورة واضحة للتابلوه لبدء الوردية.
          </p>
        </div>

        <div className="mb-5 rounded-2xl border border-black/10 bg-neutral-50 p-4">
          <p className="text-sm font-semibold text-black">رقم اللوحة</p>
          <p className="mt-1 text-sm text-neutral-600">{plateNumber}</p>
        </div>

        <div className="space-y-5">
          <div>
            <label
              htmlFor="dashboardPhoto"
              className="mb-2 block text-sm font-medium text-neutral-800"
            >
              صورة التابلوه
            </label>

            <input
              ref={fileInputRef}
              id="dashboardPhoto"
              name="dashboardPhoto"
              type="file"
              accept="image/*"
              capture="environment"
              onChange={handleImageChange}
              className="hidden"
            />

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="w-full rounded-2xl bg-black px-4 py-4 text-base font-semibold text-white transition hover:opacity-90"
            >
              التقط صورة التابلوه
            </button>

            {dashboardImage ? (
              <div className="mt-3 rounded-2xl border border-green-200 bg-green-50 px-4 py-3">
                <p className="text-sm font-medium text-green-700">تم اختيار الصورة بنجاح</p>
                <p className="mt-1 text-xs text-green-600">{dashboardImage.name}</p>
              </div>
            ) : (
              <p className="mt-2 text-sm text-neutral-400">
                {errorMessage
                  ? "يرجى التقاط صورة أوضح للتابلوه لتفعيل زر الإرسال."
                  : "لم يتم اختيار صورة بعد"}
              </p>
            )}
          </div>

          {errorMessage ? (
            <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {errorMessage}
            </div>
          ) : null}

          {successMessage ? (
            <div className="rounded-2xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
              {successMessage}
            </div>
          ) : null}

          <button
            type="button"
            onClick={handleSubmit}
            disabled={isSubmitting || !dashboardImage}
            className="w-full rounded-2xl bg-black px-4 py-4 text-base font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? "جارٍ الإرسال..." : "ابدا الشيفت من هنا"}
          </button>
        </div>
      </div>
    </main>
  );
}
