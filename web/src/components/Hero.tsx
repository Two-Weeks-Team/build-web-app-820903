"use client";

export default function Hero({ onBuilt }: { onBuilt: () => void }) {
  return (
    <header className="rounded-lg border border-border bg-card/80 p-4 shadow-board md:p-6">
      <h1 className="font-[--font-display] text-3xl md:text-4xl">Test Kitchen Meal Prep Studio</h1>
      <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
        Turn a messy goal into a structured brief, weekly board, grocery basket, and prep workflow in one pass.
      </p>
      <button onClick={onBuilt} className="mt-4 rounded-md bg-primary px-4 py-2 text-primary-foreground">
        Build Meal Plan
      </button>
    </header>
  );
}
