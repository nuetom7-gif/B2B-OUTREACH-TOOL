import { cn } from "@/lib/utils";

const TONES = {
  neutral: "bg-muted text-muted-foreground border-transparent",
  success: "bg-success/12 text-success border-success/20",
  warning: "bg-warning/15 text-warning-foreground border-warning/30 dark:text-warning",
  info: "bg-info/12 text-info border-info/20",
  primary: "bg-primary/10 text-primary border-primary/20",
  danger: "bg-destructive/10 text-destructive border-destructive/20",
} as const;

export type Tone = keyof typeof TONES;

const MAP: Record<string, Tone> = {
  // qualification
  qualified: "success",
  review: "warning",
  disqualified: "danger",
  // company / contact status
  new: "neutral",
  researching: "info",
  ready_for_outreach: "primary",
  in_campaign: "info",
  engaged: "success",
  customer: "success",
  opted_out: "danger",
  pending: "warning",
  pending_review: "warning",
  manual_review: "warning",
  needs_manual_review: "warning",
  synced: "success",
  unassigned: "neutral",
  verified: "info",
  contacted: "primary",
  replied: "success",
  meeting: "success",
  bounced: "danger",
  // campaigns / drafts / runs
  draft: "neutral",
  pending_approval: "warning",
  scheduled: "info",
  active: "success",
  paused: "warning",
  completed: "primary",
  approved: "success",
  rejected: "danger",
  sent: "primary",
  queued: "neutral",
  running: "info",
  failed: "danger",
  delivered: "primary",
  opened: "info",
  unsubscribed: "danger",
  open: "warning",
  in_progress: "info",
  resolved: "success",
};

export function StatusBadge({ status, className }: { status: string; className?: string }) {
  const tone = MAP[status] ?? "neutral";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] font-medium capitalize whitespace-nowrap",
        TONES[tone],
        className,
      )}
    >
      <span className="size-1.5 rounded-full bg-current opacity-70" />
      {status.replace(/_/g, " ")}
    </span>
  );
}

export function ConfidenceBar({ value }: { value: number }) {
  const tone = value >= 78 ? "bg-success" : value >= 58 ? "bg-warning" : "bg-destructive";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-14 overflow-hidden rounded-full bg-muted">
        <div className={cn("h-full rounded-full", tone)} style={{ width: `${value}%` }} />
      </div>
      <span className="text-xs text-numeric text-muted-foreground">{value}%</span>
    </div>
  );
}
