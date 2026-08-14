import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { toast } from "sonner";

import { PageHeader, StateCard } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { apiPost } from "@/lib/api/client";
import { useManualReview } from "@/lib/api/hooks";

export const Route = createFileRoute("/research-queue")({
  head: () => ({
    meta: [
      { title: "Research Queue - Yash Technology Outreach Hub" },
      { name: "description", content: "Manual review queue for discovery records requiring follow-up." },
      { property: "og:title", content: "Research Queue - Yash Technology Outreach Hub" },
      { property: "og:description", content: "Discovery records routed for manual review and remediation." },
    ],
  }),
  component: ResearchQueuePage,
});

function ResearchQueuePage() {
  const [offset, setOffset] = useState(0);
  const [decidingId, setDecidingId] = useState<number | null>(null);
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

  async function decide(recordId: number, decision: "approve" | "reject") {
    setDecidingId(recordId);
    try {
      const result = await apiPost<{ contacts_imported: number }>(`/discovery/staging/${recordId}/review`, { decision });
      toast.success(
        decision === "approve"
          ? `Approved. ${result.contacts_imported} contact(s) imported.`
          : "Record rejected and removed from the review queue.",
      );
      await query.refetch();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not save the review decision");
    } finally {
      setDecidingId(null);
    }
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="Research Queue"
        description={`${query.data?.total ?? 0} records need a decision. Approve keeps/imports the company and staged contacts; Reject closes this discovery record without marking anyone do-not-contact.`}
      />

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
                    Reason: {record.reason_category.replaceAll("_", " ")} | Score: {record.score}
                  </p>
                  <p className="truncate text-xs text-muted-foreground">
                    {record.company_domain ?? "No domain"} | {record.person_title ?? "No title"}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={record.final_status} />
                  <Button size="sm" disabled={decidingId !== null} onClick={() => void decide(record.id, "approve")}>
                    {decidingId === record.id ? "Saving..." : "Approve"}
                  </Button>
                  <Button size="sm" variant="outline" disabled={decidingId !== null} onClick={() => void decide(record.id, "reject")}>
                    Reject
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
          <div className="flex items-center justify-between pt-3 text-sm text-muted-foreground">
            <span>Showing {offset + 1}-{Math.min(offset + manualReview.length, query.data?.total ?? 0)} of {query.data?.total ?? 0}</span>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 50))}>Previous</Button>
              <Button variant="outline" size="sm" disabled={offset + manualReview.length >= (query.data?.total ?? 0)} onClick={() => setOffset(offset + 50)}>Next</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
