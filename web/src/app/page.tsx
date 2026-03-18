"use client";

import { useMemo, useState } from "react";
import { buildPlan, PlanResponse } from "@/lib/api";
import StatePanel from "@/components/StatePanel";
import StatsStrip from "@/components/StatsStrip";
import FeaturePanel from "@/components/FeaturePanel";
import ReferenceShelf from "@/components/ReferenceShelf";

const seeds = [
  "3-day high-protein lunch prep for Alex with a $40 budget",
  "Family weeknight dinner plan for 4 with one vegetarian meal and 30-minute cook limit",
  "Low-carb solo meal plan with batch cooking on Sunday and leftovers for lunches"
];

const demo: PlanResponse = {
  summary: "One-pass plan generated from messy goal into structured brief, weekly board, grocery basket, and prep flow.",
  score: 92,
  items: {
    brief: { servings: 3, budget: 40, diet: "balanced", cadence: "Sun prep + Tue top-up", confidence: "High", assumptions: ["Pantry has oil/spices", "Microwave reheats available"] },
    board: [
      { day: "Mon", meal: "Lunch", recipe: "Turkey Quinoa Power Bowl", macros: "42P/48C/16F", portions: "3 boxes", cost: "$3.90", reason: "Protein target + budget fit" },
      { day: "Tue", meal: "Lunch", recipe: "Chickpea Tuna Crunch Wrap", macros: "38P/44C/14F", portions: "3 wraps", cost: "$3.45", reason: "Fast assembly, office-friendly" },
      { day: "Wed", meal: "Lunch", recipe: "Greek Chicken Pasta Jar", macros: "45P/50C/15F", portions: "3 jars", cost: "$4.10", reason: "Leftover-safe and reheatable" }
    ],
    basket: [
      { group: "Proteins", ingredients: [{ name: "Turkey breast", qty: "1.2 lb", cost: 8.5, pantry: false }, { name: "Canned tuna", qty: "3 cans", cost: 4.8, pantry: false }] },
      { group: "Produce", ingredients: [{ name: "Cucumber", qty: "2", cost: 1.5, pantry: false }, { name: "Red onion", qty: "1", cost: 0.8, pantry: false }] },
      { group: "Pantry", ingredients: [{ name: "Quinoa", qty: "2 cups", cost: 0, pantry: true }, { name: "Olive oil", qty: "6 tbsp", cost: 0, pantry: true }] }
    ],
    prep_steps: [
      { step: 1, text: "Batch-cook quinoa and roast turkey together.", duration: "35 min" },
      { step: 2, text: "Assemble 3 bowls + 3 wraps + 3 jars.", duration: "20 min" },
      { step: 3, text: "Label containers by day and add dressing cups.", duration: "10 min" }
    ],
    snapshots: [
      { id: "s1", name: "Alex Protein Lunch v1", created_at: "Today 8:12 AM", score: 92 },
      { id: "s2", name: "Vegetarian Swap Trial", created_at: "Yesterday", score: 88 },
      { id: "s3", name: "$35 Tight Budget Pass", created_at: "Mon", score: 84 }
    ],
    rebalance: ["Budget -$3.20 via pantry quinoa", "Protein +9g/meal after turkey swap", "Prep time -12m by parallel roasting"]
  }
};

