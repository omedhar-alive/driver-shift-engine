"use client";

import { useEffect, useRef } from "react";
import QrScannerLib from "qr-scanner";

type QrScannerProps = {
  onScanSuccess: (decodedText: string) => void | Promise<void>;
  onScanError?: (message: string) => void;
  resetKey?: number;
};

export default function QrScanner({
  onScanSuccess,
  onScanError,
  resetKey = 0,
}: QrScannerProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const scannerRef = useRef<QrScannerLib | null>(null);
  const hasResolvedRef = useRef(false);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    let isMounted = true;
    let startTimeout: ReturnType<typeof setTimeout> | null = null;

    const scanner = new QrScannerLib(
      video,
      async (result) => {
        if (!isMounted || hasResolvedRef.current) return;

        const value = result.data.trim();
        if (!value) return;

        hasResolvedRef.current = true;

        try {
          await scanner.stop();
        } catch {}

        await onScanSuccess(value);
      },
      {
        preferredCamera: "environment",
        returnDetailedScanResult: true,
        maxScansPerSecond: 25,
      }
    );

    scannerRef.current = scanner;

    startTimeout = setTimeout(() => {
      scanner.start().catch((error: unknown) => {
        const message = error instanceof Error ? error.name : String(error);

        if (!isMounted) return;
        if (message === "AbortError") return;

        console.error("QR scanner start error:", error);

        if (!hasResolvedRef.current) {
          onScanError?.("Couldn't start the QR scanner.");
        }
      });
    }, 150);

    return () => {
      isMounted = false;
      hasResolvedRef.current = false;

      if (startTimeout) {
        clearTimeout(startTimeout);
      }

      const currentScanner = scannerRef.current;
      scannerRef.current = null;

      if (currentScanner) {
        currentScanner.destroy();
      }
    };
  }, [onScanSuccess, onScanError, resetKey]);

  return (
    <div className="relative h-[320px] w-full overflow-hidden rounded-2xl bg-black">
      <video
        ref={videoRef}
        className="h-full w-full object-cover"
        playsInline
        muted
      />

      <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
        <div className="h-[220px] w-[220px] rounded-2xl border-4 border-white/90" />
      </div>

      <div className="pointer-events-none absolute bottom-4 left-1/2 -translate-x-1/2 rounded-full bg-black/55 px-3 py-1 text-xs text-white">
        Align QR within frame
      </div>
    </div>
  );
}