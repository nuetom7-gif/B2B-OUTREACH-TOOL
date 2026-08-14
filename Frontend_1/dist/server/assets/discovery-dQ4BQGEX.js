import { d as useDiscoveryStaging, f as useDiscoveryStagingDetail, l as useDiscoveryProfiles, u as useDiscoveryRuns, v as apiPost, x as cn } from "./hooks-xnZ2zKrZ.js";
import { d as Badge, h as Button, m as Input, p as Separator } from "./router-B42mCDaV.js";
import { a as CardContent, i as Card, n as SectionCardTitle, o as CardHeader, r as StateCard, t as PageHeader } from "./page-header-B6w8wS7t.js";
import { n as StatusBadge } from "./status-badge-Bg9EAcqh.js";
import { a as SelectValue, i as SelectTrigger, n as SelectContent, r as SelectItem, t as Select } from "./select-CeKRNVBa.js";
import { t as Label } from "./label-D0XH9_BV.js";
import { i as TabsTrigger, n as TabsContent, r as TabsList, t as Tabs } from "./tabs-_Tn7Xtfh.js";
import * as React from "react";
import { useMemo, useState } from "react";
import { Fragment, jsx, jsxs } from "react/jsx-runtime";
import { Activity, Coins, Play, Radar, RefreshCw, Server } from "lucide-react";
import { toast } from "sonner";
import * as ProgressPrimitive from "@radix-ui/react-progress";
//#region src/components/ui/progress.tsx
var Progress = React.forwardRef(({ className, value, ...props }, ref) => /* @__PURE__ */ jsx(ProgressPrimitive.Root, {
	ref,
	className: cn("relative h-2 w-full overflow-hidden rounded-full bg-primary/20", className),
	...props,
	children: /* @__PURE__ */ jsx(ProgressPrimitive.Indicator, {
		className: "h-full w-full flex-1 bg-primary transition-all",
		style: { transform: `translateX(-${100 - (value || 0)}%)` }
	})
}));
Progress.displayName = ProgressPrimitive.Root.displayName;
//#endregion
//#region src/routes/discovery.tsx?tsr-split=component
function DiscoveryPage() {
	const profiles = useDiscoveryProfiles();
	const runs = useDiscoveryRuns();
	const staging = useDiscoveryStaging();
	const [profileName, setProfileName] = useState("");
	const [country, setCountry] = useState("India");
	const [state, setState] = useState("any");
	const [city, setCity] = useState("");
	const [companyLimit, setCompanyLimit] = useState("50");
	const [contactsPerCompany, setContactsPerCompany] = useState("2");
	const [submitting, setSubmitting] = useState(false);
	const enabledProfiles = profiles.data ?? [];
	const selectedProfile = enabledProfiles.find((profile) => profile.profile_name === profileName);
	const latestRun = useMemo(() => runs.data?.[0] ?? null, [runs.data]);
	const latestStage = useMemo(() => staging.data?.items[0] ?? null, [staging.data]);
	const stageDetail = useDiscoveryStagingDetail(latestStage?.id ?? null);
	if (profiles.isError || runs.isError || staging.isError) {
		const message = profiles.error?.message ?? runs.error?.message ?? staging.error?.message ?? "Discovery endpoints are unavailable.";
		return /* @__PURE__ */ jsx(StateCard, {
			title: "Discovery unavailable",
			description: message
		});
	}
	async function runDiscovery() {
		if (!profileName) {
			toast.error("Select a discovery profile first");
			return;
		}
		setSubmitting(true);
		try {
			await apiPost("/discovery/run", {
				profile_name: profileName,
				country,
				state: state === "any" ? null : state,
				city: city.trim() || null,
				company_limit: Number(companyLimit),
				contacts_per_company: Number(contactsPerCompany)
			});
			toast.success("Discovery run queued");
			await Promise.all([runs.refetch(), staging.refetch()]);
		} catch (error) {
			toast.error(error instanceof Error ? error.message : "Could not reach the discovery engine");
		} finally {
			setSubmitting(false);
		}
	}
	if (profiles.isLoading || runs.isLoading || staging.isLoading) return /* @__PURE__ */ jsx(StateCard, {
		title: "Loading discovery",
		description: "Fetching live profiles, runs and diagnostics."
	});
	const rawRecord = stageDetail.data?.raw_organization ?? {};
	const peopleResponse = stageDetail.data?.raw_people_response ?? {};
	const normalizedCompany = stageDetail.data?.normalized_company ?? {};
	const normalizedContacts = stageDetail.data?.normalized_contacts ?? [];
	const qualificationInput = stageDetail.data?.qualification_input ?? {};
	const recordProgress = latestRun && latestRun.companies_found > 0 ? Math.min(100, Math.round((latestRun.qualification_imported_count + latestRun.qualification_manual_review_count + latestRun.qualification_rejected_count) / Math.max(1, latestRun.companies_found) * 100)) : 0;
	return /* @__PURE__ */ jsxs("div", {
		className: "space-y-5",
		children: [/* @__PURE__ */ jsx(PageHeader, {
			title: "Discovery",
			description: "Search Apollo for companies and decision makers that match a backend ICP profile.",
			actions: /* @__PURE__ */ jsxs(Button, {
				variant: "outline",
				onClick: () => void Promise.all([
					profiles.refetch(),
					runs.refetch(),
					staging.refetch()
				]),
				children: [/* @__PURE__ */ jsx(RefreshCw, { className: "size-4" }), " Refresh"]
			})
		}), /* @__PURE__ */ jsxs("div", {
			className: "grid gap-4 xl:grid-cols-[380px_minmax(0,1fr)]",
			children: [/* @__PURE__ */ jsxs(Card, {
				className: "h-fit",
				children: [/* @__PURE__ */ jsx(CardHeader, { children: /* @__PURE__ */ jsx(SectionCardTitle, {
					title: "New discovery run",
					hint: "Parameters are passed to the backend engine"
				}) }), /* @__PURE__ */ jsxs(CardContent, {
					className: "space-y-3.5",
					children: [
						/* @__PURE__ */ jsxs("div", {
							className: "space-y-1.5",
							children: [/* @__PURE__ */ jsx(Label, { children: "Profile" }), /* @__PURE__ */ jsxs(Select, {
								value: profileName,
								onValueChange: setProfileName,
								children: [/* @__PURE__ */ jsx(SelectTrigger, { children: /* @__PURE__ */ jsx(SelectValue, { placeholder: "Select a profile" }) }), /* @__PURE__ */ jsx(SelectContent, { children: enabledProfiles.map((profile) => /* @__PURE__ */ jsx(SelectItem, {
									value: profile.profile_name,
									children: profile.profile_name
								}, profile.profile_name)) })]
							})]
						}),
						selectedProfile ? /* @__PURE__ */ jsxs("div", {
							className: "space-y-3 rounded-lg border border-border/70 bg-muted/20 p-3",
							children: [
								/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("p", {
									className: "text-sm font-medium",
									children: "Apollo search criteria"
								}), /* @__PURE__ */ jsx("p", {
									className: "text-xs text-muted-foreground",
									children: "Read-only criteria from the selected backend profile."
								})] }),
								/* @__PURE__ */ jsx(CriteriaTags, {
									label: "Company keywords",
									values: selectedProfile.company_keywords
								}),
								/* @__PURE__ */ jsx(CriteriaTags, {
									label: "Primary industry signals",
									values: selectedProfile.apollo_industries
								}),
								/* @__PURE__ */ jsx(CriteriaTags, {
									label: "Related industry signals",
									values: selectedProfile.related_industries
								})
							]
						}) : null,
						/* @__PURE__ */ jsxs("div", {
							className: "grid grid-cols-2 gap-3",
							children: [/* @__PURE__ */ jsxs("div", {
								className: "space-y-1.5",
								children: [/* @__PURE__ */ jsx(Label, { children: "Country" }), /* @__PURE__ */ jsx(Input, {
									value: country,
									onChange: (e) => setCountry(e.target.value)
								})]
							}), /* @__PURE__ */ jsxs("div", {
								className: "space-y-1.5",
								children: [/* @__PURE__ */ jsx(Label, { children: "State (optional)" }), /* @__PURE__ */ jsx(Input, {
									value: state,
									onChange: (e) => setState(e.target.value),
									placeholder: "Any state"
								})]
							})]
						}),
						/* @__PURE__ */ jsxs("div", {
							className: "space-y-1.5",
							children: [
								/* @__PURE__ */ jsx(Label, { children: "City / district (optional)" }),
								/* @__PURE__ */ jsx(Input, {
									value: city,
									onChange: (e) => setCity(e.target.value),
									placeholder: "Aurangabad"
								}),
								/* @__PURE__ */ jsx("p", {
									className: "text-xs text-muted-foreground",
									children: "Apollo will search company headquarters in this city, state and country."
								})
							]
						}),
						/* @__PURE__ */ jsxs("div", {
							className: "grid grid-cols-2 gap-3",
							children: [/* @__PURE__ */ jsxs("div", {
								className: "space-y-1.5",
								children: [/* @__PURE__ */ jsx(Label, { children: "Company limit" }), /* @__PURE__ */ jsx(Input, {
									value: companyLimit,
									onChange: (e) => setCompanyLimit(e.target.value),
									type: "number",
									min: 1
								})]
							}), /* @__PURE__ */ jsxs("div", {
								className: "space-y-1.5",
								children: [/* @__PURE__ */ jsx(Label, { children: "Contacts / company" }), /* @__PURE__ */ jsx(Input, {
									value: contactsPerCompany,
									onChange: (e) => setContactsPerCompany(e.target.value),
									type: "number",
									min: 1
								})]
							})]
						}),
						/* @__PURE__ */ jsxs(Button, {
							className: "w-full",
							onClick: runDiscovery,
							disabled: submitting || !profileName,
							children: [
								/* @__PURE__ */ jsx(Play, { className: "size-4" }),
								" ",
								submitting ? "Queuing…" : "Run discovery"
							]
						}),
						/* @__PURE__ */ jsx("p", {
							className: "text-xs text-muted-foreground",
							children: "The backend applies throttling, opt-out filtering and qualification."
						})
					]
				})]
			}), /* @__PURE__ */ jsxs("div", {
				className: "min-w-0 space-y-4",
				children: [/* @__PURE__ */ jsxs(Card, { children: [/* @__PURE__ */ jsxs(CardHeader, {
					className: "flex-row items-center justify-between gap-3",
					children: [/* @__PURE__ */ jsx(SectionCardTitle, {
						title: "Latest run",
						hint: latestRun ? `${latestRun.product_name} · ${latestRun.search_frequency}` : "No runs yet"
					}), latestRun ? /* @__PURE__ */ jsx(StatusBadge, { status: latestRun.status }) : null]
				}), /* @__PURE__ */ jsx(CardContent, {
					className: "space-y-4",
					children: latestRun ? /* @__PURE__ */ jsxs(Fragment, { children: [
						/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsxs("div", {
							className: "mb-1.5 flex items-center justify-between text-sm",
							children: [/* @__PURE__ */ jsxs("span", {
								className: "truncate text-muted-foreground",
								children: ["Started ", new Date(latestRun.started_at).toLocaleString()]
							}), /* @__PURE__ */ jsxs("span", {
								className: "text-numeric font-medium",
								children: [recordProgress, "%"]
							})]
						}), /* @__PURE__ */ jsx(Progress, { value: recordProgress })] }),
						/* @__PURE__ */ jsx("div", {
							className: "grid grid-cols-2 gap-3 sm:grid-cols-4",
							children: [
								{
									label: "API calls",
									value: latestRun.api_calls_used,
									icon: /* @__PURE__ */ jsx(Server, { className: "size-3.5" })
								},
								{
									label: "Credits left",
									value: latestRun.quota_remaining ?? 0,
									icon: /* @__PURE__ */ jsx(Coins, { className: "size-3.5" })
								},
								{
									label: "Companies",
									value: latestRun.companies_found,
									icon: /* @__PURE__ */ jsx(Radar, { className: "size-3.5" })
								},
								{
									label: "Contacts",
									value: latestRun.contacts_found,
									icon: /* @__PURE__ */ jsx(Activity, { className: "size-3.5" })
								}
							].map((item) => /* @__PURE__ */ jsxs("div", {
								className: "rounded-md border p-3",
								children: [/* @__PURE__ */ jsxs("p", {
									className: "flex items-center gap-1.5 text-xs text-muted-foreground",
									children: [
										item.icon,
										" ",
										item.label
									]
								}), /* @__PURE__ */ jsx("p", {
									className: "mt-1 text-lg font-semibold text-numeric",
									children: item.value
								})]
							}, item.label))
						}),
						/* @__PURE__ */ jsx(Separator, {}),
						/* @__PURE__ */ jsx("div", {
							className: "grid gap-3 sm:grid-cols-3",
							children: [
								["Imported", latestRun.qualification_imported_count],
								["Manual review", latestRun.qualification_manual_review_count],
								["Rejected", latestRun.qualification_rejected_count]
							].map(([label, value]) => /* @__PURE__ */ jsxs("div", {
								className: "rounded-md border px-3 py-2",
								children: [/* @__PURE__ */ jsx("p", {
									className: "text-xs text-muted-foreground",
									children: label
								}), /* @__PURE__ */ jsx("p", {
									className: "text-numeric text-lg font-semibold",
									children: value
								})]
							}, String(label)))
						})
					] }) : /* @__PURE__ */ jsx("div", {
						className: "py-8 text-sm text-muted-foreground",
						children: "No discovery runs found yet."
					})
				})] }), /* @__PURE__ */ jsxs(Card, { children: [/* @__PURE__ */ jsx(CardHeader, { children: /* @__PURE__ */ jsx(SectionCardTitle, { title: "Diagnostics & history" }) }), /* @__PURE__ */ jsx(CardContent, { children: /* @__PURE__ */ jsxs(Tabs, {
					defaultValue: "history",
					children: [
						/* @__PURE__ */ jsxs(TabsList, {
							className: "flex-wrap",
							children: [
								/* @__PURE__ */ jsx(TabsTrigger, {
									value: "history",
									children: "History"
								}),
								/* @__PURE__ */ jsx(TabsTrigger, {
									value: "raw",
									children: "Raw Apollo data"
								}),
								/* @__PURE__ */ jsx(TabsTrigger, {
									value: "normalized",
									children: "Normalized"
								}),
								/* @__PURE__ */ jsx(TabsTrigger, {
									value: "qualification",
									children: "Qualification"
								})
							]
						}),
						stageDetail.isLoading ? /* @__PURE__ */ jsx("p", {
							className: "mt-3 text-sm text-muted-foreground",
							children: "Loading diagnostics for the latest record..."
						}) : stageDetail.isError ? /* @__PURE__ */ jsxs("p", {
							className: "mt-3 text-sm text-destructive",
							children: ["Diagnostic data unavailable: ", stageDetail.error.message]
						}) : null,
						/* @__PURE__ */ jsx(TabsContent, {
							value: "history",
							className: "space-y-2",
							children: runs.data?.length === 0 ? /* @__PURE__ */ jsx("div", {
								className: "py-8 text-sm text-muted-foreground",
								children: "No runs found."
							}) : runs.data?.map((run) => /* @__PURE__ */ jsxs("div", {
								className: "grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 rounded-md border px-3 py-2.5",
								children: [/* @__PURE__ */ jsxs("div", {
									className: "min-w-0",
									children: [/* @__PURE__ */ jsx("p", {
										className: "truncate text-sm font-medium",
										children: run.product_name
									}), /* @__PURE__ */ jsxs("p", {
										className: "truncate text-xs text-muted-foreground",
										children: [
											run.search_frequency,
											" · ",
											run.companies_found,
											" companies · ",
											run.contacts_found,
											" contacts ·",
											" ",
											run.api_calls_used,
											" API calls"
										]
									})]
								}), /* @__PURE__ */ jsx(StatusBadge, { status: run.status })]
							}, run.id))
						}),
						/* @__PURE__ */ jsxs(TabsContent, {
							value: "raw",
							children: [/* @__PURE__ */ jsx("pre", {
								className: "max-h-72 overflow-auto rounded-md border bg-muted/40 p-3 text-[11px] leading-relaxed",
								children: JSON.stringify(rawRecord, null, 2)
							}), /* @__PURE__ */ jsx("pre", {
								className: "mt-3 max-h-72 overflow-auto rounded-md border bg-muted/40 p-3 text-[11px] leading-relaxed",
								children: JSON.stringify(peopleResponse, null, 2)
							})]
						}),
						/* @__PURE__ */ jsx(TabsContent, {
							value: "normalized",
							children: /* @__PURE__ */ jsx("pre", {
								className: "max-h-72 overflow-auto rounded-md border bg-muted/40 p-3 text-[11px] leading-relaxed",
								children: JSON.stringify({
									normalized_company: normalizedCompany,
									normalized_contacts: normalizedContacts
								}, null, 2)
							})
						}),
						/* @__PURE__ */ jsx(TabsContent, {
							value: "qualification",
							className: "space-y-2",
							children: /* @__PURE__ */ jsxs("div", {
								className: "rounded-md border p-3",
								children: [
									/* @__PURE__ */ jsxs("div", {
										className: "flex items-center gap-2",
										children: [/* @__PURE__ */ jsx(StatusBadge, { status: latestStage?.qualification_status ?? "staged" }), /* @__PURE__ */ jsxs("span", {
											className: "text-sm font-medium",
											children: ["Score ", latestStage?.score ?? 0]
										})]
									}),
									/* @__PURE__ */ jsx("p", {
										className: "mt-2 text-sm text-muted-foreground",
										children: latestStage?.reason_category ?? "No qualification record available."
									}),
									/* @__PURE__ */ jsx("pre", {
										className: "mt-3 max-h-72 overflow-auto rounded-md border bg-muted/40 p-3 text-[11px] leading-relaxed",
										children: JSON.stringify(qualificationInput, null, 2)
									})
								]
							})
						})
					]
				}) })] })]
			})]
		})]
	});
}
function CriteriaTags({ label, values }) {
	if (!values?.length) return null;
	return /* @__PURE__ */ jsxs("div", {
		className: "space-y-1.5",
		children: [/* @__PURE__ */ jsx("p", {
			className: "text-xs font-medium text-muted-foreground",
			children: label
		}), /* @__PURE__ */ jsx("div", {
			className: "flex flex-wrap gap-1.5",
			children: values.map((value) => /* @__PURE__ */ jsx(Badge, {
				variant: "secondary",
				className: "font-normal",
				children: value
			}, value))
		})]
	});
}
//#endregion
export { DiscoveryPage as component };
