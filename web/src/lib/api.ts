export type PlanRequest = {
  query: string;
  preferences: {
    diet: string;
    servings: number;
    budget: number;
    cadence: string;
  };
};

export type PlanResponse = {
  summary: string;
  score: number;
  items: {
    brief: {
      servings: number;
      budget: number;
      diet: string;
      cadence: string;
      confidence: string;
      assumptions: string[];
    };
    board: Array<{ day: string; meal: string; recipe: string; macros: string; portions: string; cost: string; reason: string }>;
    basket: Array<{ group: string; ingredients: Array<{ name: string; qty: string; cost: number; pantry: boolean }> }>;
    prep_steps: Array<{ step: number; text: string; duration: string }>;
    snapshots: Array<{ id: string; name: string; created_at: string; score: number }>;
    rebalance: string[];
  };
};

export type InsightsResponse = {
  insights: string[];
  next_actions: string[];
  highlights: string[];
};

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const msg = await res.text();
    throw new Error(msg || "Request failed");
  }
  return (await res.json()) as T;
}

export async function buildPlan(payload: PlanRequest): Promise<PlanResponse> {
  const res = await fetch("/api/plan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return handle<PlanResponse>(res);
}

export async function fetchInsights(selection: string, context: string): Promise<InsightsResponse> {
  const res = await fetch("/api/insights", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ selection, context })
  });
  return handle<InsightsResponse>(res);
}
