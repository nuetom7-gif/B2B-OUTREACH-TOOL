import { h as useMessages } from "./hooks-C4Tv24mh.js";
import { a as CardContent, i as Card, r as StateCard, t as PageHeader } from "./page-header-X6ihaif1.js";
import { n as StatusBadge } from "./status-badge-kZBN8DdI.js";
import { i as TabsTrigger, n as TabsContent, r as TabsList, t as Tabs } from "./tabs-DmCmWd_0.js";
import { jsx, jsxs } from "react/jsx-runtime";
//#region src/routes/mailbox.tsx?tsr-split=component
function MailboxPage() {
	const query = useMessages();
	const messages = query.data ?? [];
	if (query.isError) return /* @__PURE__ */ jsx(StateCard, {
		title: "Mailbox unavailable",
		description: query.error.message || "The /messages endpoint returned an error."
	});
	if (query.isLoading) return /* @__PURE__ */ jsx(StateCard, {
		title: "Loading mailbox",
		description: "Fetching live message history from FastAPI."
	});
	const statuses = Array.from(new Set(messages.map((message) => message.status))).sort();
	return /* @__PURE__ */ jsxs("div", {
		className: "space-y-5",
		children: [/* @__PURE__ */ jsx(PageHeader, {
			title: "Mailbox",
			description: `${messages.length} message events`
		}), /* @__PURE__ */ jsxs(Tabs, {
			defaultValue: statuses[0] ?? "sent",
			children: [/* @__PURE__ */ jsx(TabsList, {
				className: "flex-wrap",
				children: statuses.map((status) => /* @__PURE__ */ jsx(TabsTrigger, {
					value: status,
					className: "capitalize",
					children: status
				}, status))
			}), statuses.map((status) => {
				const items = messages.filter((message) => message.status === status);
				return /* @__PURE__ */ jsx(TabsContent, {
					value: status,
					className: "space-y-2",
					children: items.length === 0 ? /* @__PURE__ */ jsx(Card, { children: /* @__PURE__ */ jsx(CardContent, {
						className: "py-10 text-center text-sm text-muted-foreground",
						children: "Nothing here yet."
					}) }) : items.map((message) => /* @__PURE__ */ jsx(Card, { children: /* @__PURE__ */ jsxs(CardContent, {
						className: "grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 py-3",
						children: [/* @__PURE__ */ jsxs("div", {
							className: "min-w-0",
							children: [
								/* @__PURE__ */ jsx("p", {
									className: "truncate font-medium",
									children: message.subject
								}),
								/* @__PURE__ */ jsxs("p", {
									className: "truncate text-xs text-muted-foreground",
									children: [
										message.contact_name,
										" · ",
										message.company_name,
										" · ",
										message.mailbox_name ?? "No mailbox"
									]
								}),
								/* @__PURE__ */ jsxs("p", {
									className: "truncate text-xs text-muted-foreground",
									children: [
										message.sent_at ? new Date(message.sent_at).toLocaleString() : "Not sent yet",
										" · step",
										" ",
										message.sequence_step,
										" · replies ",
										message.reply_count
									]
								})
							]
						}), /* @__PURE__ */ jsx(StatusBadge, { status: message.status })]
					}) }, message.id))
				}, status);
			})]
		})]
	});
}
//#endregion
export { MailboxPage as component };
