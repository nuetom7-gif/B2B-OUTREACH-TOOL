import { t as useCampaigns } from "./hooks-xnZ2zKrZ.js";
import { h as Button } from "./router-B42mCDaV.js";
import { a as CardContent, i as Card, r as StateCard, t as PageHeader } from "./page-header-B6w8wS7t.js";
import { n as StatusBadge } from "./status-badge-Bg9EAcqh.js";
import { jsx, jsxs } from "react/jsx-runtime";
import { toast } from "sonner";
//#region src/routes/campaigns.tsx?tsr-split=component
function CampaignsPage() {
	const query = useCampaigns();
	const campaigns = query.data ?? [];
	if (query.isError) return /* @__PURE__ */ jsx(StateCard, {
		title: "Campaigns unavailable",
		description: query.error.message || "The /campaigns endpoint returned an error.",
		action: /* @__PURE__ */ jsx(Button, {
			onClick: () => toast.success("Please reconnect the backend and retry"),
			children: "Retry later"
		})
	});
	if (query.isLoading) return /* @__PURE__ */ jsx(StateCard, {
		title: "Loading campaigns",
		description: "Fetching live CRM campaigns from FastAPI."
	});
	return /* @__PURE__ */ jsxs("div", {
		className: "space-y-5",
		children: [/* @__PURE__ */ jsx(PageHeader, {
			title: "Campaigns",
			description: `${campaigns.length} campaigns across all divisions`,
			actions: /* @__PURE__ */ jsx(Button, {
				onClick: () => toast.success("Campaign creation is a backend flow"),
				children: "New campaign"
			})
		}), campaigns.length === 0 ? /* @__PURE__ */ jsx(StateCard, {
			title: "No campaigns found",
			description: "Create campaigns in the backend to see them here."
		}) : /* @__PURE__ */ jsx("div", {
			className: "grid gap-4 md:grid-cols-2 xl:grid-cols-3",
			children: campaigns.map((campaign) => /* @__PURE__ */ jsx(Card, { children: /* @__PURE__ */ jsxs(CardContent, {
				className: "space-y-3 py-4",
				children: [
					/* @__PURE__ */ jsxs("div", {
						className: "grid grid-cols-[minmax(0,1fr)_auto] items-start gap-2",
						children: [/* @__PURE__ */ jsxs("div", {
							className: "min-w-0",
							children: [/* @__PURE__ */ jsx("p", {
								className: "truncate font-medium",
								children: campaign.name
							}), /* @__PURE__ */ jsx("p", {
								className: "truncate text-xs text-muted-foreground",
								children: campaign.company_name ?? "No company linked"
							})]
						}), /* @__PURE__ */ jsx(StatusBadge, { status: "active" })]
					}),
					/* @__PURE__ */ jsx("p", {
						className: "line-clamp-3 text-sm text-muted-foreground",
						children: campaign.notes || "No notes yet."
					}),
					/* @__PURE__ */ jsxs("div", {
						className: "rounded-md border bg-muted/30 px-3 py-2 text-sm",
						children: [/* @__PURE__ */ jsx("p", {
							className: "text-xs text-muted-foreground",
							children: "Linked messages"
						}), /* @__PURE__ */ jsx("p", {
							className: "text-numeric text-lg font-semibold",
							children: campaign.message_count
						})]
					}),
					/* @__PURE__ */ jsxs("div", {
						className: "flex gap-2",
						children: [/* @__PURE__ */ jsx(Button, {
							size: "sm",
							variant: "outline",
							className: "flex-1",
							onClick: () => toast.success("Campaign paused in UI only"),
							children: "Pause"
						}), /* @__PURE__ */ jsx(Button, {
							size: "sm",
							className: "flex-1",
							onClick: () => toast.success("Campaign marked ready in UI only"),
							children: "Approve"
						})]
					})
				]
			}) }, campaign.id))
		})]
	});
}
//#endregion
export { CampaignsPage as component };
