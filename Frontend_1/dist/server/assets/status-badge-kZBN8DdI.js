import { b as cn } from "./hooks-C4Tv24mh.js";
import { jsx, jsxs } from "react/jsx-runtime";
//#region src/components/shared/status-badge.tsx
var TONES = {
	neutral: "bg-muted text-muted-foreground border-transparent",
	success: "bg-success/12 text-success border-success/20",
	warning: "bg-warning/15 text-warning-foreground border-warning/30 dark:text-warning",
	info: "bg-info/12 text-info border-info/20",
	primary: "bg-primary/10 text-primary border-primary/20",
	danger: "bg-destructive/10 text-destructive border-destructive/20"
};
var MAP = {
	qualified: "success",
	review: "warning",
	disqualified: "danger",
	new: "neutral",
	researching: "info",
	ready_for_outreach: "primary",
	in_campaign: "info",
	engaged: "success",
	customer: "success",
	opted_out: "danger",
	pending: "warning",
	pending_review: "warning",
	manual_review: "warning",
	needs_manual_review: "warning",
	synced: "success",
	unassigned: "neutral",
	verified: "info",
	contacted: "primary",
	replied: "success",
	meeting: "success",
	bounced: "danger",
	draft: "neutral",
	pending_approval: "warning",
	scheduled: "info",
	active: "success",
	paused: "warning",
	completed: "primary",
	approved: "success",
	rejected: "danger",
	sent: "primary",
	queued: "neutral",
	running: "info",
	failed: "danger",
	delivered: "primary",
	opened: "info",
	unsubscribed: "danger",
	open: "warning",
	in_progress: "info",
	resolved: "success"
};
function StatusBadge({ status, className }) {
	const tone = MAP[status] ?? "neutral";
	return /* @__PURE__ */ jsxs("span", {
		className: cn("inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] font-medium capitalize whitespace-nowrap", TONES[tone], className),
		children: [/* @__PURE__ */ jsx("span", { className: "size-1.5 rounded-full bg-current opacity-70" }), status.replace(/_/g, " ")]
	});
}
function ConfidenceBar({ value }) {
	return /* @__PURE__ */ jsxs("div", {
		className: "flex items-center gap-2",
		children: [/* @__PURE__ */ jsx("div", {
			className: "h-1.5 w-14 overflow-hidden rounded-full bg-muted",
			children: /* @__PURE__ */ jsx("div", {
				className: cn("h-full rounded-full", value >= 78 ? "bg-success" : value >= 58 ? "bg-warning" : "bg-destructive"),
				style: { width: `${value}%` }
			})
		}), /* @__PURE__ */ jsxs("span", {
			className: "text-xs text-numeric text-muted-foreground",
			children: [value, "%"]
		})]
	});
}
//#endregion
export { StatusBadge as n, ConfidenceBar as t };
