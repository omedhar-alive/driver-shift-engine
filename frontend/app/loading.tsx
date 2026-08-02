export default function Loading() {
  return (
    <main className="min-h-screen bg-neutral-100 text-black">
      <div className="mx-auto min-h-screen w-full max-w-[430px] bg-white px-5 py-6">
        <div className="flex min-h-screen flex-col items-center justify-center">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-black/15 border-t-black" />
          <p className="mt-4 text-sm text-neutral-500">Loading...</p>
        </div>
      </div>
    </main>
  );
}