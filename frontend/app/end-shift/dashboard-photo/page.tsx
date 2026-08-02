"use client";
export const dynamic = "force-dynamic";

import { ChangeEvent, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { clearSession, getAccessToken } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/config";
import {
  clearLastDriverState,
  saveEndDashboardPhotoTakenState,
  saveShiftEndedSuccessfullyState,
} from "@/lib/flow-state";
import { useRequireDriverFlow } from "@/lib/require-auth";

type OpenShift = {
  start_id: string;
} | null;

type ShiftEndState = {
  matched_start_id: string;
} | null;

async function parseJsonSafely(response: Response): Promise<unknown> {
  const responseText = await response.text();

  if (!responseText) {
    return null;
  }

  try {
    return JSON.parse(responseText);
  } catch {
    return null;
  }
}

export default function EndShiftDashboardPhotoPage() {
  const router = useRouter();
  const isAuthorized = useRequireDriverFlow("end_shift", "/end-shift/dashboard-photo");
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

    if (file) {
      saveEndDashboardPhotoTakenState();
    }
  }

  async function verifyEndShiftState(token: string): Promise<boolean> {
    try {
      const openShiftResponse = await fetch(`${API_BASE_URL}/api/v1/shift-starts/open`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!openShiftResponse.ok) {
        return false;
      }

      const openShiftData = (await parseJsonSafely(openShiftResponse)) as OpenShift;

      if (openShiftData !== null) {
        return false;
      }

      const latestShiftEndResponse = await fetch(`${API_BASE_URL}/api/v1/shift-ends/latest`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!latestShiftEndResponse.ok) {
        return false;
      }

      const latestShiftEndData = (await parseJsonSafely(
        latestShiftEndResponse
      )) as ShiftEndState;

      return latestShiftEndData !== null;
    } catch {
      return false;
    }
  }

  async function handleSubmit() {
    const token = getAccessToken();

    if (!token) {
      router.push("/");
      return;
    }

    if (!dashboardImage) {
      setErrorMessage("Please take a dashboard photo first.");
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

      const uploadData = (await parseJsonSafely(uploadResponse)) as {
        detail?: string;
        file_path?: string;
      } | null;

      if (!uploadResponse.ok) {
        setErrorMessage(uploadData?.detail || "Couldn't upload the photo.");
        return;
      }

      if (!uploadData?.file_path) {
        setErrorMessage("Couldn't upload the photo.");
        return;
      }

      const shiftEndResponse = await fetch(`${API_BASE_URL}/api/v1/shift-ends/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          end_dashboard_image: uploadData.file_path,
        }),
      });

      const shiftEndData = (await parseJsonSafely(shiftEndResponse)) as {
        detail?: string;
        requires_retake?: boolean;
        already_processed?: boolean;
        status?: string;
      } | null;

      if (!shiftEndResponse.ok) {
        const detail =
          typeof shiftEndData?.detail === "string"
            ? shiftEndData.detail
            : "Couldn't end the shift.";

        const requiresRetake = Boolean(shiftEndData?.requires_retake);

        if (requiresRetake) {
          clearSelectedImage();
          setErrorMessage(
            detail || "The photo isn't clear. Please take a clearer dashboard photo."
          );
          return;
        }

        setErrorMessage(detail);
        return;
      }

      if (shiftEndData?.already_processed) {
        setSuccessMessage("Shift already ended. Redirecting...");
      } else if (shiftEndData?.status === "pending_ocr_quota") {
        setSuccessMessage(
          "OCR service is temporarily unavailable. Your request has been saved and will be processed shortly."
        );
      } else {
        setSuccessMessage("Shift ended successfully.");
      }

      saveShiftEndedSuccessfullyState();
      setTimeout(() => {
        router.replace("/home");
      }, 700);
    } catch {
      const endShiftLikelySucceeded = await verifyEndShiftState(token);

      if (endShiftLikelySucceeded) {
        setSuccessMessage("Shift already ended. Redirecting...");
        saveShiftEndedSuccessfullyState();
        setTimeout(() => {
          router.replace("/home");
        }, 700);
        return;
      }

      setErrorMessage("Couldn't confirm the submission. Please try again.");
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
            End Shift · Dashboard Photo
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">
            Take a Dashboard Photo
          </h1>
          <p className="mt-2 text-sm text-neutral-600">
            Take or upload a clear dashboard photo to end the shift.
          </p>
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
                <p className="text-sm font-medium text-green-700">
                  Photo selected successfully
                </p>
                <p className="mt-1 text-xs text-green-600">{dashboardImage.name}</p>
              </div>
            ) : (
              <p className="mt-2 text-sm text-neutral-400">
                No photo selected yet
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
            {isSubmitting ? "Submitting..." : "End Shift From Here"}
          </button>
        </div>
      </div>
    </main>
  );
}
