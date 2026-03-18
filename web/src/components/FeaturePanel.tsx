"use client";

type Props = { rebalance: string[] };

export default function FeaturePanel({ rebalance }: Props) {
  return (
    <section className="rounded-xl border border-border bg-card/70 p-4">
      <h3 className="text-lg">Live Rebalance Indicators</h3>
      <div className="mt-3 space-y-2">
        {rebalance.map((r) => (
          <div key={r} className="pulse-rebalance rounded-md border border-border bg-muted/60 px-3 py-2 text-sm text-accent-foreground">
            {r}
          </div>
        ))}
      </div>
    </section>
  );
}
