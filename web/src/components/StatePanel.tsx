"use client";

type Props = {
  mode: "loading" | "empty" | "error" | "success";
  message?: string;
};

export default function StatePanel({ mode, message }: Props) {
  const palette = {
    loading: "text-warning",
    empty: "text-muted-foreground",
    error: "text-destructive",
    success: "text-success"
  }[mode];

  return (
    <div className="rounded-lg border border-border bg-card/70 p-3 text-sm">
      <p className={`font-medium ${palette}`}>{mode.toUpperCase()}</p>
      <p className="mt-1 text-muted-foreground">{message}</p>
    </div>
  );
}
