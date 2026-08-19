import { b as downloadCsv, n as useCompanies } from "./hooks-DJqooqkf.js";
import { d as Badge, h as Button, i as DropdownMenu, l as DropdownMenuSeparator, o as DropdownMenuContent, s as DropdownMenuItem, u as DropdownMenuTrigger } from "./router-C_gzCGaY.js";
import { r as StateCard, t as PageHeader } from "./page-header-BW-9RAbD.js";
import { n as DataTable, t as Checkbox } from "./checkbox-BoxsFlvU.js";
import { a as SelectValue, i as SelectTrigger, n as SelectContent, r as SelectItem, t as Select } from "./select-BQ8WvsND.js";
import { useMemo, useState } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import { Fragment, jsx, jsxs } from "react/jsx-runtime";
import { Download, MoreHorizontal, Plus, UserPlus } from "lucide-react";
import { toast } from "sonner";
//#region src/routes/companies.tsx?tsr-split=component
function CompaniesPage() {
	const query = useCompanies();
	const navigate = useNavigate();
	const [source, setSource] = useState("all");
	const [sync, setSync] = useState("all");
	const [review, setReview] = useState("all");
	const [exporting, setExporting] = useState(false);
	const data = query.data ?? [];
	const sources = useMemo(() => Array.from(new Set(data.map((row) => row.source).filter(Boolean))), [data]);
	const syncStatuses = useMemo(() => Array.from(new Set(data.map((row) => row.sync_status).filter(Boolean))), [data]);
	const rows = useMemo(() => data.filter((row) => (source === "all" || row.source === source) && (sync === "all" || row.sync_status === sync) && (review === "all" || (review === "yes" ? row.needs_manual_review : !row.needs_manual_review))), [
		data,
		source,
		sync,
		review
	]);
	async function exportCompanies() {
		setExporting(true);
		try {
			await downloadCsv("/companies/export/csv", "yash-technology-companies.csv");
			toast.success("Companies CSV downloaded");
		} catch (error) {
			toast.error(error instanceof Error ? error.message : "Could not export companies");
		} finally {
			setExporting(false);
		}
	}
	if (query.isError) return /* @__PURE__ */ jsx(StateCard, {
		title: "Companies unavailable",
		description: query.error.message || "The /companies endpoint returned an error.",
		action: /* @__PURE__ */ jsx(Button, {
			asChild: true,
			children: /* @__PURE__ */ jsx(Link, {
				to: "/",
				children: "Back to dashboard"
			})
		})
	});
	return /* @__PURE__ */ jsxs("div", {
		className: "space-y-5",
		children: [/* @__PURE__ */ jsx(PageHeader, {
			title: "Companies",
			description: `${rows.length} of ${data.length} discovered companies`,
			actions: /* @__PURE__ */ jsxs(Fragment, { children: [/* @__PURE__ */ jsxs(Button, {
				variant: "outline",
				onClick: () => void exportCompanies(),
				disabled: exporting,
				children: [
					/* @__PURE__ */ jsx(Download, { className: "size-4" }),
					" ",
					exporting ? "Exporting..." : "Export"
				]
			}), /* @__PURE__ */ jsx(Button, {
				asChild: true,
				children: /* @__PURE__ */ jsxs(Link, {
					to: "/discovery",
					children: [/* @__PURE__ */ jsx(Plus, { className: "size-4" }), " Discover more"]
				})
			})] })
		}), /* @__PURE__ */ jsx(DataTable, {
			columns: [
				{
					id: "select",
					enableHiding: false,
					header: ({ table }) => /* @__PURE__ */ jsx("span", {
						"data-no-row-click": true,
						children: /* @__PURE__ */ jsx(Checkbox, {
							checked: table.getIsAllPageRowsSelected(),
							onCheckedChange: (v) => table.toggleAllPageRowsSelected(!!v),
							"aria-label": "Select all"
						})
					}),
					cell: ({ row }) => /* @__PURE__ */ jsx("span", {
						"data-no-row-click": true,
						children: /* @__PURE__ */ jsx(Checkbox, {
							checked: row.getIsSelected(),
							onCheckedChange: (v) => row.toggleSelected(!!v),
							"aria-label": "Select row"
						})
					})
				},
				{
					accessorKey: "name",
					header: "Company",
					cell: ({ row }) => /* @__PURE__ */ jsxs("div", {
						className: "min-w-0",
						children: [/* @__PURE__ */ jsx("p", {
							className: "truncate font-medium",
							children: row.original.name
						}), /* @__PURE__ */ jsx("p", {
							className: "truncate text-xs text-muted-foreground",
							children: row.original.source_provider ?? row.original.source
						})]
					})
				},
				{
					accessorKey: "industry",
					header: "Industry",
					cell: ({ row }) => /* @__PURE__ */ jsx("span", {
						className: "whitespace-nowrap text-sm",
						children: row.original.industry
					})
				},
				{
					accessorKey: "source",
					header: "Source",
					cell: ({ row }) => /* @__PURE__ */ jsx("span", {
						className: "whitespace-nowrap text-sm",
						children: row.original.source
					})
				},
				{
					accessorKey: "product_fits",
					header: "Products",
					cell: ({ row }) => /* @__PURE__ */ jsx("div", {
						className: "flex max-w-[220px] flex-wrap gap-1",
						children: row.original.product_fits.length > 0 ? row.original.product_fits.slice(0, 3).map((fit) => /* @__PURE__ */ jsx(Badge, {
							variant: "secondary",
							className: "text-[10px]",
							children: fit
						}, fit)) : /* @__PURE__ */ jsx("span", {
							className: "text-xs text-muted-foreground",
							children: "none"
						})
					})
				},
				{
					accessorKey: "contact_count",
					header: "Contacts",
					cell: ({ row }) => /* @__PURE__ */ jsx("span", {
						className: "text-numeric text-sm",
						children: row.original.contact_count
					})
				},
				{
					accessorKey: "lead_score",
					header: "Lead score",
					cell: ({ row }) => /* @__PURE__ */ jsx("span", {
						className: "text-numeric text-sm",
						children: row.original.lead_score
					})
				},
				{
					accessorKey: "sync_status",
					header: "Sync",
					cell: ({ row }) => /* @__PURE__ */ jsx(Badge, {
						variant: "outline",
						children: row.original.sync_status
					})
				},
				{
					accessorKey: "needs_manual_review",
					header: "Review",
					cell: ({ row }) => /* @__PURE__ */ jsx(Badge, {
						variant: row.original.needs_manual_review ? "secondary" : "outline",
						children: row.original.needs_manual_review ? "manual review" : "ok"
					})
				},
				{
					id: "actions",
					enableHiding: false,
					header: "",
					cell: ({ row }) => /* @__PURE__ */ jsx("span", {
						"data-no-row-click": true,
						children: /* @__PURE__ */ jsxs(DropdownMenu, { children: [/* @__PURE__ */ jsx(DropdownMenuTrigger, {
							asChild: true,
							children: /* @__PURE__ */ jsx(Button, {
								variant: "ghost",
								size: "icon",
								className: "size-8",
								children: /* @__PURE__ */ jsx(MoreHorizontal, { className: "size-4" })
							})
						}), /* @__PURE__ */ jsxs(DropdownMenuContent, {
							align: "end",
							children: [
								/* @__PURE__ */ jsx(DropdownMenuItem, {
									onSelect: () => navigate({
										to: "/companies/$companyId",
										params: { companyId: String(row.original.id) }
									}),
									children: "Open record"
								}),
								/* @__PURE__ */ jsx(DropdownMenuItem, {
									onSelect: () => toast.success("Queued for research review"),
									children: "Send to review"
								}),
								/* @__PURE__ */ jsx(DropdownMenuSeparator, {}),
								/* @__PURE__ */ jsx(DropdownMenuItem, {
									onSelect: () => toast.success("Assigned to workspace owner"),
									children: "Assign owner"
								})
							]
						})] })
					})
				}
			],
			data: rows,
			loading: query.isLoading,
			searchPlaceholder: "Search company, source or industry…",
			onRowClick: (row) => navigate({
				to: "/companies/$companyId",
				params: { companyId: String(row.id) }
			}),
			bulkActions: (selected, clear) => /* @__PURE__ */ jsxs(Button, {
				size: "sm",
				onClick: () => {
					toast.success(`${selected.length} companies assigned for review`);
					clear();
				},
				children: [/* @__PURE__ */ jsx(UserPlus, { className: "size-3.5" }), " Assign review"]
			}),
			toolbar: /* @__PURE__ */ jsxs("div", {
				className: "col-span-2 flex flex-wrap gap-2 sm:col-span-1",
				children: [
					/* @__PURE__ */ jsxs(Select, {
						value: source,
						onValueChange: setSource,
						children: [/* @__PURE__ */ jsx(SelectTrigger, {
							className: "h-9 w-[170px] text-xs",
							children: /* @__PURE__ */ jsx(SelectValue, { placeholder: "Source" })
						}), /* @__PURE__ */ jsxs(SelectContent, { children: [/* @__PURE__ */ jsx(SelectItem, {
							value: "all",
							children: "All sources"
						}), sources.map((item) => /* @__PURE__ */ jsx(SelectItem, {
							value: item,
							children: item
						}, item))] })]
					}),
					/* @__PURE__ */ jsxs(Select, {
						value: sync,
						onValueChange: setSync,
						children: [/* @__PURE__ */ jsx(SelectTrigger, {
							className: "h-9 w-[170px] text-xs",
							children: /* @__PURE__ */ jsx(SelectValue, { placeholder: "Sync status" })
						}), /* @__PURE__ */ jsxs(SelectContent, { children: [/* @__PURE__ */ jsx(SelectItem, {
							value: "all",
							children: "All sync statuses"
						}), syncStatuses.map((item) => /* @__PURE__ */ jsx(SelectItem, {
							value: item,
							children: item
						}, item))] })]
					}),
					/* @__PURE__ */ jsxs(Select, {
						value: review,
						onValueChange: setReview,
						children: [/* @__PURE__ */ jsx(SelectTrigger, {
							className: "h-9 w-[170px] text-xs",
							children: /* @__PURE__ */ jsx(SelectValue, { placeholder: "Manual review" })
						}), /* @__PURE__ */ jsxs(SelectContent, { children: [
							/* @__PURE__ */ jsx(SelectItem, {
								value: "all",
								children: "All review states"
							}),
							/* @__PURE__ */ jsx(SelectItem, {
								value: "yes",
								children: "Needs review"
							}),
							/* @__PURE__ */ jsx(SelectItem, {
								value: "no",
								children: "No review needed"
							})
						] })]
					})
				]
			})
		})]
	});
}
//#endregion
export { CompaniesPage as component };
