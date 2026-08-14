import { r as useCompany } from "./hooks-xnZ2zKrZ.js";
import { d as Badge, h as Button, p as Separator, r as Route } from "./router-CZcbm7f-.js";
import { a as CardContent, i as Card, o as CardHeader, r as StateCard, t as PageHeader } from "./page-header-B6w8wS7t.js";
import { Link } from "@tanstack/react-router";
import { jsx, jsxs } from "react/jsx-runtime";
import { ArrowLeft } from "lucide-react";
//#region src/routes/companies.$companyId.tsx?tsr-split=component
function CompanyDetailPage() {
	const { companyId } = Route.useParams();
	const query = useCompany(companyId);
	if (query.isLoading) return /* @__PURE__ */ jsx(StateCard, {
		title: "Loading company",
		description: "Fetching the company record from FastAPI."
	});
	if (query.isError || !query.data) return /* @__PURE__ */ jsx(StateCard, {
		title: "Company detail not available",
		description: "The backend currently does not expose GET /companies/{id}, so this screen cannot resolve a company record yet.",
		action: /* @__PURE__ */ jsx(Button, {
			asChild: true,
			children: /* @__PURE__ */ jsx(Link, {
				to: "/companies",
				children: "Back to companies"
			})
		})
	});
	const company = query.data;
	return /* @__PURE__ */ jsxs("div", {
		className: "space-y-5",
		children: [
			/* @__PURE__ */ jsx(Button, {
				variant: "ghost",
				size: "sm",
				asChild: true,
				className: "-ml-2 w-fit",
				children: /* @__PURE__ */ jsxs(Link, {
					to: "/companies",
					children: [/* @__PURE__ */ jsx(ArrowLeft, { className: "size-4" }), " Companies"]
				})
			}),
			/* @__PURE__ */ jsx(PageHeader, {
				title: company.name,
				description: `${company.industry} · ${company.source}`,
				actions: /* @__PURE__ */ jsx(Badge, {
					variant: "secondary",
					children: company.sync_status
				})
			}),
			/* @__PURE__ */ jsxs("div", {
				className: "flex flex-wrap items-center gap-2",
				children: [
					/* @__PURE__ */ jsx(Badge, {
						variant: company.needs_manual_review ? "warning" : "outline",
						children: company.needs_manual_review ? "manual review" : "ready"
					}),
					/* @__PURE__ */ jsxs(Badge, {
						variant: "secondary",
						children: [company.lead_score, " lead score"]
					}),
					/* @__PURE__ */ jsxs(Badge, {
						variant: "outline",
						children: [company.contact_count, " contacts"]
					}),
					company.fallback_contact_used ? /* @__PURE__ */ jsx(Badge, {
						variant: "secondary",
						children: "fallback contact used"
					}) : null
				]
			}),
			/* @__PURE__ */ jsxs("div", {
				className: "grid gap-4 lg:grid-cols-3",
				children: [/* @__PURE__ */ jsxs(Card, {
					className: "lg:col-span-2",
					children: [/* @__PURE__ */ jsx(CardHeader, { children: /* @__PURE__ */ jsx("h2", {
						className: "text-sm font-semibold",
						children: "CRM metadata"
					}) }), /* @__PURE__ */ jsx(CardContent, {
						className: "grid gap-3 text-sm sm:grid-cols-2",
						children: [
							["Source provider", company.source_provider ?? "—"],
							["Source record", company.source_record_id ?? "—"],
							["Apollo org id", company.apollo_organization_id ?? "—"],
							["Owner id", company.owner_id?.toString() ?? "—"],
							["Assignment", company.assignment_status],
							["Assignment source", company.assignment_source ?? "—"],
							["Discovery contacts returned", String(company.discovery_contacts_returned)],
							["Contact status", company.contact_status]
						].map(([label, value]) => /* @__PURE__ */ jsxs("div", {
							className: "min-w-0",
							children: [/* @__PURE__ */ jsx("p", {
								className: "text-xs text-muted-foreground",
								children: label
							}), /* @__PURE__ */ jsx("p", {
								className: "truncate font-medium",
								children: value
							})]
						}, label))
					})]
				}), /* @__PURE__ */ jsxs(Card, { children: [/* @__PURE__ */ jsx(CardHeader, { children: /* @__PURE__ */ jsx("h2", {
					className: "text-sm font-semibold",
					children: "Notes"
				}) }), /* @__PURE__ */ jsxs(CardContent, {
					className: "space-y-3 text-sm",
					children: [
						/* @__PURE__ */ jsx("p", {
							className: "text-muted-foreground",
							children: company.notes || "No notes available."
						}),
						/* @__PURE__ */ jsx(Separator, {}),
						/* @__PURE__ */ jsxs("div", {
							className: "space-y-2",
							children: [/* @__PURE__ */ jsx("p", {
								className: "text-xs text-muted-foreground",
								children: "Product fits"
							}), /* @__PURE__ */ jsx("div", {
								className: "flex flex-wrap gap-2",
								children: company.product_fits.length > 0 ? company.product_fits.map((fit) => /* @__PURE__ */ jsx(Badge, {
									variant: "secondary",
									children: fit
								}, fit)) : /* @__PURE__ */ jsx("span", {
									className: "text-xs text-muted-foreground",
									children: "None recorded"
								})
							})]
						})
					]
				})] })]
			})
		]
	});
}
//#endregion
export { CompanyDetailPage as component };
