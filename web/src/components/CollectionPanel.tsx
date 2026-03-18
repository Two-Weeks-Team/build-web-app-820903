"use client";

export default function CollectionPanel({ refreshKey }: { refreshKey: number }) {
  return (
    <aside className="rounded-lg border border-border bg-card/80 p-4 shadow-soft">
      <h2 className="font-[--font-display] text-xl">Grocery Basket & Saved Snapshots</h2>
      <p className="mt-2 text-sm text-muted-foreground">Snapshot sync token: {refreshKey}</p>
    </aside>
  );
}
