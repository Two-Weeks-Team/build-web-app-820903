"use client";

type Props = { score: number; totalCost: number; proteinMeals: number; containers: number };

export default function StatsStrip({ score, totalCost, proteinMeals, containers }: Props) {
  const items = [
    ["Plan Confidence", `${score}%`],
    ["Basket Total", `$${totalCost.toFixed(2)}`],
    ["High-Protein Slots", `${proteinMeals}`],
    ["Prep Containers", `${containers}`]
  ];
  return (
    <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
      {items.map(([k, v]) => (
        <div key={k} className="rounded-lg border border-border bg-card/80 p-3 shadow-card">
          <p className="text-xs text-muted-foreground">{k}</p>
          <p className="text-lg font-semibold text-foreground">{v}</p>
        </div>
      ))}
    </div>
  );
}
