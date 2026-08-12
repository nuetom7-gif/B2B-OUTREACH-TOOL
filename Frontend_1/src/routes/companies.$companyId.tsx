import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";

import { PageHeader, StateCard } from "@/components/shared/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useCompany } from "@/lib/api/hooks";

export const Route = createFileRoute("/companies/$companyId")({
  head: () => ({
    meta: [
      { title: "Company record — Yash Technology Outreach Hub" },
      {
        name: "description",
        content: "Full company record with CRM source metadata and product fits.",
      },
      { property: "og:title", content: "Company record — Yash Technology Outreach Hub" },
      { property: "og:description", content: "Company details, review flags and discovery source metadata." },
    ],
  }),
  component: CompanyDetailPage,
});

function CompanyDetailPage() {
  const { companyId } = Route.useParams();
  const query = useCompany(companyId);

  if (query.isLoading) {
    return <StateCard title="Loading company" description="Fetching the company record from FastAPI." />;
  }

  if (query.isError || !query.data) {
    return (
      <StateCard
        title="Company detail not available"
        description="The backend currently does not expose GET /companies/{id}, so this screen cannot resolve a company record yet."
        action={
          <Button asChild>
            <Link to="/companies">Back to companies</Link>
          </Button>
        }
      />
    );
  }

  const company = query.data;

  return (
    <div className="space-y-5">
      <Button variant="ghost" size="sm" asChild className="-ml-2 w-fit">
        <Link to="/companies">
          <ArrowLeft className="size-4" /> Companies
        </Link>
      </Button>

      <PageHeader
        title={company.name}
        description={`${company.industry} · ${company.source}`}
        actions={<Badge variant="secondary">{company.sync_status}</Badge>}
      />

      <div className="flex flex-wrap items-center gap-2">
        <Badge variant={company.needs_manual_review ? "warning" : "outline"}>
          {company.needs_manual_review ? "manual review" : "ready"}
        </Badge>
        <Badge variant="secondary">{company.lead_score} lead score</Badge>
        <Badge variant="outline">{company.contact_count} contacts</Badge>
        {company.fallback_contact_used ? <Badge variant="secondary">fallback contact used</Badge> : null}
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <h2 className="text-sm font-semibold">CRM metadata</h2>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm sm:grid-cols-2">
            {[
              ["Source provider", company.source_provider ?? "—"],
              ["Source record", company.source_record_id ?? "—"],
              ["Apollo org id", company.apollo_organization_id ?? "—"],
              ["Owner id", company.owner_id?.toString() ?? "—"],
              ["Assignment", company.assignment_status],
              ["Assignment source", company.assignment_source ?? "—"],
              ["Discovery contacts returned", String(company.discovery_contacts_returned)],
              ["Contact status", company.contact_status],
            ].map(([label, value]) => (
              <div key={label} className="min-w-0">
                <p className="text-xs text-muted-foreground">{label}</p>
                <p className="truncate font-medium">{value}</p>
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <h2 className="text-sm font-semibold">Notes</h2>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p className="text-muted-foreground">{company.notes || "No notes available."}</p>
            <Separator />
            <div className="space-y-2">
              <p className="text-xs text-muted-foreground">Product fits</p>
              <div className="flex flex-wrap gap-2">
                {company.product_fits.length > 0 ? (
                  company.product_fits.map((fit) => (
                    <Badge key={fit} variant="secondary">
                      {fit}
                    </Badge>
                  ))
                ) : (
                  <span className="text-xs text-muted-foreground">None recorded</span>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
