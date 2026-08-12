import { useEffect, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { toast } from "sonner";

import { PageHeader, StateCard, SectionCardTitle } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { apiPut } from "@/lib/api/client";
import { useDailyTargets, useSettingsSnapshot } from "@/lib/api/hooks";
import type { BackendDailyTarget } from "@/lib/api/types";

const DAILY_TARGET_FIELDS = [
  "target_leads_per_day",
  "companies_per_run",
  "contacts_per_company",
  "max_emails_per_batch",
] as const satisfies ReadonlyArray<keyof BackendDailyTarget>;

export const Route = createFileRoute("/settings")({
  head: () => ({
    meta: [
      { title: "Settings — Yash Technology Outreach Hub" },
      { name: "description", content: "Workspace settings, SMTP settings and daily lead targets." },
      { property: "og:title", content: "Settings — Yash Technology Outreach Hub" },
      { property: "og:description", content: "Configure workspace settings and product-level daily targets." },
    ],
  }),
  component: SettingsPage,
});

function SettingsPage() {
  const settings = useSettingsSnapshot();
  const targets = useDailyTargets();
  const [settingsState, setSettingsState] = useState<Record<string, string>>({});
  const [targetsState, setTargetsState] = useState<Record<number, BackendDailyTarget>>({});

  useEffect(() => {
    if (settings.data) {
      setSettingsState(
        Object.fromEntries(Object.entries(settings.data).map(([key, value]) => [key, String(value ?? "")])),
      );
    }
  }, [settings.data]);

  useEffect(() => {
    if (targets.data) {
      setTargetsState(Object.fromEntries(targets.data.map((target) => [target.id, target])));
    }
  }, [targets.data]);

  if (settings.isError || targets.isError) {
    return (
      <StateCard
        title="Settings unavailable"
        description={settings.error?.message ?? targets.error?.message ?? "The settings endpoints returned an error."}
      />
    );
  }

  if (settings.isLoading || targets.isLoading || !settings.data || !targets.data) {
    return <StateCard title="Loading settings" description="Fetching workspace settings and daily targets." />;
  }

  async function saveSettings() {
    try {
      await apiPut("/settings", Object.entries(settingsState).map(([key, value]) => ({ key, value })));
      toast.success("Settings saved");
      await settings.refetch();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not save settings");
    }
  }

  async function saveTargets() {
    try {
      await apiPut(
        "/daily-targets",
        Object.values(targetsState).map((target) => ({
          product_segment: target.product_segment,
          target_leads_per_day: Number(target.target_leads_per_day),
          companies_per_run: Number(target.companies_per_run),
          contacts_per_company: Number(target.contacts_per_company),
          max_emails_per_batch: Number(target.max_emails_per_batch),
          active: target.active,
          default_campaign_id: target.default_campaign_id,
          default_mailbox_id: target.default_mailbox_id,
        })),
      );
      toast.success("Daily targets saved");
      await targets.refetch();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not save daily targets");
    }
  }

  return (
    <div className="space-y-5">
      <PageHeader title="Settings" description="Workspace settings, SMTP settings and daily lead targets" />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <SectionCardTitle title="Workspace settings" hint="Stored in the backend settings table" />
          </CardHeader>
          <CardContent className="space-y-4">
            {Object.entries(settingsState).map(([key, value]) => (
              <div key={key} className="space-y-1.5">
                <Label htmlFor={key}>{key}</Label>
                <Input
                  id={key}
                  value={value}
                  onChange={(e) => setSettingsState((prev) => ({ ...prev, [key]: e.target.value }))}
                />
              </div>
            ))}
            <Button onClick={() => void saveSettings()}>Save workspace settings</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <SectionCardTitle title="Daily lead targets" hint="Per-product targets and caps" />
          </CardHeader>
          <CardContent className="space-y-4">
            {Object.values(targetsState).map((target) => (
              <div key={target.id} className="rounded-md border p-3">
                <p className="text-sm font-medium">{target.product_segment}</p>
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  {DAILY_TARGET_FIELDS.map((field) => (
                    <div key={field} className="space-y-1">
                      <Label className="text-xs">{field}</Label>
                      <Input
                        type="number"
                        value={String(target[field] ?? "")}
                        onChange={(e) =>
                          setTargetsState((prev) => ({
                            ...prev,
                            [target.id]: {
                              ...target,
                              [field]: Number(e.target.value),
                            } as BackendDailyTarget,
                          }))
                        }
                      />
                    </div>
                  ))}
                </div>
                <Separator className="my-3" />
                <div className="flex items-center justify-between gap-3">
                  <p className="text-xs text-muted-foreground">Active</p>
                  <Button
                    variant={target.active ? "secondary" : "outline"}
                    size="sm"
                    onClick={() =>
                      setTargetsState((prev) => ({
                        ...prev,
                        [target.id]: { ...target, active: !target.active },
                      }))
                    }
                  >
                    {target.active ? "Enabled" : "Disabled"}
                  </Button>
                </div>
              </div>
            ))}
            <Button onClick={() => void saveTargets()}>Save daily targets</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
