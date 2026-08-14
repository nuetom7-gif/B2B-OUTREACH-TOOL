import { m as useManualReview } from "./hooks-xnZ2zKrZ.js";
import { a as CardContent, i as Card, r as StateCard, t as PageHeader } from "./page-header-B6w8wS7t.js";
import { n as StatusBadge } from "./status-badge-Bg9EAcqh.js";
import { useState } from "react";
import { jsx, jsxs } from "react/jsx-runtime";
//#region src/routes/research-queue.tsx?tsr-split=component
function ResearchQueuePage() {
	const [offset, setOffset] = useState(0);
	const query = useManualReview(offset);
	const manualReview = query.data?.items ?? [];
	if (query.isError) return /* @__PURE__ */ jsx(StateCard, {
		title: "Research queue unavailable",
		description: query.error.message || "The discovery staging endpoint returned an error."
	});
	if (query.isLoading) return /* @__PURE__ */ jsx(StateCard, {
		title: "Loading research queue",
		description: "Fetching manual review records from FastAPI."
	});
	return /* @__PURE__ */ jsxs("div", {
		className: "space-y-5",
		children: [/* @__PURE__ */ jsx(PageHeader, {
			title: "Research Queue",
			description: `${query.data?.total ?? 0} records in manual review`
		}), manualReview.length === 0 ? /* @__PURE__ */ jsx(StateCard, {
			title: "Queue is empty",
			description: "No discovery records currently require manual review."
		}) : /* @__PURE__ */ jsxs("div", {
			className: "space-y-2",
			children: [manualReview.map((record) => /* @__PURE__ */ jsx(Card, { children: /* @__PURE__ */ jsxs(CardContent, {
				className: "grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 py-3",
				children: [/* @__PURE__ */ jsxs("div", {
					className: "min-w-0",
					children: [
						/* @__PURE__ */ jsx("p", {
							className: "truncate font-medium",
							children: record.company_name ?? record.person_name ?? "Unknown record"
						}),
						/* @__PURE__ */ jsxs("p", {
							className: "truncate text-xs text-muted-foreground",
							children: [
								record.reason_category,
								" · ",
								record.decision_stage,
								" · ",
								record.provider_name
							]
						}),
						/* @__PURE__ */ jsxs("p", {
							className: "truncate text-xs text-muted-foreground",
							children: [
								record.company_domain ?? "No domain",
								" · ",
								record.person_title ?? "No title"
							]
						})
					]
				}), /* @__PURE__ */ jsx(StatusBadge, { status: record.final_status })]
			}) }, record.id)), /* @__PURE__ */ jsxs("div", {
				className: "flex items-center justify-between pt-3 text-sm text-muted-foreground",
				children: [/* @__PURE__ */ jsxs("span", { children: [
					"Showing ",
					offset + 1,
					"-",
					Math.min(offset + manualReview.length, query.data?.total ?? 0),
					" of ",
					query.data?.total ?? 0
				] }), /* @__PURE__ */ jsxs("div", {
					className: "flex gap-2",
					children: [/* @__PURE__ */ jsx("button", {
						className: "rounded border px-3 py-1 disabled:opacity-50",
						disabled: offset === 0,
						onClick: () => setOffset(Math.max(0, offset - 50)),
						children: "Previous"
					}), /* @__PURE__ */ jsx("button", {
						className: "rounded border px-3 py-1 disabled:opacity-50",
						disabled: offset + manualReview.length >= (query.data?.total ?? 0),
						onClick: () => setOffset(offset + 50),
						children: "Next"
					})]
				})]
			})]
		})]
	});
}
//#endregion
export { ResearchQueuePage as component };
