import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Play, RefreshCw, Radar, Server, Coins, Activity } from "lucide-react";
import { toast } from "sonner";

import { PageHeader, StateCard, SectionCardTitle } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiPost } from "@/lib/api/client";
import { useDiscoveryProfiles, useDiscoveryRuns, useDiscoveryStaging, useDiscoveryStagingDetail } from "@/lib/api/hooks";

export const Route = createFileRoute("/discovery")({
  head: () => ({
    meta: [
      { title: "Discovery — Yash Technology Outreach Hub" },
      {
        name: "description",
        content: "Run Apollo-powered company and decision-maker discovery by backend profile and geography.",
      },
      { property: "og:title", content: "Discovery — Yash Technology Outreach Hub" },
      {
        property: "og:description",
        content: "Launch discovery runs and monitor API usage, credits and search diagnostics.",
      },
    ],
  }),
  component: DiscoveryPage,
});

function DiscoveryPage() {
  const profiles = useDiscoveryProfiles();
  const runs = useDiscoveryRuns();
  const staging = useDiscoveryStaging();
  const [profileName, setProfileName] = useState("");
  const [country, setCountry] = useState("India");
  const [state, setState] = useState<string>("any");
  const [city, setCity] = useState("");
  const [companyLimit, setCompanyLimit] = useState("50");
  const [contactsPerCompany, setContactsPerCompany] = useState("2");
  const [submitting, setSubmitting] = useState(false);

  const enabledProfiles = profiles.data ?? [];
  const selectedProfile = enabledProfiles.find((profile) => profile.profile_name === profileName);
  const latestRun = useMemo(() => runs.data?.[0] ?? null, [runs.data]);
  const latestStage = useMemo(() => staging.data?.items[0] ?? null, [staging.data]);
  const stageDetail = useDiscoveryStagingDetail(latestStage?.id ?? null);

  if (profiles.isError || runs.isError || staging.isError) {
    const message = profiles.error?.message ?? runs.error?.message ?? staging.error?.message ?? "Discovery endpoints are unavailable.";
    return <StateCard title="Discovery unavailable" description={message} />;
  }

  async function runDiscovery() {
    if (!profileName) {
      toast.error("Select a discovery profile first");
      return;
    }
    setSubmitting(true);
    try {
      await apiPost("/discovery/run", {
        profile_name: profileName,
        country,
        state: state === "any" ? null : state,
        city: city.trim() || null,
        company_limit: Number(companyLimit),
        contacts_per_company: Number(contactsPerCompany),
      });
      toast.success("Discovery run queued");
      await Promise.all([runs.refetch(), staging.refetch()]);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not reach the discovery engine");
    } finally {
      setSubmitting(false);
    }
  }

  if (profiles.isLoading || runs.isLoading || staging.isLoading) {
    return <StateCard title="Loading discovery" description="Fetching live profiles, runs and diagnostics." />;
  }

  const rawRecord = stageDetail.data?.raw_organization ?? {};
  const peopleResponse = stageDetail.data?.raw_people_response ?? {};
  const normalizedCompany = stageDetail.data?.normalized_company ?? {};
  const normalizedContacts = stageDetail.data?.normalized_contacts ?? [];
  const qualificationInput = stageDetail.data?.qualification_input ?? {};
  const recordProgress = latestRun && latestRun.companies_found > 0
    ? Math.min(
        100,
        Math.round(
          ((latestRun.qualification_imported_count + latestRun.qualification_manual_review_count + latestRun.qualification_rejected_count) /
            Math.max(1, latestRun.companies_found)) *
            100,
        ),
      )
    : 0;

  return (
    <div className="space-y-5">
      <PageHeader
        title="Discovery"
        description="Search Apollo for companies and decision makers that match a backend ICP profile."
        actions={
          <Button variant="outline" onClick={() => void Promise.all([profiles.refetch(), runs.refetch(), staging.refetch()])}>
            <RefreshCw className="size-4" /> Refresh
          </Button>
        }
      />

      <div className="grid gap-4 xl:grid-cols-[380px_minmax(0,1fr)]">
        <Card className="h-fit">
          <CardHeader>
            <SectionCardTitle title="New discovery run" hint="Parameters are passed to the backend engine" />
          </CardHeader>
          <CardContent className="space-y-3.5">
            <div className="space-y-1.5">
              <Label>Profile</Label>
              <Select value={profileName} onValueChange={setProfileName}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a profile" />
                </SelectTrigger>
                <SelectContent>
                  {enabledProfiles.map((profile) => (
                    <SelectItem key={profile.profile_name} value={profile.profile_name}>
                      {profile.profile_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {selectedProfile ? (
              <div className="space-y-3 rounded-lg border border-border/70 bg-muted/20 p-3">
                <div>
                  <p className="text-sm font-medium">Apollo search criteria</p>
                  <p className="text-xs text-muted-foreground">Read-only criteria from the selected backend profile.</p>
                </div>
                <CriteriaTags label="Company keywords" values={selectedProfile.company_keywords} />
                <CriteriaTags label="Primary industry signals" values={selectedProfile.apollo_industries} />
                <CriteriaTags label="Related industry signals" values={selectedProfile.related_industries} />
              </div>
            ) : null}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Country</Label>
                <Input value={country} onChange={(e) => setCountry(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label>State (optional)</Label>
                <Input value={state} onChange={(e) => setState(e.target.value)} placeholder="Any state" />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>City / district (optional)</Label>
              <Input value={city} onChange={(e) => setCity(e.target.value)} placeholder="Aurangabad" />
              <p className="text-xs text-muted-foreground">Apollo will search company headquarters in this city, state and country.</p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Company limit</Label>
                <Input value={companyLimit} onChange={(e) => setCompanyLimit(e.target.value)} type="number" min={1} />
              </div>
              <div className="space-y-1.5">
                <Label>Contacts / company</Label>
                <Input value={contactsPerCompany} onChange={(e) => setContactsPerCompany(e.target.value)} type="number" min={1} />
              </div>
            </div>
            <Button className="w-full" onClick={runDiscovery} disabled={submitting || !profileName}>
              <Play className="size-4" /> {submitting ? "Queuing…" : "Run discovery"}
            </Button>
            <p className="text-xs text-muted-foreground">
              The backend applies throttling, opt-out filtering and qualification.
            </p>
          </CardContent>
        </Card>

        <div className="min-w-0 space-y-4">
          <Card>
            <CardHeader className="flex-row items-center justify-between gap-3">
              <SectionCardTitle
                title="Latest run"
                hint={latestRun ? `${latestRun.product_name} · ${latestRun.search_frequency}` : "No runs yet"}
              />
              {latestRun ? <StatusBadge status={latestRun.status} /> : null}
            </CardHeader>
            <CardContent className="space-y-4">
              {latestRun ? (
                <>
                  <div>
                    <div className="mb-1.5 flex items-center justify-between text-sm">
                      <span className="truncate text-muted-foreground">
                        {latestRun.status === "running"
                          ? "Live counts refresh every 2 seconds"
                          : `Started ${new Date(latestRun.started_at).toLocaleString()}`}
                      </span>
                      <span className="text-numeric font-medium">{recordProgress}%</span>
                    </div>
                    <Progress value={recordProgress} />
                  </div>
                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                    {[
                      { label: "API calls", value: latestRun.api_calls_used, icon: <Server className="size-3.5" /> },
                      { label: "Credits left", value: latestRun.quota_remaining ?? 0, icon: <Coins className="size-3.5" /> },
                      { label: "Companies", value: latestRun.companies_found, icon: <Radar className="size-3.5" /> },
                      { label: "Contacts", value: latestRun.contacts_found, icon: <Activity className="size-3.5" /> },
                    ].map((item) => (
                      <div key={item.label} className="rounded-md border p-3">
                        <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                          {item.icon} {item.label}
                        </p>
                        <p className="mt-1 text-lg font-semibold text-numeric">{item.value}</p>
                      </div>
                    ))}
                  </div>
                  <Separator />
                  <div className="grid gap-3 sm:grid-cols-3">
                    {[
                      ["Imported", latestRun.qualification_imported_count],
                      ["Manual review", latestRun.qualification_manual_review_count],
                      ["Rejected", latestRun.qualification_rejected_count],
                    ].map(([label, value]) => (
                      <div key={String(label)} className="rounded-md border px-3 py-2">
                        <p className="text-xs text-muted-foreground">{label}</p>
                        <p className="text-numeric text-lg font-semibold">{value}</p>
                      </div>
                    ))}
                  </div>
                  {latestRun.status === "failed" && latestRun.errors.length > 0 ? (
                    <p className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                      Discovery failed: {latestRun.errors[0]}
                    </p>
                  ) : null}
                </>
              ) : (
                <div className="py-8 text-sm text-muted-foreground">No discovery runs found yet.</div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <SectionCardTitle title="Diagnostics & history" />
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="history">
              <TabsList className="flex-wrap">
                  <TabsTrigger value="history">History</TabsTrigger>
                  <TabsTrigger value="raw">Raw Apollo data</TabsTrigger>
                  <TabsTrigger value="normalized">Normalized</TabsTrigger>
                  <TabsTrigger value="qualification">Qualification</TabsTrigger>
              </TabsList>
              {stageDetail.isLoading ? (
                <p className="mt-3 text-sm text-muted-foreground">Loading diagnostics for the latest record...</p>
              ) : stageDetail.isError ? (
                <p className="mt-3 text-sm text-destructive">Diagnostic data unavailable: {stageDetail.error.message}</p>
              ) : null}

              <TabsContent value="history" className="space-y-2">
                  {runs.data?.length === 0 ? (
                    <div className="py-8 text-sm text-muted-foreground">No runs found.</div>
                  ) : (
                    runs.data?.map((run) => (
                      <div key={run.id} className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 rounded-md border px-3 py-2.5">
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium">{run.product_name}</p>
                          <p className="truncate text-xs text-muted-foreground">
                            {run.search_frequency} · {run.companies_found} companies · {run.contacts_found} contacts ·{" "}
                            {run.api_calls_used} API calls
                          </p>
                          {run.status === "failed" && run.errors.length > 0 ? (
                            <p className="truncate text-xs text-destructive">{run.errors[0]}</p>
                          ) : null}
                        </div>
                        <StatusBadge status={run.status} />
                      </div>
                    ))
                  )}
                </TabsContent>

                <TabsContent value="raw">
                  <pre className="max-h-72 overflow-auto rounded-md border bg-muted/40 p-3 text-[11px] leading-relaxed">
{JSON.stringify(rawRecord, null, 2)}
                  </pre>
                  <pre className="mt-3 max-h-72 overflow-auto rounded-md border bg-muted/40 p-3 text-[11px] leading-relaxed">
{JSON.stringify(peopleResponse, null, 2)}
                  </pre>
                </TabsContent>

                <TabsContent value="normalized">
                  <pre className="max-h-72 overflow-auto rounded-md border bg-muted/40 p-3 text-[11px] leading-relaxed">
{JSON.stringify(
  {
    normalized_company: normalizedCompany,
    normalized_contacts: normalizedContacts,
  },
  null,
  2,
)}
                  </pre>
                </TabsContent>

                <TabsContent value="qualification" className="space-y-2">
                  <div className="rounded-md border p-3">
                    <div className="flex items-center gap-2">
                      <StatusBadge status={latestStage?.qualification_status ?? "staged"} />
                      <span className="text-sm font-medium">Score {latestStage?.score ?? 0}</span>
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground">
                      {latestStage?.reason_category ?? "No qualification record available."}
                    </p>
                    <pre className="mt-3 max-h-72 overflow-auto rounded-md border bg-muted/40 p-3 text-[11px] leading-relaxed">
{JSON.stringify(qualificationInput, null, 2)}
                    </pre>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function CriteriaTags({ label, values }: { label: string; values: string[] | undefined }) {
  if (!values?.length) {
    return null;
  }

  return (
    <div className="space-y-1.5">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <div className="flex flex-wrap gap-1.5">
        {values.map((value) => (
          <Badge key={value} variant="secondary" className="font-normal">
            {value}
          </Badge>
        ))}
      </div>
    </div>
  );
}
