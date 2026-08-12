import { useQuery } from "@tanstack/react-query";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import axios from "axios";
//#region src/lib/utils.ts
function cn(...inputs) {
	return twMerge(clsx(inputs));
}
//#endregion
//#region src/lib/api/client.ts
/**
* Base URL of the existing FastAPI backend.
* Override with VITE_API_BASE_URL when deploying.
*/
var API_BASE_URL = {
	"BASE_URL": "/",
	"DEV": false,
	"MODE": "production",
	"PROD": true,
	"SSR": true,
	"TSS_DEV_SERVER": "false",
	"TSS_DEV_SSR_STYLES_BASEPATH": "/",
	"TSS_DEV_SSR_STYLES_ENABLED": "true",
	"TSS_DISABLE_CSRF_MIDDLEWARE_WARNING": "false",
	"TSS_INLINE_CSS_ENABLED": "false",
	"TSS_ROUTER_BASEPATH": "",
	"TSS_SERVER_FN_BASE": "/_serverFn/"
}["VITE_API_BASE_URL"] ?? "http://localhost:8000";
var TOKEN_STORAGE_KEY = "yash.outreach.token";
function getToken() {
	if (typeof window === "undefined") return null;
	return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}
var api = axios.create({
	baseURL: API_BASE_URL,
	timeout: 12e3,
	headers: { "Content-Type": "application/json" }
});
function normalizePath(path) {
	return path.startsWith("/api/") ? path.slice(4) : path;
}
api.interceptors.request.use((config) => {
	const token = getToken();
	if (token) config.headers.Authorization = `Bearer ${token}`;
	return config;
});
api.interceptors.response.use(void 0, (error) => {
	const detail = error?.response?.data?.detail;
	if (detail) return Promise.reject(new Error(typeof detail === "string" ? detail : JSON.stringify(detail)));
	if (error?.request && !error?.response) return Promise.reject(/* @__PURE__ */ new Error(`Backend unavailable at ${API_BASE_URL}`));
	return Promise.reject(error);
});
/** GET helper that throws on failure so callers can fall back to sample data. */
async function apiGet(path, params) {
	return (await api.get(normalizePath(path), { params })).data;
}
async function apiPost(path, body) {
	return (await api.post(normalizePath(path), body)).data;
}
async function apiPut(path, body) {
	return (await api.put(normalizePath(path), body)).data;
}
//#endregion
//#region src/lib/api/hooks.ts
function useApiQuery(key, path, params) {
	return useQuery({
		queryKey: [...key, params ?? null],
		queryFn: () => apiGet(path, params),
		staleTime: 3e4
	});
}
var useCompanies = () => useApiQuery(["companies"], "/companies");
function useCompany(id) {
	return useApiQuery(["company", id], `/companies/${id}`);
}
var useContacts = () => useApiQuery(["contacts"], "/contacts");
function useContact(id) {
	return useApiQuery(["contact", id], `/contacts/${id}`);
}
var useCampaigns = () => useApiQuery(["campaigns"], "/campaigns");
var useDrafts = () => useApiQuery(["drafts"], "/drafts");
var useMessages = () => useApiQuery(["messages"], "/messages");
var useDashboardSummary = () => useApiQuery(["dashboard-summary"], "/dashboard");
var useDashboardStats = () => useApiQuery(["dashboard-stats"], "/dashboard/stats");
var useDiscoveryRuns = () => useApiQuery(["discovery-runs"], "/discovery/runs");
var useDiscoveryStaging = (offset = 0, limit = 50) => useApiQuery([
	"discovery-staging",
	offset,
	limit
], "/discovery/staging", {
	offset,
	limit
});
var useDiscoveryStagingDetail = (recordId) => useQuery({
	queryKey: ["discovery-staging-detail", recordId],
	queryFn: () => apiGet(`/discovery/staging/${recordId}`),
	enabled: recordId !== null,
	staleTime: 6e4
});
var useManualReview = (offset = 0, limit = 50) => useApiQuery([
	"discovery-manual-review",
	offset,
	limit
], "/discovery/manual-review", {
	offset,
	limit
});
var useDiscoveryProfiles = () => useApiQuery(["discovery-profiles"], "/discovery/search-profiles");
var useSettingsSnapshot = () => useApiQuery(["settings"], "/settings");
var useWorkspaceProfile = () => useApiQuery(["workspace-profile"], "/workspace/profile");
var useDailyTargets = () => useApiQuery(["daily-targets"], "/daily-targets");
//#endregion
export { useWorkspaceProfile as _, useContacts as a, cn as b, useDashboardSummary as c, useDiscoveryStaging as d, useDiscoveryStagingDetail as f, useSettingsSnapshot as g, useMessages as h, useContact as i, useDiscoveryProfiles as l, useManualReview as m, useCompanies as n, useDailyTargets as o, useDrafts as p, useCompany as r, useDashboardStats as s, useCampaigns as t, useDiscoveryRuns as u, apiPost as v, apiPut as y };
