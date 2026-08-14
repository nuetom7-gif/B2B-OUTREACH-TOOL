import { s as useDashboardStats } from "./hooks-xnZ2zKrZ.js";
import { d as Badge } from "./router-CZcbm7f-.js";
import { a as CardContent, i as Card, n as SectionCardTitle, o as CardHeader, r as StateCard, t as PageHeader } from "./page-header-B6w8wS7t.js";
import { jsx, jsxs } from "react/jsx-runtime";
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
//#region src/routes/analytics.tsx?tsr-split=component
var COLORS = [
	"var(--chart-1)",
	"var(--chart-2)",
	"var(--chart-3)",
	"var(--chart-4)",
	"var(--chart-5)"
];
function AnalyticsPage() {
	const query = useDashboardStats();
	const stats = query.data;
	if (query.isError) return /* @__PURE__ */ jsx(StateCard, {
		title: "Analytics unavailable",
		description: query.error.message || "The /dashboard/stats endpoint returned an error."
	});
	if (query.isLoading || !stats) return /* @__PURE__ */ jsx(StateCard, {
		title: "Loading analytics",
		description: "Fetching dashboard stats from FastAPI."
	});
	const products = stats.per_product_stats.map((item) => ({
		label: item.product_segment,
		current: item.current,
		target: item.target,
		progress: item.progress
	}));
	const dailyActivity = stats.daily_leads.map((point) => ({
		date: point.date,
		leads: point.count,
		emails: stats.daily_emails.find((row) => row.date === point.date)?.count ?? 0,
		replies: stats.daily_replies.find((row) => row.date === point.date)?.count ?? 0
	}));
	const funnel = Object.entries(stats.funnel).map(([label, value]) => ({
		label,
		value
	}));
	return /* @__PURE__ */ jsxs("div", {
		className: "space-y-5",
		children: [/* @__PURE__ */ jsx(PageHeader, {
			title: "Analytics",
			description: "Discovery and outreach performance breakdowns"
		}), /* @__PURE__ */ jsxs("div", {
			className: "grid gap-4 lg:grid-cols-2",
			children: [
				/* @__PURE__ */ jsxs(Card, { children: [/* @__PURE__ */ jsx(CardHeader, { children: /* @__PURE__ */ jsx(SectionCardTitle, {
					title: "Product progress",
					hint: "Current versus target leads by product"
				}) }), /* @__PURE__ */ jsx(CardContent, {
					className: "h-72",
					children: /* @__PURE__ */ jsx(ResponsiveContainer, {
						width: "100%",
						height: "100%",
						children: /* @__PURE__ */ jsxs(BarChart, {
							data: products,
							children: [
								/* @__PURE__ */ jsx(CartesianGrid, {
									strokeDasharray: "3 3",
									stroke: "var(--border)",
									vertical: false
								}),
								/* @__PURE__ */ jsx(XAxis, {
									dataKey: "label",
									tick: { fontSize: 11 },
									interval: 0,
									angle: -20,
									textAnchor: "end",
									height: 60
								}),
								/* @__PURE__ */ jsx(YAxis, { tick: { fontSize: 11 } }),
								/* @__PURE__ */ jsx(Tooltip, {}),
								/* @__PURE__ */ jsx(Bar, {
									dataKey: "current",
									fill: "var(--chart-1)",
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
					title: "Daily activity",
					hint: "Leads, emails and replies over time"
				}) }), /* @__PURE__ */ jsx(CardContent, {
					className: "h-72",
					children: /* @__PURE__ */ jsx(ResponsiveContainer, {
						width: "100%",
						height: "100%",
						children: /* @__PURE__ */ jsxs(LineChart, {
							data: dailyActivity,
							children: [
								/* @__PURE__ */ jsx(CartesianGrid, {
									strokeDasharray: "3 3",
									stroke: "var(--border)",
									vertical: false
								}),
								/* @__PURE__ */ jsx(XAxis, {
									dataKey: "date",
									tick: { fontSize: 11 }
								}),
								/* @__PURE__ */ jsx(YAxis, { tick: { fontSize: 11 } }),
								/* @__PURE__ */ jsx(Tooltip, {}),
								/* @__PURE__ */ jsx(Line, {
									type: "monotone",
									dataKey: "leads",
									stroke: "var(--chart-1)",
									strokeWidth: 2,
									dot: false
								}),
								/* @__PURE__ */ jsx(Line, {
									type: "monotone",
									dataKey: "emails",
									stroke: "var(--chart-2)",
									strokeWidth: 2,
									dot: false
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
				})] }),
				/* @__PURE__ */ jsxs(Card, { children: [/* @__PURE__ */ jsx(CardHeader, { children: /* @__PURE__ */ jsx(SectionCardTitle, {
					title: "Funnel",
					hint: "Current CRM counts"
				}) }), /* @__PURE__ */ jsx(CardContent, {
					className: "h-72",
					children: /* @__PURE__ */ jsx(ResponsiveContainer, {
						width: "100%",
						height: "100%",
						children: /* @__PURE__ */ jsxs(PieChart, { children: [/* @__PURE__ */ jsx(Pie, {
							data: funnel,
							dataKey: "value",
							nameKey: "label",
							innerRadius: 55,
							outerRadius: 95,
							children: funnel.map((_, index) => /* @__PURE__ */ jsx(Cell, { fill: COLORS[index % COLORS.length] }, index))
						}), /* @__PURE__ */ jsx(Tooltip, {})] })
					})
				})] }),
				/* @__PURE__ */ jsxs(Card, { children: [/* @__PURE__ */ jsx(CardHeader, { children: /* @__PURE__ */ jsx(SectionCardTitle, {
					title: "Today by product",
					hint: "Lead counts and remaining targets"
				}) }), /* @__PURE__ */ jsx(CardContent, {
					className: "space-y-2",
					children: Object.entries(stats.today_leads).map(([segment, target]) => /* @__PURE__ */ jsxs("div", {
						className: "rounded-md border px-3 py-2",
						children: [/* @__PURE__ */ jsxs("div", {
							className: "flex items-center justify-between gap-3",
							children: [/* @__PURE__ */ jsx("p", {
								className: "truncate text-sm font-medium",
								children: segment
							}), /* @__PURE__ */ jsxs(Badge, {
								variant: "secondary",
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
				})] })
			]
		})]
	});
}
//#endregion
export { AnalyticsPage as component };
