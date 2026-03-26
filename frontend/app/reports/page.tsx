import { DigestReport } from "@/components/DigestReport";
import { EmptyState } from "@/components/EmptyState";
import { getLatestReport } from "@/lib/api";

export const revalidate = 60;

export default async function ReportsPage() {
  const response = await getLatestReport();
  if (!response.data) {
    return <EmptyState />;
  }
  return <DigestReport report={response.data} />;
}
