import { useMemo, useState } from "react";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import type { ColumnDef } from "@tanstack/react-table";
import { Download, MoreHorizontal, Plus, UserPlus } from "lucide-react";
import { toast } from "sonner";

import { PageHeader, StateCard } from "@/components/shared/page-header";
import { DataTable } from "@/components/shared/data-table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useCompanies } from "@/lib/api/hooks";
import type { BackendCompany } from "@/lib/api/types";

export const Route = createFileRoute("/companies")({
  head: () => ({
    meta: [
      { title: "Companies — Yash Technology Outreach Hub" },
      {
        name: "description",
        content: "CRM view of discovered companies with source, product fits, sync status and review flags.",
      },
      { property: "og:title", content: "Companies — Yash Technology Outreach Hub" },
      {
        property: "og:description",
        content: "Filter, review and assign discovered companies across the CRM.",
      },
    ],
  }),
  component: CompaniesPage,
});

function CompaniesPage() {
  const query = useCompanies();
  const navigate = useNavigate();
  const [source, setSource] = useState("all");
  const [sync, setSync] = useState("all");
  const [review, setReview] = useState("all");

  const data = query.data ?? [];

  const sources = useMemo(() => Array.from(new Set(data.map((row) => row.source).filter(Boolean))), [data]);
  const syncStatuses = useMemo(
    () => Array.from(new Set(data.map((row) => row.sync_status).filter(Boolean))),
    [data],
  );

  const rows = useMemo(
    () =>
      data.filter(
        (row) =>
          (source === "all" || row.source === source) &&
          (sync === "all" || row.sync_status === sync) &&
          (review === "all" || (review === "yes" ? row.needs_manual_review : !row.needs_manual_review)),
      ),
    [data, source, sync, review],
  );

  if (query.isError) {
    return (
      <StateCard
        title="Companies unavailable"
        description={query.error.message || "The /companies endpoint returned an error."}
        action={
          <Button asChild>
            <Link to="/">Back to dashboard</Link>
          </Button>
        }
      />
    );
  }

  const columns: ColumnDef<BackendCompany, unknown>[] = [
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
      header: "Company",
      cell: ({ row }) => (
        <div className="min-w-0">
          <p className="truncate font-medium">{row.original.name}</p>
          <p className="truncate text-xs text-muted-foreground">
            {row.original.source_provider ?? row.original.source}
          </p>
        </div>
      ),
    },
    {
      accessorKey: "industry",
      header: "Industry",
      cell: ({ row }) => <span className="whitespace-nowrap text-sm">{row.original.industry}</span>,
    },
    {
      accessorKey: "source",
      header: "Source",
      cell: ({ row }) => <span className="whitespace-nowrap text-sm">{row.original.source}</span>,
    },
    {
      accessorKey: "product_fits",
      header: "Products",
      cell: ({ row }) => (
        <div className="flex max-w-[220px] flex-wrap gap-1">
          {row.original.product_fits.length > 0 ? (
            row.original.product_fits.slice(0, 3).map((fit) => (
              <Badge key={fit} variant="secondary" className="text-[10px]">
                {fit}
              </Badge>
            ))
          ) : (
            <span className="text-xs text-muted-foreground">none</span>
          )}
        </div>
      ),
    },
    {
      accessorKey: "contact_count",
      header: "Contacts",
      cell: ({ row }) => <span className="text-numeric text-sm">{row.original.contact_count}</span>,
    },
    {
      accessorKey: "lead_score",
      header: "Lead score",
      cell: ({ row }) => <span className="text-numeric text-sm">{row.original.lead_score}</span>,
    },
    {
      accessorKey: "sync_status",
      header: "Sync",
      cell: ({ row }) => <Badge variant="outline">{row.original.sync_status}</Badge>,
    },
    {
      accessorKey: "needs_manual_review",
      header: "Review",
      cell: ({ row }) => (
        <Badge variant={row.original.needs_manual_review ? "secondary" : "outline"}>
          {row.original.needs_manual_review ? "manual review" : "ok"}
        </Badge>
      ),
    },
    {
      id: "actions",
      enableHiding: false,
      header: "",
      cell: ({ row }) => (
        <span data-no-row-click>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="size-8">
                <MoreHorizontal className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onSelect={() => navigate({ to: "/companies/$companyId", params: { companyId: String(row.original.id) } })}
              >
                Open record
              </DropdownMenuItem>
              <DropdownMenuItem onSelect={() => toast.success("Queued for research review")}>
                Send to review
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onSelect={() => toast.success("Assigned to workspace owner")}>
                Assign owner
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-5">
      <PageHeader
        title="Companies"
        description={`${rows.length} of ${data.length} discovered companies`}
        actions={
          <>
            <Button variant="outline" onClick={() => toast.success("Export queued")}>
              <Download className="size-4" /> Export
            </Button>
            <Button asChild>
              <Link to="/discovery">
                <Plus className="size-4" /> Discover more
              </Link>
            </Button>
          </>
        }
      />

      <DataTable
        columns={columns}
        data={rows}
        loading={query.isLoading}
        searchPlaceholder="Search company, source or industry…"
        onRowClick={(row) => navigate({ to: "/companies/$companyId", params: { companyId: String(row.id) } })}
        bulkActions={(selected, clear) => (
          <Button
            size="sm"
            onClick={() => {
              toast.success(`${selected.length} companies assigned for review`);
              clear();
            }}
          >
            <UserPlus className="size-3.5" /> Assign review
          </Button>
        )}
        toolbar={
          <div className="col-span-2 flex flex-wrap gap-2 sm:col-span-1">
            <Select value={source} onValueChange={setSource}>
              <SelectTrigger className="h-9 w-[170px] text-xs">
                <SelectValue placeholder="Source" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All sources</SelectItem>
                {sources.map((item) => (
                  <SelectItem key={item} value={item}>
                    {item}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={sync} onValueChange={setSync}>
              <SelectTrigger className="h-9 w-[170px] text-xs">
                <SelectValue placeholder="Sync status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All sync statuses</SelectItem>
                {syncStatuses.map((item) => (
                  <SelectItem key={item} value={item}>
                    {item}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={review} onValueChange={setReview}>
              <SelectTrigger className="h-9 w-[170px] text-xs">
                <SelectValue placeholder="Manual review" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All review states</SelectItem>
                <SelectItem value="yes">Needs review</SelectItem>
                <SelectItem value="no">No review needed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        }
      />
    </div>
  );
}
