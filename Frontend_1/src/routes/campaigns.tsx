import { createFileRoute } from "@tanstack/react-router";
import { toast } from "sonner";

import { PageHeader, StateCard } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useCampaigns } from "@/lib/api/hooks";

export const Route = createFileRoute("/campaigns")({
  head: () => ({
    meta: [
      { title: "Campaigns — Yash Technology Outreach Hub" },
      {
        name: "description",
        content: "Outreach campaigns with notes, owning company and linked message count.",
      },
      { property: "og:title", content: "Campaigns — Yash Technology Outreach Hub" },
      { property: "og:description", content: "Manage outreach campaigns and their linked messages." },
    ],
  }),
  component: CampaignsPage,
});

function CampaignsPage() {
  const query = useCampaigns();
  const campaigns = query.data ?? [];

  if (query.isError) {
    return (
      <StateCard
        title="Campaigns unavailable"
        description={query.error.message || "The /campaigns endpoint returned an error."}
        action={
          <Button onClick={() => toast.success("Please reconnect the backend and retry")}>
            Retry later
          </Button>
        }
      />
    );
  }

  if (query.isLoading) {
    return <StateCard title="Loading campaigns" description="Fetching live CRM campaigns from FastAPI." />;
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="Campaigns"
        description={`${campaigns.length} campaigns across all divisions`}
        actions={<Button onClick={() => toast.success("Campaign creation is a backend flow")}>New campaign</Button>}
      />

      {campaigns.length === 0 ? (
        <StateCard title="No campaigns found" description="Create campaigns in the backend to see them here." />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {campaigns.map((campaign) => (
            <Card key={campaign.id}>
              <CardContent className="space-y-3 py-4">
                <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-2">
                  <div className="min-w-0">
                    <p className="truncate font-medium">{campaign.name}</p>
                    <p className="truncate text-xs text-muted-foreground">
                      {campaign.company_name ?? "No company linked"}
                    </p>
                  </div>
                  <StatusBadge status="active" />
                </div>
                <p className="line-clamp-3 text-sm text-muted-foreground">{campaign.notes || "No notes yet."}</p>
                <div className="rounded-md border bg-muted/30 px-3 py-2 text-sm">
                  <p className="text-xs text-muted-foreground">Linked messages</p>
                  <p className="text-numeric text-lg font-semibold">{campaign.message_count}</p>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" className="flex-1" onClick={() => toast.success("Campaign paused in UI only")}>
                    Pause
                  </Button>
                  <Button size="sm" className="flex-1" onClick={() => toast.success("Campaign marked ready in UI only")}>
                    Approve
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
