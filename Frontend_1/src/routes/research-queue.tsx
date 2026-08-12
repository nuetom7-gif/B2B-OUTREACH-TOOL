import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";

import { PageHeader, StateCard } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { Card, CardContent } from "@/components/ui/card";
import { useManualReview } from "@/lib/api/hooks";

export const Route = createFileRoute("/research-queue")({
  head: () => ({
    meta: [
      { title: "Research Queue — Yash Technology Outreach Hub" },
      { name: "description", content: "Manual review queue for discovery records requiring follow-up." },
      { property: "og:title", content: "Research Queue — Yash Technology Outreach Hub" },
      { property: "og:description", content: "Discovery records routed for manual review and remediation." },
    ],
  }),
  component: ResearchQueuePage,
});

function ResearchQueuePage() {
  const [offset, setOffset] = useState(0);
  const query = useManualReview(offset);
  const manualReview = query.data?.items ?? [];

  if (query.isError) {
    return (
      <StateCard
        title="Research queue unavailable"
        description={query.error.message || "The discovery staging endpoint returned an error."}
      />
    );
  }

  if (query.isLoading) {
    return <StateCard title="Loading research queue" description="Fetching manual review records from FastAPI." />;
  }

  return (
    <div className="space-y-5">
      <PageHeader title="Research Queue" description={`${query.data?.total ?? 0} records in manual review`} />

      {manualReview.length === 0 ? (
        <StateCard title="Queue is empty" description="No discovery records currently require manual review." />
      ) : (
        <div className="space-y-2">
          {manualReview.map((record) => (
            <Card key={record.id}>
              <CardContent className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 py-3">
                <div className="min-w-0">
                  <p className="truncate font-medium">{record.company_name ?? record.person_name ?? "Unknown record"}</p>
                  <p className="truncate text-xs text-muted-foreground">
                    {record.reason_category} · {record.decision_stage} · {record.provider_name}
                  </p>
                  <p className="truncate text-xs text-muted-foreground">
                    {record.company_domain ?? "No domain"} · {record.person_title ?? "No title"}
                  </p>
                </div>
                <StatusBadge status={record.final_status} />
              </CardContent>
            </Card>
          ))}
          <div className="flex items-center justify-between pt-3 text-sm text-muted-foreground">
            <span>Showing {offset + 1}-{Math.min(offset + manualReview.length, query.data?.total ?? 0)} of {query.data?.total ?? 0}</span>
            <div className="flex gap-2">
              <button className="rounded border px-3 py-1 disabled:opacity-50" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 50))}>Previous</button>
              <button className="rounded border px-3 py-1 disabled:opacity-50" disabled={offset + manualReview.length >= (query.data?.total ?? 0)} onClick={() => setOffset(offset + 50)}>Next</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
