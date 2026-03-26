interface Props {
  title: string;
  source: string;
  url: string;
  bullets: string[];
}

export function ArticleCard({ title, source, url, bullets }: Props) {
  return (
    <div className="py-3 border-b border-gray-100 dark:border-gray-800 last:border-0">
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="font-medium text-gray-900 dark:text-gray-100 hover:underline"
      >
        {title}
      </a>
      <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{source}</p>
      <ul className="mt-2 space-y-1">
        {bullets.map((b, i) => (
          <li key={i} className="text-sm text-gray-600 dark:text-gray-400 flex gap-2">
            <span className="text-gray-300 dark:text-gray-600 shrink-0">•</span>
            {b}
          </li>
        ))}
      </ul>
    </div>
  );
}
