"use client";

import { API_BASE_URL } from "@/lib/config";
import { clearSession, getAccessToken } from "@/lib/auth";

const LAST_STATE_KEY = "last_driver_state";

const START_RESUMABLE_ROUTES = new Set(["/start-shift/dashboard-photo"]);

const END_RESUMABLE_ROUTES = new Set(["/end-shift/dashboard-photo"]);

type LandingState = {
  flow: "start_shift" | "end_shift";
  route: string;
  reason: "no_active_shift" | "active_shift";
  active_shift_id?: string | null;
  active_shift_status?: string | null;
};

type DriverResumeState =
  | {
      kind: "start_qr_scanned";
      flow: "start_shift";
      route: string;
      plateNumber: string;
    }
  | {
      kind: "start_dashboard_photo_taken";
      flow: "start_shift";
      route: string;
      plateNumber: string;
    }
  | {
      kind: "shift_started_successfully";
      flow: "end_shift";
      route: string;
    }
  | {
      kind: "end_dashboard_photo_taken";
      flow: "end_shift";
      route: string;
    }
  | {
      kind: "shift_ended_successfully";
      flow: "start_shift";
      route: string;
    };

function getSavedDriverState(): DriverResumeState | null {
  const rawState = localStorage.getItem(LAST_STATE_KEY);

  if (!rawState) {
    return null;
  }

  try {
    return JSON.parse(rawState) as DriverResumeState;
  } catch {
    localStorage.removeItem(LAST_STATE_KEY);
    return null;
  }
}

function saveDriverState(state: DriverResumeState): void {
  localStorage.setItem(LAST_STATE_KEY, JSON.stringify(state));
}

async function fetchLandingState(token: string): Promise<LandingState | null> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/landing-state`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.status === 401) {
    clearSession();
    clearLastDriverState();
    return null;
  }

  if (!response.ok) {
    throw new Error("Failed to load landing state");
  }

  return (await response.json()) as LandingState;
}

export async function getDriverLandingState(): Promise<LandingState | null> {
  const token = getAccessToken();

  if (!token) {
    clearSession();
    clearLastDriverState();
    return null;
  }

  return fetchLandingState(token);
}

function isRouteResumableForFlow(route: string, flow: LandingState["flow"]): boolean {
  const [pathname] = route.split("?");

  if (flow === "end_shift") {
    return END_RESUMABLE_ROUTES.has(pathname);
  }

  return START_RESUMABLE_ROUTES.has(pathname);
}

export function clearLastDriverState(): void {
  localStorage.removeItem(LAST_STATE_KEY);
}

export function saveStartQrScannedState(plateNumber: string): void {
  const normalizedPlate = plateNumber.trim();

  if (!normalizedPlate) {
    return;
  }

  saveDriverState({
    kind: "start_qr_scanned",
    flow: "start_shift",
    route: `/start-shift/dashboard-photo?plate_number=${encodeURIComponent(
      normalizedPlate
    )}`,
    plateNumber: normalizedPlate,
  });
}

export function saveStartDashboardPhotoTakenState(plateNumber: string): void {
  const normalizedPlate = plateNumber.trim();

  if (!normalizedPlate) {
    return;
  }

  saveDriverState({
    kind: "start_dashboard_photo_taken",
    flow: "start_shift",
    route: `/start-shift/dashboard-photo?plate_number=${encodeURIComponent(
      normalizedPlate
    )}`,
    plateNumber: normalizedPlate,
  });
}

export function saveShiftStartedSuccessfullyState(): void {
  saveDriverState({
    kind: "shift_started_successfully",
    flow: "end_shift",
    route: "/home",
  });
}

export function saveEndDashboardPhotoTakenState(): void {
  saveDriverState({
    kind: "end_dashboard_photo_taken",
    flow: "end_shift",
    route: "/end-shift/dashboard-photo",
  });
}

export function saveShiftEndedSuccessfullyState(): void {
  saveDriverState({
    kind: "shift_ended_successfully",
    flow: "start_shift",
    route: "/home",
  });
}

export async function resolveLatestDriverRoute(): Promise<string> {
  try {
    const landingState = await getDriverLandingState();

    if (!landingState) {
      return "/";
    }

    const savedState = getSavedDriverState();

    if (!savedState) {
      return landingState.route;
    }

    if (savedState.flow !== landingState.flow) {
      return landingState.route;
    }

    if (
      savedState.kind === "shift_started_successfully" ||
      savedState.kind === "shift_ended_successfully"
    ) {
      return landingState.route;
    }

    if (!isRouteResumableForFlow(savedState.route, landingState.flow)) {
      return landingState.route;
    }

    return savedState.route;
  } catch {
    return "/home";
  }
}

export async function resolveCurrentDriverRoute(): Promise<string> {
  try {
    const landingState = await getDriverLandingState();

    if (!landingState) {
      return "/";
    }

    return landingState.route;
  } catch {
    return "/home";
  }
}
