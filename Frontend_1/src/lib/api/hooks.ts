import { useQuery } from "@tanstack/react-query";

import { apiGet } from "./client";
import type {
  BackendCampaign,
  BackendCompany,
  BackendContact,
  BackendContactDetail,
  BackendDashboardSummary,
  BackendDashboardStats,
  BackendDailyTarget,
  BackendDiscoveryProfile,
  BackendDiscoveryRun,
  BackendDiscoveryStagingRecord,
  BackendDiscoveryStagingPage,
  BackendDraft,
  BackendMailbox,
  BackendMessage,
  BackendSetting,
  BackendWorkspaceProfile,
} from "./types";

type QueryKey = readonly unknown[];

export function useApiQuery<T>(key: QueryKey, path: string, params?: Record<string, unknown>) {
  return useQuery({
    queryKey: [...key, params ?? null],
    queryFn: () => apiGet<T>(path, params),
    staleTime: 30_000,
  });
}

export const useCompanies = () => useApiQuery<BackendCompany[]>(["companies"], "/companies");

export function useCompany(id: string) {
  return useApiQuery<BackendCompany>(["company", id], `/companies/${id}`);
}

export const useContacts = () => useApiQuery<BackendContact[]>(["contacts"], "/contacts");

export function useContact(id: string) {
  return useApiQuery<BackendContactDetail>(["contact", id], `/contacts/${id}`);
}

export const useCampaigns = () => useApiQuery<BackendCampaign[]>(["campaigns"], "/campaigns");

export const useDrafts = () => useApiQuery<BackendDraft[]>(["drafts"], "/drafts");

export const useMessages = () => useApiQuery<BackendMessage[]>(["messages"], "/messages");

export const useMailboxList = () => useApiQuery<BackendMailbox[]>(["mailboxes"], "/mailboxes");

export const useDashboardSummary = () =>
  useApiQuery<BackendDashboardSummary>(["dashboard-summary"], "/dashboard");

export const useDashboardStats = () =>
  useApiQuery<BackendDashboardStats>(["dashboard-stats"], "/dashboard/stats");

export const useDiscoveryRuns = () =>
  useApiQuery<BackendDiscoveryRun[]>(["discovery-runs"], "/discovery/runs");

export const useDiscoveryStaging = (offset = 0, limit = 50) =>
  useApiQuery<BackendDiscoveryStagingPage>(["discovery-staging", offset, limit], "/discovery/staging", { offset, limit });

export const useDiscoveryStagingDetail = (recordId: number | null) =>
  useQuery({
    queryKey: ["discovery-staging-detail", recordId],
    queryFn: () => apiGet<BackendDiscoveryStagingRecord>(`/discovery/staging/${recordId}`),
    enabled: recordId !== null,
    staleTime: 60_000,
  });

export const useManualReview = (offset = 0, limit = 50) =>
  useApiQuery<BackendDiscoveryStagingPage>(["discovery-manual-review", offset, limit], "/discovery/manual-review", { offset, limit });

export const useDiscoverySummary = () =>
  useApiQuery<Record<string, unknown>>(["discovery-summary"], "/discovery/summary");

export const useDiscoveryProfiles = () =>
  useApiQuery<BackendDiscoveryProfile[]>(["discovery-profiles"], "/discovery/search-profiles");

export const useSettingsSnapshot = () =>
  useApiQuery<BackendSetting>(["settings"], "/settings");

export const useWorkspaceProfile = () =>
  useApiQuery<BackendWorkspaceProfile>(["workspace-profile"], "/workspace/profile");

export const useDailyTargets = () =>
  useApiQuery<BackendDailyTarget[]>(["daily-targets"], "/daily-targets");
