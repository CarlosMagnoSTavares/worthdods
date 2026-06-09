import type { Filters, PropertiesResponse, PropertyDetail, LegalSummary } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}/api/v1${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export function buildQueryString(filters: Filters): string {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") {
      params.set(k, String(v));
    }
  });
  return params.toString();
}

export const api = {
  properties: {
    list: (filters: Filters = {}): Promise<PropertiesResponse> => {
      const qs = buildQueryString(filters);
      return apiFetch(`/properties${qs ? `?${qs}` : ""}`);
    },

    get: (id: string): Promise<PropertyDetail> => apiFetch(`/properties/${id}`),

    stats: () => apiFetch<Record<string, unknown>>("/properties/stats"),

    analyze: (id: string): Promise<{ message: string; status: string; analyses?: unknown[]; legal_checks?: unknown[] }> =>
      apiFetch(`/properties/${id}/analyze`, { method: "POST" }),

    getAnalysis: (id: string): Promise<{ property_id: string; analyses: unknown[]; legal_checks: unknown[]; legal_summary: LegalSummary; has_analysis: boolean; is_processing: boolean }> =>
      apiFetch(`/properties/${id}/analysis`),

    getLegal: (id: string) => apiFetch(`/properties/${id}/legal`),
  },
};
