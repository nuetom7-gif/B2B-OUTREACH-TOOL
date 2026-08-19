import { c as useDashboardSummary, s as useDashboardStats, x as cn } from "./hooks-DJqooqkf.js";
import { d as Badge, f as Skeleton, h as Button, p as Separator } from "./router-C_gzCGaY.js";
import { a as CardContent, i as Card, n as SectionCardTitle, o as CardHeader, r as StateCard, t as PageHeader } from "./page-header-BW-9RAbD.js";
import { Link } from "@tanstack/react-router";
import { Fragment, jsx, jsxs } from "react/jsx-runtime";
import { ArrowDownRight, ArrowUpRight, Bell, CheckCircle2, ClipboardList, Coins, Mail, MessageSquareReply, Radar, Send, ShieldAlert, Users } from "lucide-react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { motion } from "framer-motion";
//#region src/components/shared/stat-card.tsx
function StatCard({ label, value, delta, icon, hint, loading, index = 0 }) {
	return /* @__PURE__ */ jsx(motion.div, {
		initial: {
			opacity: 0,
			y: 8
		},
		animate: {
			opacity: 1,
			y: 0
		},
		transition: {
			duration: .25,
			delay: Math.min(index * .03, .24)
		},
		children: /* @__PURE__ */ jsxs(Card, {
			className: "gap-0 p-4 shadow-[var(--shadow-card)] transition-shadow hover:shadow-[var(--shadow-pop)]",
			children: [
				/* @__PURE__ */ jsxs("div", {
					className: "flex items-start justify-between gap-3",
					children: [/* @__PURE__ */ jsx("p", {
						className: "min-w-0 truncate text-[13px] font-medium text-muted-foreground",
						children: label
					}), icon ? /* @__PURE__ */ jsx("span", {
						className: "grid size-8 shrink-0 place-items-center rounded-md bg-primary/8 text-primary",
						children: icon
					}) : null]
				}),
				loading ? /* @__PURE__ */ jsx(Skeleton, { className: "mt-3 h-7 w-20" }) : /* @__PURE__ */ jsx("p", {
					className: "mt-2 text-2xl font-semibold text-numeric tracking-tight",
					children: value
				}),
				/* @__PURE__ */ jsxs("div", {
					className: "mt-1.5 flex items-center gap-1.5 text-xs",
					children: [typeof delta === "number" ? /* @__PURE__ */ jsxs("span", {
						className: cn("flex items-center gap-0.5 font-medium", delta >= 0 ? "text-success" : "text-destructive"),
						children: [
							delta >= 0 ? /* @__PURE__ */ jsx(ArrowUpRight, { className: "size-3.5" }) : /* @__PURE__ */ jsx(ArrowDownRight, { className: "size-3.5" }),
							Math.abs(delta),
							"%"
						]
					}) : null, hint ? /* @__PURE__ */ jsx("span", {
						className: "truncate text-muted-foreground",
						children: hint
					}) : null]
				})
			]
		})
	});
}
//#endregion
//#region src/routes/index.tsx?tsr-split=component
var CHART = [
	"var(--chart-1)",
	"var(--chart-2)",
	"var(--chart-3)",
	"var(--chart-4)",
	"var(--chart-5)"
];
var tooltipStyle = { contentStyle: {
	background: "var(--popover)",
	border: "1px solid var(--border)",
	borderRadius: "8px",
	fontSize: "12px",
	color: "var(--popover-foreground)"
} };
function DashboardPage() {
	const summary = useDashboardSummary();
	const stats = useDashboardStats();
	if (summary.isError || stats.isError) {
		const message = summary.error?.message ?? stats.error?.message ?? "The dashboard endpoint could not be reached.";
		return /* @__PURE__ */ jsx(StateCard, {
			title: "Dashboard unavailable",
			description: message,
			action: /* @__PURE__ */ jsx(Button, {
				asChild: true,
				children: /* @__PURE__ */ jsx(Link, {
					to: "/settings",
					children: "Check backend settings"
				})
			})
		});
	}
	if (summary.isLoading || stats.isLoading || !summary.data || !stats.data) return /* @__PURE__ */ jsxs("div", {
		className: "space-y-5",
		children: [/* @__PURE__ */ jsx(PageHeader, {
			title: "Dashboard",
			description: "Pipeline health across discovery, qualification and outreach."
		}), /* @__PURE__ */ jsx("div", {
			className: "grid grid-cols-2 gap-3 lg:grid-cols-5",
			children: Array.from({ length: 10 }).map((_, index) => /* @__PURE__ */ jsx(StatCard, {
				index,
				label: "Loading",
				value: "—",
				loading: true,
				icon: /* @__PURE__ */ jsx(Bell, { className: "size-4" })
			}, index))
		})]
	});
	const dashboard = summary.data;
	const metrics = stats.data;
	const funnelData = Object.entries(metrics.funnel).map(([label, value]) => ({
		label,
		value
	}));
	const dailySeries = metrics.daily_leads.map((point) => ({
		date: point.date,
		leads: point.count,
		emails: metrics.daily_emails.find((row) => row.date === point.date)?.count ?? 0,
		replies: metrics.daily_replies.find((row) => row.date === point.date)?.count ?? 0
	}));
	const topProducts = metrics.per_product_stats.slice(0, 6);
	return /* @__PURE__ */ jsxs("div", {
		className: "space-y-5",
		children: [
			/* @__PURE__ */ jsx(PageHeader, {
				title: "Dashboard",
				description: "Pipeline health across discovery, qualification and outreach.",
				actions: /* @__PURE__ */ jsxs(Fragment, { children: [/* @__PURE__ */ jsx(Button, {
					variant: "outline",
					asChild: true,
					children: /* @__PURE__ */ jsx(Link, {
						to: "/analytics",
						children: "Open analytics"
					})
				}), /* @__PURE__ */ jsx(Button, {
					asChild: true,
					children: /* @__PURE__ */ jsxs(Link, {
						to: "/discovery",
						children: [/* @__PURE__ */ jsx(Radar, { className: "size-4" }), " Run discovery"]
					})
				})] })
			}),
			/* @__PURE__ */ jsxs("div", {
				className: "grid grid-cols-2 gap-3 lg:grid-cols-5",
				children: [
					/* @__PURE__ */ jsx(StatCard, {
						index: 0,
						label: "Total contacts",
						value: metrics.total_contacts.toLocaleString(),
						icon: /* @__PURE__ */ jsx(Users, { className: "size-4" })
					}),
					/* @__PURE__ */ jsx(StatCard, {
						index: 1,
						label: "Messages sent this month",
						value: dashboard.messages_sent_this_month.toLocaleString(),
						icon: /* @__PURE__ */ jsx(Send, { className: "size-4" })
					}),
					/* @__PURE__ */ jsx(StatCard, {
						index: 2,
						label: "Reply rate",
						value: `${(dashboard.reply_rate * 100).toFixed(1)}%`,
						icon: /* @__PURE__ */ jsx(MessageSquareReply, { className: "size-4" })
					}),
					/* @__PURE__ */ jsx(StatCard, {
						index: 3,
						label: "Active mailboxes",
						value: dashboard.active_mailboxes,
						icon: /* @__PURE__ */ jsx(Mail, { className: "size-4" })
					}),
					/* @__PURE__ */ jsx(StatCard, {
						index: 4,
						label: "Emails sent today",
						value: metrics.today_emails_sent,
						icon: /* @__PURE__ */ jsx(Send, { className: "size-4" })
					}),
					/* @__PURE__ */ jsx(StatCard, {
						index: 5,
						label: "Replies today",
						value: metrics.today_replies,
						icon: /* @__PURE__ */ jsx(MessageSquareReply, { className: "size-4" })
					}),
					/* @__PURE__ */ jsx(StatCard, {
						index: 6,
						label: "Bounce rate",
						value: `${(metrics.bounce_rate * 100).toFixed(1)}%`,
						icon: /* @__PURE__ */ jsx(ShieldAlert, { className: "size-4" })
					}),
					/* @__PURE__ */ jsx(StatCard, {
						index: 7,
						label: "Apollo credits remaining",
						value: metrics.apollo_credits_remaining.toLocaleString(),
						icon: /* @__PURE__ */ jsx(Coins, { className: "size-4" })
					}),
					/* @__PURE__ */ jsx(StatCard, {
						index: 8,
						label: "Pending drafts",
						value: metrics.pending_drafts,
						icon: /* @__PURE__ */ jsx(ClipboardList, { className: "size-4" })
					}),
					/* @__PURE__ */ jsx(StatCard, {
						index: 9,
						label: "Manual reviews",
						value: metrics.pending_reviews,
						icon: /* @__PURE__ */ jsx(CheckCircle2, { className: "size-4" })
					})
				]
			}),
			/* @__PURE__ */ jsxs("div", {
				className: "grid gap-4 xl:grid-cols-3",
				children: [/* @__PURE__ */ jsxs(Card, {
					className: "xl:col-span-2",
					children: [/* @__PURE__ */ jsxs(CardHeader, {
						className: "flex-row items-center justify-between gap-3",
						children: [/* @__PURE__ */ jsx(SectionCardTitle, {
							title: "Lead activity trend",
							hint: "Daily leads, emails and replies"
						}), /* @__PURE__ */ jsx(Badge, {
							variant: "secondary",
							children: "14d"
						})]
					}), /* @__PURE__ */ jsx(CardContent, {
						className: "h-[260px] px-2",
						children: /* @__PURE__ */ jsx(ResponsiveContainer, {
							width: "100%",
							height: "100%",
							children: /* @__PURE__ */ jsxs(AreaChart, {
								data: dailySeries,
								children: [
									/* @__PURE__ */ jsxs("defs", { children: [/* @__PURE__ */ jsxs("linearGradient", {
										id: "gLeads",
										x1: "0",
										y1: "0",
										x2: "0",
										y2: "1",
										children: [/* @__PURE__ */ jsx("stop", {
											offset: "0%",
											stopColor: "var(--chart-1)",
											stopOpacity: .35
										}), /* @__PURE__ */ jsx("stop", {
											offset: "100%",
											stopColor: "var(--chart-1)",
											stopOpacity: 0
										})]
									}), /* @__PURE__ */ jsxs("linearGradient", {
										id: "gEmails",
										x1: "0",
										y1: "0",
										x2: "0",
										y2: "1",
										children: [/* @__PURE__ */ jsx("stop", {
											offset: "0%",
											stopColor: "var(--chart-2)",
											stopOpacity: .3
										}), /* @__PURE__ */ jsx("stop", {
											offset: "100%",
											stopColor: "var(--chart-2)",
											stopOpacity: 0
										})]
									})] }),
									/* @__PURE__ */ jsx(CartesianGrid, {
										strokeDasharray: "3 3",
										stroke: "var(--border)",
										vertical: false
									}),
									/* @__PURE__ */ jsx(XAxis, {
										dataKey: "date",
										tick: { fontSize: 11 },
										stroke: "var(--muted-foreground)"
									}),
									/* @__PURE__ */ jsx(YAxis, {
										tick: { fontSize: 11 },
										stroke: "var(--muted-foreground)",
										width: 32
									}),
									/* @__PURE__ */ jsx(Tooltip, { ...tooltipStyle }),
									/* @__PURE__ */ jsx(Area, {
										type: "monotone",
										dataKey: "emails",
										stroke: "var(--chart-2)",
										fill: "url(#gEmails)",
										strokeWidth: 2
									}),
									/* @__PURE__ */ jsx(Area, {
										type: "monotone",
										dataKey: "leads",
										stroke: "var(--chart-1)",
										fill: "url(#gLeads)",
										strokeWidth: 2
									}),
									/* @__PURE__ */ jsx(Line, {
										type: "monotone",
										dataKey: "replies",
										stroke: "var(--chart-3)",
										strokeWidth: 2,
										dot: false
									})
								]
							})
						})
					})]
				}), /* @__PURE__ */ jsxs(Card, { children: [/* @__PURE__ */ jsx(CardHeader, { children: /* @__PURE__ */ jsx(SectionCardTitle, {
					title: "Pipeline funnel",
					hint: "Current CRM staging"
				}) }), /* @__PURE__ */ jsx(CardContent, {
					className: "h-[260px] px-2",
					children: /* @__PURE__ */ jsx(ResponsiveContainer, {
						width: "100%",
						height: "100%",
						children: /* @__PURE__ */ jsxs(BarChart, {
							data: funnelData,
							layout: "vertical",
							margin: { left: 12 },
							children: [
								/* @__PURE__ */ jsx(CartesianGrid, {
									strokeDasharray: "3 3",
									stroke: "var(--border)",
									horizontal: false
								}),
								/* @__PURE__ */ jsx(XAxis, {
									type: "number",
									tick: { fontSize: 11 },
									stroke: "var(--muted-foreground)"
								}),
								/* @__PURE__ */ jsx(YAxis, {
									type: "category",
									dataKey: "label",
									width: 96,
									tick: { fontSize: 11 },
									stroke: "var(--muted-foreground)"
								}),
								/* @__PURE__ */ jsx(Tooltip, { ...tooltipStyle }),
								/* @__PURE__ */ jsx(Bar, {
									dataKey: "value",
									radius: [
										0,
										4,
										4,
										0
									],
									children: funnelData.map((_, index) => /* @__PURE__ */ jsx(Cell, { fill: CHART[index % CHART.length] }, index))
								})
							]
						})
					})
				})] })]
			}),
			/* @__PURE__ */ jsxs("div", {
				className: "grid gap-4 xl:grid-cols-3",
				children: [
					/* @__PURE__ */ jsxs(Card, { children: [/* @__PURE__ */ jsx(CardHeader, { children: /* @__PURE__ */ jsx(SectionCardTitle, {
						title: "Product targets",
						hint: "Progress against daily targets"
					}) }), /* @__PURE__ */ jsx(CardContent, {
						className: "h-[240px] px-2",
						children: /* @__PURE__ */ jsx(ResponsiveContainer, {
							width: "100%",
							height: "100%",
							children: /* @__PURE__ */ jsxs(BarChart, {
								data: topProducts,
								children: [
									/* @__PURE__ */ jsx(CartesianGrid, {
										strokeDasharray: "3 3",
										stroke: "var(--border)",
										vertical: false
									}),
									/* @__PURE__ */ jsx(XAxis, {
										dataKey: "product_segment",
										tick: { fontSize: 10 },
										interval: 0,
										angle: -18,
										textAnchor: "end",
										height: 56
									}),
									/* @__PURE__ */ jsx(YAxis, { tick: { fontSize: 11 } }),
									/* @__PURE__ */ jsx(Tooltip, { ...tooltipStyle }),
									/* @__PURE__ */ jsx(Bar, {
										dataKey: "current",
										fill: "var(--chart-4)",
										radius: [
											4,
											4,
											0,
											0
										]
									})
								]
							})
						})
					})] }),
					/* @__PURE__ */ jsxs(Card, { children: [/* @__PURE__ */ jsx(CardHeader, { children: /* @__PURE__ */ jsx(SectionCardTitle, {
						title: "Today by product",
						hint: "Leads discovered against target"
					}) }), /* @__PURE__ */ jsx(CardContent, {
						className: "space-y-2",
						children: Object.entries(metrics.today_leads).map(([segment, target]) => /* @__PURE__ */ jsxs("div", {
							className: "rounded-md border px-3 py-2",
							children: [/* @__PURE__ */ jsxs("div", {
								className: "flex items-center justify-between gap-3",
								children: [/* @__PURE__ */ jsx("p", {
									className: "truncate text-sm font-medium",
									children: segment
								}), /* @__PURE__ */ jsxs("p", {
									className: "text-xs text-muted-foreground",
									children: [
										target.current,
										"/",
										target.target
									]
								})]
							}), /* @__PURE__ */ jsx("div", {
								className: "mt-2 h-1.5 overflow-hidden rounded-full bg-muted",
								children: /* @__PURE__ */ jsx("div", {
									className: "h-full rounded-full bg-primary",
									style: { width: `${Math.min(100, target.target === 0 ? 0 : target.current / target.target * 100)}%` }
								})
							})]
						}, segment))
					})] }),
					/* @__PURE__ */ jsxs(Card, { children: [/* @__PURE__ */ jsx(CardHeader, { children: /* @__PURE__ */ jsx(SectionCardTitle, {
						title: "Recent activity",
						hint: "Latest backend activity"
					}) }), /* @__PURE__ */ jsx(CardContent, {
						className: "space-y-0 p-0",
						children: dashboard.recent_messages.map((message, index) => /* @__PURE__ */ jsxs("div", { children: [index > 0 ? /* @__PURE__ */ jsx(Separator, {}) : null, /* @__PURE__ */ jsxs("div", {
							className: "flex items-start gap-3 px-6 py-3",
							children: [
								/* @__PURE__ */ jsx("span", { className: "mt-1.5 size-2 shrink-0 rounded-full bg-primary" }),
								/* @__PURE__ */ jsxs("div", {
									className: "min-w-0 flex-1",
									children: [/* @__PURE__ */ jsx("p", {
										className: "truncate text-sm font-medium",
										children: message.subject
									}), /* @__PURE__ */ jsxs("p", {
										className: "truncate text-xs text-muted-foreground",
										children: [
											message.contact_name,
											" · ",
											message.company_name
										]
									})]
								}),
								/* @__PURE__ */ jsx("span", {
									className: "shrink-0 text-xs text-muted-foreground",
									children: message.status
								})
							]
						})] }, message.id))
					})] })
				]
			})
		]
	});
}
//#endregion
export { DashboardPage as component };