export default function Page() {
  const [query, setQuery] = useState(seeds[0]);
  const [diet, setDiet] = useState("balanced");
  const [mode, setMode] = useState<"loading" | "empty" | "error" | "success">("success");
  const [error, setError] = useState("");
  const [plan, setPlan] = useState<PlanResponse>(demo);

  const totalCost = useMemo(() => plan.items.basket.flatMap((g) => g.ingredients).reduce((sum, i) => sum + (i.pantry ? 0 : i.cost), 0), [plan]);

  async function onBuild() {
    try {
      setMode("loading");
      setError("");
      const next = await buildPlan({ query, preferences: { diet, servings: 3, budget: 40, cadence: "Sun prep + Tue top-up" } });
      setPlan(next);
      setMode("success");
    } catch (e) {
      setMode("error");
      setError(e instanceof Error ? e.message : "Could not build meal plan");
    }
  }

  return (
    <main className="mx-auto max-w-[1400px] p-4 md:p-6">
      <header className="mb-4 rounded-xl border border-border bg-card/70 p-4 fade-in-up">
        <h1 className="text-3xl">Test Kitchen Meal Planning Studio</h1>
        <p className="mt-1 text-sm text-muted-foreground">Turn messy goals into a filled weekly board, grocery basket, pantry shelf, and prep workflow.</p>
      </header>

      <StatsStrip score={plan.score} totalCost={totalCost} proteinMeals={plan.items.board.length} containers={9} />

      <section className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-[320px_1fr_360px]">
        <div className="space-y-4">
          <div className="rounded-xl border border-border bg-card/80 p-4">
            <h2 className="text-xl">Build Meal Plan</h2>
            <label className="mt-3 block text-xs text-muted-foreground">What meal prep goal do you have?</label>
            <textarea value={query} onChange={(e) => setQuery(e.target.value)} className="mt-1 h-28 w-full rounded-md border border-border bg-muted/60 p-2 text-sm" />
            <div className="mt-2 flex flex-wrap gap-2">
              {seeds.map((s) => <button key={s} onClick={() => setQuery(s)} className="rounded-full border border-border bg-muted px-2 py-1 text-xs">Quick Fill</button>)}
            </div>
            <label className="mt-3 block text-xs text-muted-foreground">Constraints, budget, diet, and schedule</label>
            <select value={diet} onChange={(e) => setDiet(e.target.value)} className="mt-1 w-full rounded-md border border-border bg-muted/60 p-2 text-sm">
              <option value="balanced">Balanced</option><option value="vegetarian">Vegetarian</option><option value="low-carb">Low-carb</option>
            </select>
            <button onClick={onBuild} className="mt-3 w-full rounded-md bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground">Build Meal Plan</button>
          </div>
          <div className="rounded-xl border border-border bg-card/80 p-4">
            <h3 className="text-lg">Structured Meal Brief</h3>
            <p className="text-sm text-muted-foreground">Servings {plan.items.brief.servings} · Budget ${plan.items.brief.budget} · Diet {plan.items.brief.diet}</p>
            <p className="mt-2 text-xs text-success">Confidence: {plan.items.brief.confidence}</p>
          </div>
          <StatePanel mode={mode} message={error || plan.summary} />
        </div>

        <div className="space-y-4">
          <section className="rounded-xl border border-border bg-card/70 p-4">
            <h2 className="text-xl">Weekly Meal Board</h2>
            <div className="mt-3 grid gap-3 md:grid-cols-3">
              {plan.items.board.map((c) => (
                <article key={`${c.day}-${c.recipe}`} className="rounded-lg border border-border bg-muted/40 p-3 shadow-card">
                  <p className="text-xs text-muted-foreground">{c.day} · {c.meal}</p>
                  <h3 className="mt-1 text-base">{c.recipe}</h3>
                  <p className="text-xs text-accent-foreground">{c.macros} • {c.portions} • {c.cost}</p>
                </article>
              ))}
            </div>
          </section>
          <section className="rounded-xl border border-border bg-card/70 p-4">
            <h3 className="text-lg">Prep Workflow Strip</h3>
            <div className="mt-2 flex flex-col gap-2">
              {plan.items.prep_steps.map((s) => <div key={s.step} className="rounded-md border border-border bg-muted/60 p-2 text-sm">Step {s.step}: {s.text} <span className="text-muted-foreground">({s.duration})</span></div>)}
            </div>
          </section>
          <FeaturePanel rebalance={plan.items.rebalance} />
        </div>

        <div className="space-y-4">
          <ReferenceShelf basket={plan.items.basket} />
          <section className="rounded-xl border border-border bg-card/80 p-4">
            <h3 className="text-lg">Saved Prep Snapshots</h3>
            <div className="mt-2 space-y-2">
              {plan.items.snapshots.map((s) => <button key={s.id} className="w-full rounded-md border border-border bg-muted/50 px-3 py-2 text-left text-sm">{s.name} · {s.created_at} · score {s.score}</button>)}
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}
