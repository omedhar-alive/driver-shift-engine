export function getAccessToken(): string | null {
  return localStorage.getItem("access_token");
}

export function clearSession(): void {
  localStorage.removeItem("access_token");
  localStorage.removeItem("driver_code");
  localStorage.removeItem("driver_name");
}
