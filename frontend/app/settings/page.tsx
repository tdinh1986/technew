import { SourceList } from "@/components/SourceList";
import { TopicList } from "@/components/TopicList";

export default function SettingsPage() {
  return (
    <div className="max-w-2xl mx-auto px-4 py-8 space-y-10">
      <section>
        <h2 className="text-lg font-semibold mb-4">News Sources</h2>
        <SourceList />
      </section>
      <section>
        <h2 className="text-lg font-semibold mb-4">Topic Filters</h2>
        <TopicList />
      </section>
    </div>
  );
}
