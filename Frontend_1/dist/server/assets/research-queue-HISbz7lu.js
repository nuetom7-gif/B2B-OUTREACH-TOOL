import { m as useManualReview, v as apiPost } from "./hooks-DJqooqkf.js";
import { h as Button } from "./router-C_gzCGaY.js";
import { a as CardContent, i as Card, r as StateCard, t as PageHeader } from "./page-header-BW-9RAbD.js";
import { n as StatusBadge } from "./status-badge-DEpkNyc-.js";
import { useState } from "react";
import { jsx, jsxs } from "react/jsx-runtime";
import { toast } from "sonner";
//#region src/routes/research-queue.tsx?tsr-split=component
function ResearchQueuePage() {
	const [offset, setOffset] = useState(0);
	const [decidingId, setDecidingId] = useState(null);
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
	async function decide(recordId, decision) {
		setDecidingId(recordId);
		try {
			const result = await apiPost(`/discovery/staging/${recordId}/review`, { decision });
			toast.success(decision === "approve" ? `Approved. ${result.contacts_imported} contact(s) imported.` : "Record rejected and removed from the review queue.");
			await query.refetch();
		} catch (error) {
			toast.error(error instanceof Error ? error.message : "Could not save the review decision");
		} finally {
			setDecidingId(null);
		}
	}
	return /* @__PURE__ */ jsxs("div", {
		className: "space-y-5",
		children: [/* @__PURE__ */ jsx(PageHeader, {
			title: "Research Queue",
			description: `${query.data?.total ?? 0} records need a decision. Approve keeps/imports the company and staged contacts; Reject closes this discovery record without marking anyone do-not-contact.`
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
								"Reason: ",
								record.reason_category.replaceAll("_", " "),
								" | Score: ",
								record.score
							]
						}),
						/* @__PURE__ */ jsxs("p", {
							className: "truncate text-xs text-muted-foreground",
							children: [
								record.company_domain ?? "No domain",
								" | ",
								record.person_title ?? "No title"
							]
						})
					]
				}), /* @__PURE__ */ jsxs("div", {
					className: "flex items-center gap-2",
					children: [
						/* @__PURE__ */ jsx(StatusBadge, { status: record.final_status }),
						/* @__PURE__ */ jsx(Button, {
							size: "sm",
							disabled: decidingId !== null,
							onClick: () => void decide(record.id, "approve"),
							children: decidingId === record.id ? "Saving..." : "Approve"
						}),
						/* @__PURE__ */ jsx(Button, {
							size: "sm",
							variant: "outline",
							disabled: decidingId !== null,
							onClick: () => void decide(record.id, "reject"),
							children: "Reject"
						})
					]
				})]
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
					children: [/* @__PURE__ */ jsx(Button, {
						variant: "outline",
						size: "sm",
						disabled: offset === 0,
						onClick: () => setOffset(Math.max(0, offset - 50)),
						children: "Previous"
					}), /* @__PURE__ */ jsx(Button, {
						variant: "outline",
						size: "sm",
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
