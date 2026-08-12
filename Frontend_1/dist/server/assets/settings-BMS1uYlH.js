import { g as useSettingsSnapshot, o as useDailyTargets, y as apiPut } from "./hooks-C4Tv24mh.js";
import { h as Button, m as Input, p as Separator } from "./router-Df8hO_k6.js";
import { a as CardContent, i as Card, n as SectionCardTitle, o as CardHeader, r as StateCard, t as PageHeader } from "./page-header-X6ihaif1.js";
import { t as Label } from "./label-BKJc-6Cg.js";
import { useEffect, useState } from "react";
import { jsx, jsxs } from "react/jsx-runtime";
import { toast } from "sonner";
//#region src/routes/settings.tsx?tsr-split=component
var DAILY_TARGET_FIELDS = [
	"target_leads_per_day",
	"companies_per_run",
	"contacts_per_company",
	"max_emails_per_batch"
];
function SettingsPage() {
	const settings = useSettingsSnapshot();
	const targets = useDailyTargets();
	const [settingsState, setSettingsState] = useState({});
	const [targetsState, setTargetsState] = useState({});
	useEffect(() => {
		if (settings.data) setSettingsState(Object.fromEntries(Object.entries(settings.data).map(([key, value]) => [key, String(value ?? "")])));
	}, [settings.data]);
	useEffect(() => {
		if (targets.data) setTargetsState(Object.fromEntries(targets.data.map((target) => [target.id, target])));
	}, [targets.data]);
	if (settings.isError || targets.isError) return /* @__PURE__ */ jsx(StateCard, {
		title: "Settings unavailable",
		description: settings.error?.message ?? targets.error?.message ?? "The settings endpoints returned an error."
	});
	if (settings.isLoading || targets.isLoading || !settings.data || !targets.data) return /* @__PURE__ */ jsx(StateCard, {
		title: "Loading settings",
		description: "Fetching workspace settings and daily targets."
	});
	async function saveSettings() {
		try {
			await apiPut("/settings", Object.entries(settingsState).map(([key, value]) => ({
				key,
				value
			})));
			toast.success("Settings saved");
			await settings.refetch();
		} catch (error) {
			toast.error(error instanceof Error ? error.message : "Could not save settings");
		}
	}
	async function saveTargets() {
		try {
			await apiPut("/daily-targets", Object.values(targetsState).map((target) => ({
				product_segment: target.product_segment,
				target_leads_per_day: Number(target.target_leads_per_day),
				companies_per_run: Number(target.companies_per_run),
				contacts_per_company: Number(target.contacts_per_company),
				max_emails_per_batch: Number(target.max_emails_per_batch),
				active: target.active,
				default_campaign_id: target.default_campaign_id,
				default_mailbox_id: target.default_mailbox_id
			})));
			toast.success("Daily targets saved");
			await targets.refetch();
		} catch (error) {
			toast.error(error instanceof Error ? error.message : "Could not save daily targets");
		}
	}
	return /* @__PURE__ */ jsxs("div", {
		className: "space-y-5",
		children: [/* @__PURE__ */ jsx(PageHeader, {
			title: "Settings",
			description: "Workspace settings, SMTP settings and daily lead targets"
		}), /* @__PURE__ */ jsxs("div", {
			className: "grid gap-4 lg:grid-cols-2",
			children: [/* @__PURE__ */ jsxs(Card, { children: [/* @__PURE__ */ jsx(CardHeader, { children: /* @__PURE__ */ jsx(SectionCardTitle, {
				title: "Workspace settings",
				hint: "Stored in the backend settings table"
			}) }), /* @__PURE__ */ jsxs(CardContent, {
				className: "space-y-4",
				children: [Object.entries(settingsState).map(([key, value]) => /* @__PURE__ */ jsxs("div", {
					className: "space-y-1.5",
					children: [/* @__PURE__ */ jsx(Label, {
						htmlFor: key,
						children: key
					}), /* @__PURE__ */ jsx(Input, {
						id: key,
						value,
						onChange: (e) => setSettingsState((prev) => ({
							...prev,
							[key]: e.target.value
						}))
					})]
				}, key)), /* @__PURE__ */ jsx(Button, {
					onClick: () => void saveSettings(),
					children: "Save workspace settings"
				})]
			})] }), /* @__PURE__ */ jsxs(Card, { children: [/* @__PURE__ */ jsx(CardHeader, { children: /* @__PURE__ */ jsx(SectionCardTitle, {
				title: "Daily lead targets",
				hint: "Per-product targets and caps"
			}) }), /* @__PURE__ */ jsxs(CardContent, {
				className: "space-y-4",
				children: [Object.values(targetsState).map((target) => /* @__PURE__ */ jsxs("div", {
					className: "rounded-md border p-3",
					children: [
						/* @__PURE__ */ jsx("p", {
							className: "text-sm font-medium",
							children: target.product_segment
						}),
						/* @__PURE__ */ jsx("div", {
							className: "mt-3 grid gap-3 sm:grid-cols-2",
							children: DAILY_TARGET_FIELDS.map((field) => /* @__PURE__ */ jsxs("div", {
								className: "space-y-1",
								children: [/* @__PURE__ */ jsx(Label, {
									className: "text-xs",
									children: field
								}), /* @__PURE__ */ jsx(Input, {
									type: "number",
									value: String(target[field] ?? ""),
									onChange: (e) => setTargetsState((prev) => ({
										...prev,
										[target.id]: {
											...target,
											[field]: Number(e.target.value)
										}
									}))
								})]
							}, field))
						}),
						/* @__PURE__ */ jsx(Separator, { className: "my-3" }),
						/* @__PURE__ */ jsxs("div", {
							className: "flex items-center justify-between gap-3",
							children: [/* @__PURE__ */ jsx("p", {
								className: "text-xs text-muted-foreground",
								children: "Active"
							}), /* @__PURE__ */ jsx(Button, {
								variant: target.active ? "secondary" : "outline",
								size: "sm",
								onClick: () => setTargetsState((prev) => ({
									...prev,
									[target.id]: {
										...target,
										active: !target.active
									}
								})),
								children: target.active ? "Enabled" : "Disabled"
							})]
						})
					]
				}, target.id)), /* @__PURE__ */ jsx(Button, {
					onClick: () => void saveTargets(),
					children: "Save daily targets"
				})]
			})] })]
		})]
	});
}
//#endregion
export { SettingsPage as component };
