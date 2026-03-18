"use client";

type Ingredient = { name: string; qty: string; pantry: boolean; cost: number };
type Group = { group: string; ingredients: Ingredient[] };

export default function ReferenceShelf({ basket }: { basket: Group[] }) {
  const spend = basket.flatMap((g) => g.ingredients).reduce((a, i) => a + (i.pantry ? 0 : i.cost), 0);
  return (
    <aside className="rounded-xl border border-border bg-card/75 p-4">
      <h3 className="text-lg">Grocery Basket + Pantry Shelf</h3>
      <p className="text-xs text-muted-foreground">Mise en place trays with quantity rollups — est. spend ${spend.toFixed(2)}</p>
      <div className="mt-3 space-y-3">
        {basket.map((g) => (
          <div key={g.group}>
            <p className="mb-1 text-xs uppercase tracking-wide text-muted-foreground">{g.group}</p>
            <div className="flex flex-wrap gap-2">
              {g.ingredients.map((i) => (
                <span key={i.name} className={`rounded-full border px-2 py-1 text-xs ${i.pantry ? "bg-muted text-muted-foreground" : "bg-accent/20 text-accent-foreground"}`}>
                  {i.name} · {i.qty} · {i.pantry ? "Pantry" : `$${i.cost.toFixed(2)}`}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}
