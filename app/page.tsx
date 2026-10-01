import { Suspense } from "react";
import ChartLoader from "@/components/ChartLoader"; 

export default function Home() {
  return (
    <main className="p-4 space-y-4">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      
      {/* This Boundary isolates the slow data fetching.
        The page loads instantly, showing the fallback 
        while cookies are checked and data is fetched.
      */}
      <Suspense fallback={<SkeletonLoader />}>
        <ChartLoader />
      </Suspense>
      
    </main>
  );
}

// A simple loading placeholder to show while fetching
function SkeletonLoader() {
  return (
    <div className="h-[400px] w-full bg-zinc-100 dark:bg-zinc-800 rounded-lg animate-pulse flex items-center justify-center">
      <span className="text-zinc-400">Loading Chart Data...</span>
    </div>
  );
}
