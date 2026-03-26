import type { ActionableInsight, ArticleOut } from "@/lib/types";
import { ActionBadge } from "./ActionBadge";
import { ArticleCard } from "./ArticleCard";

interface Props {
  topic: string;
  articles: ArticleOut[];
  actionable_insight: ActionableInsight;
}

export function TopicSection({ topic, articles, actionable_insight }: Props) {
  return (
    <section className="mb-10">
      <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-3">{topic}</h2>
      <div className="border-l-4 border-green-400 dark:border-green-600 pl-4 mb-4">
        <ActionBadge type={actionable_insight.type} text={actionable_insight.text} />
      </div>
      <div>
        {articles.map((article) => (
          <ArticleCard
            key={article.id}
            title={article.title}
            source={article.source}
            url={article.url}
            bullets={article.bullets}
          />
        ))}
      </div>
    </section>
  );
}
