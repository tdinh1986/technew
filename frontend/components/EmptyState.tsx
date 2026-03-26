import { FetchButton } from "./FetchButton";

export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-24 text-center">
      <h2 className="text-2xl font-semibold text-gray-700 dark:text-gray-300">
        No digest yet
      </h2>
      <p className="text-gray-500 dark:text-gray-400">
        Fetch news to generate your first report
      </p>
      <FetchButton />
    </div>
  );
}
