import { UrlDigestForm } from "@/components/UrlDigestForm";

export const metadata = {
  title: "Summarize URLs — TechNew",
};

export default function SummarizePage() {
  return (
    <main>
      <div className="max-w-2xl mx-auto px-4 pt-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Summarize URLs</h1>
        <p className="mt-1 text-gray-500 dark:text-gray-400">
          Paste article URLs to get an AI-generated digest with bullet summaries and actionable
          insights.
        </p>
      </div>
      <UrlDigestForm />
    </main>
  );
}
