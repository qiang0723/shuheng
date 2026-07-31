export function StatCard({
  label,
  value,
  unit,
  note,
  tone = "default",
}: {
  label: string;
  value: string | number;
  unit?: string;
  note: string;
  tone?: "default" | "warning" | "neutral";
}) {
  return (
    <article className={`stat-card ${tone}`}>
      <span>{label}</span>
      <div><strong>{value}</strong>{unit && <small>{unit}</small>}</div>
      <p>{note}</p>
    </article>
  );
}
