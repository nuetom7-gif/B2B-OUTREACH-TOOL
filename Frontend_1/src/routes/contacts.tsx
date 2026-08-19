import { useMemo, useState } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import type { ColumnDef } from "@tanstack/react-table";
import { Download, Linkedin, Mail, Phone, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { PageHeader, StateCard } from "@/components/shared/page-header";
import { DataTable } from "@/components/shared/data-table";
import { StatusBadge, ConfidenceBar } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useContacts } from "@/lib/api/hooks";
import { downloadCsv } from "@/lib/api/client";
import type { BackendContact } from "@/lib/api/types";

export const Route = createFileRoute("/contacts")({
  head: () => ({
    meta: [
      { title: "Contacts — Yash Technology Outreach Hub" },
      {
        name: "description",
        content:
          "Decision-maker directory with title, company, email, phone, verification status and primary contact flags.",
      },
      { property: "og:title", content: "Contacts — Yash Technology Outreach Hub" },
      { property: "og:description", content: "Discovered contacts with contactability and review metadata." },
    ],
  }),
  component: ContactsPage,
});

function ContactsPage() {
  const query = useContacts();
  const navigate = useNavigate();
  const [verification, setVerification] = useState("all");
  const [priority, setPriority] = useState("all");
  const [exporting, setExporting] = useState(false);

  const data = query.data ?? [];
  const statuses = useMemo(
    () => Array.from(new Set(data.map((row) => row.verification_status).filter(Boolean))),
    [data],
  );
  const priorities = useMemo(
    () => Array.from(new Set(data.map((row) => row.contact_priority ?? "").filter(Boolean))),
    [data],
  );

  const rows = useMemo(
    () =>
      data.filter(
        (row) =>
          (verification === "all" || row.verification_status === verification) &&
          (priority === "all" || (priority === "primary" ? row.recommended_primary_contact : row.contact_priority === priority)),
      ),
    [data, verification, priority],
  );

  async function exportContacts() {
    setExporting(true);
    try {
      await downloadCsv("/contacts/export/csv", "yash-technology-contacts.csv");
      toast.success("Contacts CSV downloaded");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not export contacts");
    } finally {
      setExporting(false);
    }
  }

  if (query.isError) {
    return (
      <StateCard
        title="Contacts unavailable"
        description={query.error.message || "The /contacts endpoint returned an error."}
        action={
          <Button asChild>
            <a href="/dashboard">Back to dashboard</a>
          </Button>
        }
      />
    );
  }

  const columns: ColumnDef<BackendContact, unknown>[] = [
    {
      id: "select",
      enableHiding: false,
      header: ({ table }) => (
        <span data-no-row-click>
          <Checkbox
            checked={table.getIsAllPageRowsSelected()}
            onCheckedChange={(v) => table.toggleAllPageRowsSelected(!!v)}
            aria-label="Select all"
          />
        </span>
      ),
      cell: ({ row }) => (
        <span data-no-row-click>
          <Checkbox
            checked={row.getIsSelected()}
            onCheckedChange={(v) => row.toggleSelected(!!v)}
            aria-label="Select row"
          />
        </span>
      ),
    },
    {
      accessorKey: "name",
      header: "Name",
      cell: ({ row }) => (
        <div className="min-w-0">
          <p className="truncate font-medium">{row.original.name}</p>
          <p className="truncate text-xs text-muted-foreground">{row.original.contact_selection_reason ?? row.original.verification_status}</p>
        </div>
      ),
    },
    {
      accessorKey: "title",
      header: "Title",
      cell: ({ row }) => <span className="whitespace-nowrap text-sm">{row.original.title}</span>,
    },
    {
      accessorKey: "company_name",
      header: "Company",
      cell: ({ row }) => <span className="block max-w-[200px] truncate text-sm">{row.original.company_name}</span>,
    },
    {
      accessorKey: "email",
      header: "Email",
      cell: ({ row }) =>
        row.original.email ? (
          <span className="flex items-center gap-1.5 text-sm">
            <Mail className="size-3.5 text-muted-foreground" />
            {row.original.email}
          </span>
        ) : (
          <span className="text-xs text-muted-foreground">missing</span>
        ),
    },
    {
      accessorKey: "phone",
      header: "Phone",
      cell: ({ row }) =>
        row.original.phone ? (
          <span className="flex items-center gap-1.5 whitespace-nowrap text-sm">
            <Phone className="size-3.5 text-muted-foreground" />
            {row.original.phone}
          </span>
        ) : (
          <span className="text-xs text-muted-foreground">missing</span>
        ),
    },
    {
      accessorKey: "linkedin_url",
      header: "LinkedIn",
      cell: ({ row }) =>
        row.original.linkedin_url ? (
          <a data-no-row-click href={row.original.linkedin_url} target="_blank" rel="noreferrer" className="text-primary">
            <Linkedin className="size-4" />
          </a>
        ) : (
          <span className="text-xs text-muted-foreground">—</span>
        ),
    },
    {
      accessorKey: "source",
      header: "Source",
      cell: ({ row }) => <span className="whitespace-nowrap text-sm">{row.original.source}</span>,
    },
    {
      accessorKey: "discovery_profiles",
      header: "Discovery profile",
      cell: ({ row }) => (
        <div className="flex max-w-[220px] flex-wrap gap-1">
          {row.original.discovery_profiles.length > 0 ? (
            row.original.discovery_profiles.map((profile) => (
              <Badge key={profile} variant="secondary" className="text-[10px]">
                {profile}
              </Badge>
            ))
          ) : (
            <span className="text-xs text-muted-foreground">not discovered</span>
          )}
        </div>
      ),
    },
    {
      accessorKey: "contact_priority",
      header: "Priority",
      cell: ({ row }) => (
        <Badge variant={row.original.contact_priority === "low" ? "secondary" : "outline"}>
          {row.original.contact_priority ?? "unknown"}
        </Badge>
      ),
    },
    {
      accessorKey: "verification_status",
      header: "Verification",
      cell: ({ row }) => <StatusBadge status={row.original.verification_status} />,
    },
    {
      accessorKey: "lead_score",
      header: "Score",
      cell: ({ row }) => <ConfidenceBar value={Math.min(100, Math.max(0, row.original.lead_score))} />,
    },
    {
      accessorKey: "recommended_primary_contact",
      header: "Primary",
      cell: ({ row }) => (
        <Badge variant={row.original.recommended_primary_contact ? "success" : "outline"}>
          {row.original.recommended_primary_contact ? "yes" : "no"}
        </Badge>
      ),
    },
    {
      accessorKey: "do_not_contact",
      header: "DNC",
      cell: ({ row }) => <StatusBadge status={row.original.do_not_contact ? "opted_out" : "new"} />,
    },
  ];

  return (
    <div className="space-y-5">
      <PageHeader
        title="Contacts"
        description={`${rows.length} of ${data.length} decision makers`}
        actions={
          <Button variant="outline" onClick={() => void exportContacts()} disabled={exporting}>
            <Download className="size-4" /> {exporting ? "Exporting..." : "Export"}
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={rows}
        loading={query.isLoading}
        searchPlaceholder="Search name, company, title or email…"
        onRowClick={(row) => navigate({ to: "/contacts/$contactId", params: { contactId: String(row.id) } })}
        bulkActions={(selected, clear) => (
          <Button
            size="sm"
            onClick={() => {
              toast.success(`AI drafts queued for ${selected.length} contacts`);
              clear();
            }}
          >
            <Sparkles className="size-3.5" /> Generate drafts
          </Button>
        )}
        toolbar={
          <div className="col-span-2 flex flex-wrap gap-2 sm:col-span-1">
            <Select value={verification} onValueChange={setVerification}>
              <SelectTrigger className="h-9 w-[180px] text-xs">
                <SelectValue placeholder="Verification" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All verification states</SelectItem>
                {statuses.map((item) => (
                  <SelectItem key={item} value={item}>
                    {item}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={priority} onValueChange={setPriority}>
              <SelectTrigger className="h-9 w-[180px] text-xs">
                <SelectValue placeholder="Priority" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All priorities</SelectItem>
                <SelectItem value="primary">Primary only</SelectItem>
                {priorities.map((item) => (
                  <SelectItem key={item} value={item}>
                    {item}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        }
      />
    </div>
  );
}
