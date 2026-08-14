import { p as useDrafts, y as apiPut } from "./hooks-xnZ2zKrZ.js";
import { h as Button, m as Input } from "./router-B42mCDaV.js";
import { a as CardContent, i as Card, r as StateCard, t as PageHeader } from "./page-header-B6w8wS7t.js";
import { n as StatusBadge } from "./status-badge-Bg9EAcqh.js";
import { t as Textarea } from "./textarea-GR4yGSmz.js";
import { useEffect, useMemo, useState } from "react";
import { jsx, jsxs } from "react/jsx-runtime";
import { toast } from "sonner";
//#region src/routes/drafts.tsx?tsr-split=component
function DraftsPage() {
	const query = useDrafts();
	const drafts = query.data ?? [];
	const [draftState, setDraftState] = useState({});
	useEffect(() => {
		setDraftState(Object.fromEntries(drafts.map((draft) => [draft.id, {
			subject: draft.subject,
			body: draft.body,
			sequence_step: draft.sequence_step
		}])));
	}, [drafts]);
	const sortedDrafts = useMemo(() => drafts, [drafts]);
	async function saveDraft(draft) {
		const current = draftState[draft.id] ?? {
			subject: draft.subject,
			body: draft.body,
			sequence_step: draft.sequence_step
		};
		try {
			await apiPut(`/drafts/${draft.id}`, {
				subject: current.subject,
				body: current.body,
				campaign_id: draft.campaign_id,
				sequence_step: current.sequence_step
			});
			toast.success("Draft saved");
			await query.refetch();
		} catch (error) {
			toast.error(error instanceof Error ? error.message : "Could not save draft");
		}
	}
	if (query.isError) return /* @__PURE__ */ jsx(StateCard, {
		title: "Drafts unavailable",
		description: query.error.message || "The /drafts endpoint returned an error.",
		action: /* @__PURE__ */ jsx(Button, {
			onClick: () => toast.success("Retry after reconnecting the backend"),
			children: "Retry later"
		})
	});
	if (query.isLoading) return /* @__PURE__ */ jsx(StateCard, {
		title: "Loading drafts",
		description: "Fetching live draft records from FastAPI."
	});
	return /* @__PURE__ */ jsxs("div", {
		className: "space-y-5",
		children: [/* @__PURE__ */ jsx(PageHeader, {
			title: "AI Drafts",
			description: `${sortedDrafts.length} drafts awaiting review`
		}), sortedDrafts.length === 0 ? /* @__PURE__ */ jsx(StateCard, {
			title: "No drafts found",
			description: "Generate drafts in the backend to review them here."
		}) : /* @__PURE__ */ jsx("div", {
			className: "grid gap-4 lg:grid-cols-2",
			children: sortedDrafts.map((draft) => {
				const current = draftState[draft.id] ?? {
					subject: draft.subject,
					body: draft.body,
					sequence_step: draft.sequence_step
				};
				return /* @__PURE__ */ jsx(Card, { children: /* @__PURE__ */ jsxs(CardContent, {
					className: "space-y-3 py-4",
					children: [
						/* @__PURE__ */ jsxs("div", {
							className: "grid grid-cols-[minmax(0,1fr)_auto] items-start gap-2",
							children: [/* @__PURE__ */ jsxs("div", {
								className: "min-w-0",
								children: [/* @__PURE__ */ jsx(Input, {
									value: current.subject,
									onChange: (e) => setDraftState((prev) => ({
										...prev,
										[draft.id]: {
											...current,
											subject: e.target.value
										}
									})),
									className: "h-9"
								}), /* @__PURE__ */ jsxs("p", {
									className: "truncate text-xs text-muted-foreground",
									children: [
										draft.contact_name,
										" · ",
										draft.company_name,
										" · step ",
										draft.sequence_step
									]
								})]
							}), /* @__PURE__ */ jsx(StatusBadge, { status: draft.status })]
						}),
						/* @__PURE__ */ jsx(Textarea, {
							value: current.body,
							onChange: (e) => setDraftState((prev) => ({
								...prev,
								[draft.id]: {
									...current,
									body: e.target.value
								}
							})),
							rows: 8,
							className: "text-sm"
						}),
						/* @__PURE__ */ jsxs("div", {
							className: "flex flex-wrap gap-2",
							children: [/* @__PURE__ */ jsx(Button, {
								size: "sm",
								variant: "outline",
								className: "flex-1",
								onClick: () => toast.success("Draft regenerated in UI only"),
								children: "Regenerate"
							}), /* @__PURE__ */ jsx(Button, {
								size: "sm",
								className: "flex-1",
								onClick: () => void saveDraft(draft),
								children: "Save"
							})]
						})
					]
				}) }, draft.id);
			})
		})]
	});
}
//#endregion
export { DraftsPage as component };
