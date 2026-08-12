import { a as useContacts } from "./hooks-C4Tv24mh.js";
import { d as Badge, h as Button } from "./router-Df8hO_k6.js";
import { r as StateCard, t as PageHeader } from "./page-header-X6ihaif1.js";
import { n as StatusBadge, t as ConfidenceBar } from "./status-badge-kZBN8DdI.js";
import { n as DataTable, t as Checkbox } from "./checkbox-C0d19Cj5.js";
import { a as SelectValue, i as SelectTrigger, n as SelectContent, r as SelectItem, t as Select } from "./select-BhB0Q1VR.js";
import { useMemo, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { jsx, jsxs } from "react/jsx-runtime";
import { Download, Linkedin, Mail, Phone, Sparkles } from "lucide-react";
import { toast } from "sonner";
//#region src/routes/contacts.tsx?tsr-split=component
function ContactsPage() {
	const query = useContacts();
	const navigate = useNavigate();
	const [verification, setVerification] = useState("all");
	const [priority, setPriority] = useState("all");
	const data = query.data ?? [];
	const statuses = useMemo(() => Array.from(new Set(data.map((row) => row.verification_status).filter(Boolean))), [data]);
	const priorities = useMemo(() => Array.from(new Set(data.map((row) => row.contact_priority ?? "").filter(Boolean))), [data]);
	const rows = useMemo(() => data.filter((row) => (verification === "all" || row.verification_status === verification) && (priority === "all" || (priority === "primary" ? row.recommended_primary_contact : row.contact_priority === priority))), [
		data,
		verification,
		priority
	]);
	if (query.isError) return /* @__PURE__ */ jsx(StateCard, {
		title: "Contacts unavailable",
		description: query.error.message || "The /contacts endpoint returned an error.",
		action: /* @__PURE__ */ jsx(Button, {
			asChild: true,
			children: /* @__PURE__ */ jsx("a", {
				href: "/dashboard",
				children: "Back to dashboard"
			})
		})
	});
	return /* @__PURE__ */ jsxs("div", {
		className: "space-y-5",
		children: [/* @__PURE__ */ jsx(PageHeader, {
			title: "Contacts",
			description: `${rows.length} of ${data.length} decision makers`,
			actions: /* @__PURE__ */ jsxs(Button, {
				variant: "outline",
				onClick: () => toast.success("Export queued"),
				children: [/* @__PURE__ */ jsx(Download, { className: "size-4" }), " Export"]
			})
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
					header: "Name",
					cell: ({ row }) => /* @__PURE__ */ jsxs("div", {
						className: "min-w-0",
						children: [/* @__PURE__ */ jsx("p", {
							className: "truncate font-medium",
							children: row.original.name
						}), /* @__PURE__ */ jsx("p", {
							className: "truncate text-xs text-muted-foreground",
							children: row.original.contact_selection_reason ?? row.original.verification_status
						})]
					})
				},
				{
					accessorKey: "title",
					header: "Title",
					cell: ({ row }) => /* @__PURE__ */ jsx("span", {
						className: "whitespace-nowrap text-sm",
						children: row.original.title
					})
				},
				{
					accessorKey: "company_name",
					header: "Company",
					cell: ({ row }) => /* @__PURE__ */ jsx("span", {
						className: "block max-w-[200px] truncate text-sm",
						children: row.original.company_name
					})
				},
				{
					accessorKey: "email",
					header: "Email",
					cell: ({ row }) => row.original.email ? /* @__PURE__ */ jsxs("span", {
						className: "flex items-center gap-1.5 text-sm",
						children: [/* @__PURE__ */ jsx(Mail, { className: "size-3.5 text-muted-foreground" }), row.original.email]
					}) : /* @__PURE__ */ jsx("span", {
						className: "text-xs text-muted-foreground",
						children: "missing"
					})
				},
				{
					accessorKey: "phone",
					header: "Phone",
					cell: ({ row }) => row.original.phone ? /* @__PURE__ */ jsxs("span", {
						className: "flex items-center gap-1.5 whitespace-nowrap text-sm",
						children: [/* @__PURE__ */ jsx(Phone, { className: "size-3.5 text-muted-foreground" }), row.original.phone]
					}) : /* @__PURE__ */ jsx("span", {
						className: "text-xs text-muted-foreground",
						children: "missing"
					})
				},
				{
					accessorKey: "linkedin_url",
					header: "LinkedIn",
					cell: ({ row }) => row.original.linkedin_url ? /* @__PURE__ */ jsx("a", {
						"data-no-row-click": true,
						href: row.original.linkedin_url,
						target: "_blank",
						rel: "noreferrer",
						className: "text-primary",
						children: /* @__PURE__ */ jsx(Linkedin, { className: "size-4" })
					}) : /* @__PURE__ */ jsx("span", {
						className: "text-xs text-muted-foreground",
						children: "—"
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
					accessorKey: "contact_priority",
					header: "Priority",
					cell: ({ row }) => /* @__PURE__ */ jsx(Badge, {
						variant: row.original.contact_priority === "low" ? "secondary" : "outline",
						children: row.original.contact_priority ?? "unknown"
					})
				},
				{
					accessorKey: "verification_status",
					header: "Verification",
					cell: ({ row }) => /* @__PURE__ */ jsx(StatusBadge, { status: row.original.verification_status })
				},
				{
					accessorKey: "lead_score",
					header: "Score",
					cell: ({ row }) => /* @__PURE__ */ jsx(ConfidenceBar, { value: Math.min(100, Math.max(0, row.original.lead_score)) })
				},
				{
					accessorKey: "recommended_primary_contact",
					header: "Primary",
					cell: ({ row }) => /* @__PURE__ */ jsx(Badge, {
						variant: row.original.recommended_primary_contact ? "success" : "outline",
						children: row.original.recommended_primary_contact ? "yes" : "no"
					})
				},
				{
					accessorKey: "do_not_contact",
					header: "DNC",
					cell: ({ row }) => /* @__PURE__ */ jsx(StatusBadge, { status: row.original.do_not_contact ? "opted_out" : "new" })
				}
			],
			data: rows,
			loading: query.isLoading,
			searchPlaceholder: "Search name, company, title or email…",
			onRowClick: (row) => navigate({
				to: "/contacts/$contactId",
				params: { contactId: String(row.id) }
			}),
			bulkActions: (selected, clear) => /* @__PURE__ */ jsxs(Button, {
				size: "sm",
				onClick: () => {
					toast.success(`AI drafts queued for ${selected.length} contacts`);
					clear();
				},
				children: [/* @__PURE__ */ jsx(Sparkles, { className: "size-3.5" }), " Generate drafts"]
			}),
			toolbar: /* @__PURE__ */ jsxs("div", {
				className: "col-span-2 flex flex-wrap gap-2 sm:col-span-1",
				children: [/* @__PURE__ */ jsxs(Select, {
					value: verification,
					onValueChange: setVerification,
					children: [/* @__PURE__ */ jsx(SelectTrigger, {
						className: "h-9 w-[180px] text-xs",
						children: /* @__PURE__ */ jsx(SelectValue, { placeholder: "Verification" })
					}), /* @__PURE__ */ jsxs(SelectContent, { children: [/* @__PURE__ */ jsx(SelectItem, {
						value: "all",
						children: "All verification states"
					}), statuses.map((item) => /* @__PURE__ */ jsx(SelectItem, {
						value: item,
						children: item
					}, item))] })]
				}), /* @__PURE__ */ jsxs(Select, {
					value: priority,
					onValueChange: setPriority,
					children: [/* @__PURE__ */ jsx(SelectTrigger, {
						className: "h-9 w-[180px] text-xs",
						children: /* @__PURE__ */ jsx(SelectValue, { placeholder: "Priority" })
					}), /* @__PURE__ */ jsxs(SelectContent, { children: [
						/* @__PURE__ */ jsx(SelectItem, {
							value: "all",
							children: "All priorities"
						}),
						/* @__PURE__ */ jsx(SelectItem, {
							value: "primary",
							children: "Primary only"
						}),
						priorities.map((item) => /* @__PURE__ */ jsx(SelectItem, {
							value: item,
							children: item
						}, item))
					] })]
				})]
			})
		})]
	});
}
//#endregion
export { ContactsPage as component };
