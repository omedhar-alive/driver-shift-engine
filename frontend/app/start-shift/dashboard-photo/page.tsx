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
      setErrorMessage("Plate number is missing.");
      return;
    }

    if (!dashboardImage) {
      setErrorMessage("Please select a dashboard photo.");
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
        setErrorMessage(uploadData.detail || "Couldn't upload the photo.");
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
            : "Couldn't start the shift.";

        const requiresRetake = Boolean(shiftStartData.requires_retake);

        if (requiresRetake) {
          clearSelectedImage();
          setErrorMessage(
            detail || "The photo isn't clear. Please take a clearer dashboard photo."
          );
          return;
        }

        if (detail.toLowerCase().includes("open shift")) {
          setErrorMessage("You already have an active shift. Redirecting...");
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
          "OCR service is temporarily unavailable. Your request has been saved and will be processed shortly."
        );
      } else {
        setSuccessMessage("Shift started successfully.");
      }

      saveShiftStartedSuccessfullyState();
      setTimeout(() => {
        router.replace("/home");
      }, 700);
    } catch {
      setErrorMessage("Could not connect to the server.");
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
            Log Out
          </button>

          <p className="text-xs font-semibold tracking-wide text-neutral-500">
            Start Shift · Dashboard Photo
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">
            Take a Dashboard Photo
          </h1>
          <p className="mt-2 text-sm text-neutral-600">
            Take or upload a clear dashboard photo to start the shift.
          </p>
        </div>

        <div className="mb-5 rounded-2xl border border-black/10 bg-neutral-50 p-4">
          <p className="text-sm font-semibold text-black">Plate Number</p>
          <p className="mt-1 text-sm text-neutral-600">{plateNumber}</p>
        </div>

        <div className="space-y-5">
          <div>
            <label
              htmlFor="dashboardPhoto"
              className="mb-2 block text-sm font-medium text-neutral-800"
            >
              Dashboard Photo
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
              Take Dashboard Photo
            </button>

            {dashboardImage ? (
              <div className="mt-3 rounded-2xl border border-green-200 bg-green-50 px-4 py-3">
                <p className="text-sm font-medium text-green-700">Photo selected successfully</p>
                <p className="mt-1 text-xs text-green-600">{dashboardImage.name}</p>
              </div>
            ) : (
              <p className="mt-2 text-sm text-neutral-400">
                {errorMessage
                  ? "Please take a clearer dashboard photo to enable the submit button."
                  : "No photo selected yet"}
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
            {isSubmitting ? "Submitting..." : "Start Shift From Here"}
          </button>
        </div>
      </div>
    </main>
  );
}
