export interface ApiResponse<T> {
  data: T | null;
  error: string | null;
  meta: Record<string, unknown>;
}

export interface ArticleOut {
  id: string;
  title: string;
  source: string;
  url: string;
  bullets: string[];
}

export interface ActionableInsight {
  type: "Apply" | "Read More";
  text: string;
}

export interface TopicSection {
  topic: string;
  article_count: number;
  actionable_insight: ActionableInsight;
  articles: ArticleOut[];
}

export interface DigestReport {
  id: string;
  created_at: string;
  article_count: number;
  topic_sections: TopicSection[];
}

export interface DigestReportListItem {
  id: string;
  created_at: string;
  article_count: number;
}

export interface FetchJobOut {
  id: string;
  status: "queued" | "running" | "done" | "failed";
  started_at: string | null;
  completed_at: string | null;
  articles_added: number | null;
  error_message: string | null;
  report_id: string | null;
}

export interface Source {
  id: string;
  type: "rss" | "newsapi" | "hackernews";
  url: string;
  name: string | null;
  enabled: boolean;
  last_fetched_at: string | null;
}

export interface SourceCreate {
  type: "rss" | "newsapi" | "hackernews";
  url: string;
  name?: string;
}

export interface SourceUpdate {
  enabled?: boolean;
  url?: string;
  name?: string;
}

export interface TopicFilter {
  id: string;
  keyword: string;
  active: boolean;
  created_at: string;
}

export interface TopicFilterCreate {
  keyword: string;
}
