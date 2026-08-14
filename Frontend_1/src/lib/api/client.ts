import axios from "axios";

/**
 * Base URL of the existing FastAPI backend.
 * Override with VITE_API_BASE_URL when deploying.
 */
export const API_BASE_URL =
  (import.meta.env["VITE_API_BASE_URL"] as string | undefined) ?? "http://localhost:8000";

/** Shared local-development key accepted by FastAPI write endpoints. */
export const WRITE_API_KEY =
  (import.meta.env["VITE_WRITE_API_KEY"] as string | undefined) ?? "";

export const TOKEN_STORAGE_KEY = "yash.outreach.token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
  else window.localStorage.removeItem(TOKEN_STORAGE_KEY);
}

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 12_000,
  headers: { "Content-Type": "application/json" },
});

function normalizePath(path: string) {
  return path.startsWith("/api/") ? path.slice(4) : path;
}

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  if (WRITE_API_KEY && config.method && config.method.toLowerCase() !== "get") {
    config.headers["X-API-Key"] = WRITE_API_KEY;
  }
  return config;
});

api.interceptors.response.use(undefined, (error) => {
  const detail = error?.response?.data?.detail;
  if (detail) {
    return Promise.reject(new Error(typeof detail === "string" ? detail : JSON.stringify(detail)));
  }
  if (error?.request && !error?.response) {
    return Promise.reject(new Error(`Backend unavailable at ${API_BASE_URL}`));
  }
  return Promise.reject(error);
});

/** GET helper that throws on failure so callers can fall back to sample data. */
export async function apiGet<T>(path: string, params?: Record<string, unknown>): Promise<T> {
  const res = await api.get<T>(normalizePath(path), { params });
  return res.data;
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const res = await api.post<T>(normalizePath(path), body);
  return res.data;
}

export async function apiPatch<T>(path: string, body?: unknown): Promise<T> {
  const res = await api.patch<T>(normalizePath(path), body);
  return res.data;
}

export async function apiPut<T>(path: string, body?: unknown): Promise<T> {
  const res = await api.put<T>(normalizePath(path), body);
  return res.data;
}

export async function downloadCsv(path: string, filename: string): Promise<void> {
  const response = await api.get<Blob>(normalizePath(path), { responseType: "blob" });
  const url = window.URL.createObjectURL(response.data);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(url);
}
