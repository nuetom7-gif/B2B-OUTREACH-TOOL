import { i as useContact } from "./hooks-xnZ2zKrZ.js";
import { d as Badge, h as Button, n as Route, p as Separator } from "./router-CZcbm7f-.js";
import { a as CardContent, i as Card, o as CardHeader, r as StateCard, t as PageHeader } from "./page-header-B6w8wS7t.js";
import { n as StatusBadge, t as ConfidenceBar } from "./status-badge-Bg9EAcqh.js";
import { t as Textarea } from "./textarea-GR4yGSmz.js";
import { Link } from "@tanstack/react-router";
import { jsx, jsxs } from "react/jsx-runtime";
import { ArrowLeft, Mail, Sparkles } from "lucide-react";
import { toast } from "sonner";
//#region src/routes/contacts.$contactId.tsx?tsr-split=component
function ContactDetailPage() {
	const { contactId } = Route.useParams();
	const query = useContact(contactId);
	if (query.isError) return /* @__PURE__ */ jsx(StateCard, {
		title: "Contact unavailable",
		description: query.error.message || "The contact detail endpoint could not be reached.",
		action: /* @__PURE__ */ jsx(Button, {
			asChild: true,
			children: /* @__PURE__ */ jsx(Link, {
				to: "/contacts",
				children: "Back to contacts"
			})
		})
	});
	const contact = query.data;
	if (query.isLoading || !contact) return /* @__PURE__ */ jsx(StateCard, {
		title: "Loading contact",
		description: "Fetching the full CRM record from FastAPI."
	});
	return /* @__PURE__ */ jsxs("div", {
		className: "space-y-5",
		children: [
			/* @__PURE__ */ jsx(Button, {
				variant: "ghost",
				size: "sm",
				asChild: true,
				className: "-ml-2 w-fit",
				children: /* @__PURE__ */ jsxs(Link, {
					to: "/contacts",
					children: [/* @__PURE__ */ jsx(ArrowLeft, { className: "size-4" }), " Contacts"]
				})
			}),
			/* @__PURE__ */ jsx(PageHeader, {
				title: contact.name,
				description: `${contact.title} · ${contact.company_name}`,
				actions: /* @__PURE__ */ jsxs(Button, {
					onClick: () => toast.success("AI draft generation queued"),
					children: [/* @__PURE__ */ jsx(Sparkles, { className: "size-4" }), " Generate AI draft"]
				})
			}),
			/* @__PURE__ */ jsxs("div", {
				className: "flex flex-wrap items-center gap-2",
				children: [
					/* @__PURE__ */ jsx(StatusBadge, { status: contact.verification_status }),
					/* @__PURE__ */ jsx(StatusBadge, { status: contact.do_not_contact ? "opted_out" : "verified" }),
					/* @__PURE__ */ jsx(ConfidenceBar, { value: Math.min(100, Math.max(0, contact.lead_score)) }),
					contact.recommended_primary_contact ? /* @__PURE__ */ jsx(Badge, {
						variant: "success",
						children: "primary contact"
					}) : null,
					contact.fallback_contact_used ? /* @__PURE__ */ jsx(Badge, {
						variant: "secondary",
						children: "fallback"
					}) : null
				]
			}),
			/* @__PURE__ */ jsxs("div", {
				className: "grid gap-4 lg:grid-cols-3",
				children: [/* @__PURE__ */ jsxs(Card, {
					className: "lg:col-span-2",
					children: [/* @__PURE__ */ jsx(CardHeader, { children: /* @__PURE__ */ jsx("h2", {
						className: "text-sm font-semibold",
						children: "Details"
					}) }), /* @__PURE__ */ jsx(CardContent, {
						className: "grid gap-3 text-sm sm:grid-cols-2",
						children: [
							["Email", contact.email ?? "missing"],
							["Phone", contact.phone ?? "missing"],
							["LinkedIn", contact.linkedin_url ?? "—"],
							["Source", contact.source],
							["Priority", contact.contact_priority ?? "unknown"],
							["Selection reason", contact.contact_selection_reason ?? "—"],
							["Latest message", contact.latest_message_subject ?? "—"],
							["Latest status", contact.latest_message_status ?? "—"]
						].map(([k, v]) => /* @__PURE__ */ jsxs("div", {
							className: "min-w-0",
							children: [/* @__PURE__ */ jsx("p", {
								className: "text-xs text-muted-foreground",
								children: k
							}), /* @__PURE__ */ jsx("p", {
								className: "truncate font-medium",
								children: v
							})]
						}, k))
					})]
				}), /* @__PURE__ */ jsxs(Card, { children: [/* @__PURE__ */ jsx(CardHeader, { children: /* @__PURE__ */ jsx("h2", {
					className: "text-sm font-semibold",
					children: "Notes"
				}) }), /* @__PURE__ */ jsxs(CardContent, {
					className: "space-y-3",
					children: [
						/* @__PURE__ */ jsx("p", {
							className: "text-sm text-muted-foreground",
							children: contact.recommended_primary_contact ? "This contact was selected as the primary decision maker for the company." : "This contact was imported as part of the discovery or CRM flow."
						}),
						/* @__PURE__ */ jsx(Textarea, {
							rows: 4,
							placeholder: "Add a note…"
						}),
						/* @__PURE__ */ jsxs(Button, {
							size: "sm",
							onClick: () => toast.success("Note added"),
							children: [/* @__PURE__ */ jsx(Mail, { className: "size-3.5" }), " Add note"]
						})
					]
				})] })]
			}),
			/* @__PURE__ */ jsxs("div", {
				className: "grid gap-4 lg:grid-cols-2",
				children: [/* @__PURE__ */ jsxs(Card, { children: [/* @__PURE__ */ jsx(CardHeader, { children: /* @__PURE__ */ jsx("h2", {
					className: "text-sm font-semibold",
					children: "Messages"
				}) }), /* @__PURE__ */ jsx(CardContent, {
					className: "space-y-2",
					children: contact.messages.length === 0 ? /* @__PURE__ */ jsx("div", {
						className: "py-10 text-center text-sm text-muted-foreground",
						children: "No messages recorded."
					}) : contact.messages.map((message) => /* @__PURE__ */ jsxs("div", {
						className: "rounded-md border p-3",
						children: [
							/* @__PURE__ */ jsxs("div", {
								className: "grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3",
								children: [/* @__PURE__ */ jsxs("div", {
									className: "min-w-0",
									children: [/* @__PURE__ */ jsx("p", {
										className: "truncate text-sm font-medium",
										children: message.subject
									}), /* @__PURE__ */ jsxs("p", {
										className: "truncate text-xs text-muted-foreground",
										children: [
											message.mailbox_name ?? "No mailbox",
											" · ",
											message.campaign_name ?? "No campaign"
										]
									})]
								}), /* @__PURE__ */ jsx(StatusBadge, { status: message.status })]
							}),
							/* @__PURE__ */ jsx(Separator, { className: "my-2" }),
							/* @__PURE__ */ jsxs("p", {
								className: "text-xs text-muted-foreground",
								children: [
									"Sent at ",
									message.sent_at ? new Date(message.sent_at).toLocaleString() : "not sent",
									" · Step",
									" ",
									message.sequence_step,
									" · Replies ",
									message.reply_count
								]
							})
						]
					}, message.id))
				})] }), /* @__PURE__ */ jsxs(Card, { children: [/* @__PURE__ */ jsx(CardHeader, { children: /* @__PURE__ */ jsx("h2", {
					className: "text-sm font-semibold",
					children: "Replies"
				}) }), /* @__PURE__ */ jsx(CardContent, {
					className: "space-y-2",
					children: contact.replies.length === 0 ? /* @__PURE__ */ jsx("div", {
						className: "py-10 text-center text-sm text-muted-foreground",
						children: "No replies recorded."
					}) : contact.replies.map((reply) => /* @__PURE__ */ jsxs("div", {
						className: "rounded-md border p-3",
						children: [/* @__PURE__ */ jsxs("div", {
							className: "flex items-center justify-between gap-3",
							children: [/* @__PURE__ */ jsx("p", {
								className: "text-sm font-medium",
								children: reply.outcome
							}), /* @__PURE__ */ jsx("span", {
								className: "text-xs text-muted-foreground",
								children: new Date(reply.received_at).toLocaleString()
							})]
						}), /* @__PURE__ */ jsx("p", {
							className: "mt-2 text-sm text-muted-foreground",
							children: reply.body
						})]
					}, reply.id))
				})] })]
			})
		]
	});
}
//#endregion
export { ContactDetailPage as component };
