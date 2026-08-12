import type { ReactNode } from "react";
import { Info } from "lucide-react";

import { API_BASE_URL } from "@/lib/api/client";
import { Card, CardContent } from "@/components/ui/card";

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string | undefined;
  actions?: ReactNode | undefined;
}) {
  return (
    <header className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3 sm:flex sm:flex-wrap sm:items-center sm:justify-between">
      <div className="min-w-0">
        <h1 className="truncate text-xl font-semibold sm:text-2xl">{title}</h1>
        {description ? (
          <p className="mt-1 text-sm text-muted-foreground">{description}</p>
        ) : null}
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap gap-2">{actions}</div> : null}
    </header>
  );
}

/** Shown when the FastAPI backend could not be reached and sample data is rendered. */
export function SampleDataNotice({ isLive }: { isLive: boolean }) {
  if (isLive) return null;
  return (
    <div className="flex items-start gap-2 rounded-md border border-warning/30 bg-warning/10 px-3 py-2 text-xs text-foreground">
      <Info className="mt-0.5 size-3.5 shrink-0 text-warning" />
      <p className="min-w-0">
        Showing sample data — the FastAPI backend at <code className="font-mono">{API_BASE_URL}</code>{" "}
        is not reachable from this browser. Screens switch to live records automatically once it responds.
      </p>
    </div>
  );
}

export function SectionCardTitle({ title, hint }: { title: string; hint?: string | undefined }) {
  return (
    <div className="min-w-0">
      <h2 className="truncate text-sm font-semibold">{title}</h2>
      {hint ? <p className="text-xs text-muted-foreground">{hint}</p> : null}
    </div>
  );
}

export function StateCard({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <Card>
      <CardContent className="flex min-h-40 flex-col items-start justify-center gap-3 py-8 text-sm">
        <div className="space-y-1">
          <p className="font-medium">{title}</p>
          <p className="text-muted-foreground">{description}</p>
        </div>
        {action ? <div>{action}</div> : null}
      </CardContent>
    </Card>
  );
}
