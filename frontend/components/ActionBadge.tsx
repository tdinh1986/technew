interface Props {
  type: "Apply" | "Read More";
  text: string;
}

export function ActionBadge({ type, text }: Props) {
  const colour =
    type === "Apply"
      ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
      : "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
  return (
    <div className={`inline-flex items-start gap-2 rounded-lg px-3 py-2 text-sm ${colour}`}>
      <span className="font-semibold shrink-0">{type}:</span>
      <span>{text}</span>
    </div>
  );
}
