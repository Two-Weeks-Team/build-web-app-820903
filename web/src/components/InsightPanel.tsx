"use client";

export default function InsightPanel({ refreshKey }: { refreshKey: number }) {
  return (
    <section className="rounded-lg border border-border bg-card/80 p-4 shadow-soft">
      <h2 className="font-[--font-display] text-xl">Weekly Meal Board</h2>
      <p className="mt-2 text-sm text-muted-foreground">Live rebalance indicator key: {refreshKey}</p>
    </section>
  );
}
