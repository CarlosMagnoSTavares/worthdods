"use client";

import { useState, useEffect, useCallback } from "react";
import { PropertyCard } from "@/components/PropertyCard";
import { FiltersPanel } from "@/components/FiltersPanel";
import { api } from "@/lib/api";
import type { Property, Filters, PropertiesResponse } from "@/types";

export default function DashboardPage() {
  const [filters, setFilters] = useState<Filters>({
    order_by: "ipl_score",
    order_dir: "desc",
    page: 1,
    page_size: 20,
  });
  const [data, setData] = useState<PropertiesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadProperties = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.properties.list(filters);
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar imóveis");
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadProperties();
  }, [loadProperties]);

  const handleFilterChange = (newFilters: Filters) => {
    setFilters({ ...newFilters, page_size: 20 });
  };

  const handlePageChange = (page: number) => {
    setFilters((f) => ({ ...f, page }));
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="font-serif text-3xl" style={{ color: "var(--ink)" }}>
          Imóveis em Leilão
        </h1>
        <p className="text-sm mt-1" style={{ color: "var(--mid)" }}>
          {data
            ? `${data.total.toLocaleString("pt-BR")} imóveis encontrados`
            : "Carregando..."}
        </p>
      </div>

      <div className="flex gap-6">
        {/* Filtros — sidebar */}
        <div className="hidden lg:block w-64 flex-shrink-0">
          <FiltersPanel filters={filters} onChange={handleFilterChange} />
        </div>

        {/* Grid de imóveis */}
        <div className="flex-1 min-w-0">
          {/* Mobile: filtros em dropdown */}
          <div className="lg:hidden mb-4">
            <details className="border rounded-xl" style={{ borderColor: "var(--border)" }}>
              <summary
                className="px-4 py-3 font-semibold cursor-pointer text-sm"
                style={{ color: "var(--ink)" }}
              >
                🔍 Filtros
              </summary>
              <div className="p-4">
                <FiltersPanel filters={filters} onChange={handleFilterChange} />
              </div>
            </details>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="h-72 rounded-xl animate-pulse"
                  style={{ background: "var(--cream)" }}
                />
              ))}
            </div>
          ) : error ? (
            <div
              className="rounded-xl p-8 text-center border"
              style={{
                background: "#fff5f5",
                borderColor: "#e57373",
                color: "var(--red)",
              }}
            >
              <p className="font-semibold">Erro ao carregar imóveis</p>
              <p className="text-sm mt-1 opacity-70">{error}</p>
              <button
                onClick={loadProperties}
                className="mt-4 px-5 py-2 text-sm rounded-lg font-semibold"
                style={{ background: "var(--ink)", color: "var(--paper)" }}
              >
                Tentar novamente
              </button>
            </div>
          ) : !data?.data?.length ? (
            <div
              className="rounded-xl p-8 text-center border"
              style={{ background: "#fff", borderColor: "var(--border)" }}
            >
              <div className="text-4xl mb-3">🏚️</div>
              <p className="font-semibold" style={{ color: "var(--ink)" }}>
                Nenhum imóvel encontrado
              </p>
              <p className="text-sm mt-1" style={{ color: "var(--mid)" }}>
                Tente ajustar os filtros
              </p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4 mb-6">
                {data.data.map((property: Property) => (
                  <PropertyCard key={property.id} property={property} />
                ))}
              </div>

              {/* Paginação */}
              {data.pages > 1 && (
                <div className="flex items-center justify-center gap-2 flex-wrap">
                  <button
                    onClick={() => handlePageChange((filters.page || 1) - 1)}
                    disabled={!filters.page || filters.page <= 1}
                    className="px-4 py-2 text-sm rounded-lg border disabled:opacity-40 hover:bg-gray-50"
                    style={{ borderColor: "var(--border)" }}
                  >
                    ← Anterior
                  </button>

                  {(() => {
                    const current = filters.page || 1;
                    const total = data.pages;
                    const pages: (number | "…")[] = [];
                    if (total <= 7) {
                      for (let i = 1; i <= total; i++) pages.push(i);
                    } else {
                      pages.push(1);
                      if (current > 3) pages.push("…");
                      for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) pages.push(i);
                      if (current < total - 2) pages.push("…");
                      pages.push(total);
                    }
                    return pages.map((p, i) =>
                      p === "…" ? (
                        <span key={`ellipsis-${i}`} className="px-2 py-2 text-sm" style={{ color: "var(--mid)" }}>…</span>
                      ) : (
                        <button
                          key={p}
                          onClick={() => handlePageChange(p as number)}
                          className="px-3 py-2 text-sm rounded-lg border font-medium"
                          style={{
                            borderColor: "var(--border)",
                            background: current === p ? "var(--ink)" : "#fff",
                            color: current === p ? "var(--gold-light)" : "var(--ink)",
                          }}
                        >
                          {p}
                        </button>
                      )
                    );
                  })()}

                  <button
                    onClick={() => handlePageChange((filters.page || 1) + 1)}
                    disabled={!data || (filters.page || 1) >= data.pages}
                    className="px-4 py-2 text-sm rounded-lg border disabled:opacity-40 hover:bg-gray-50"
                    style={{ borderColor: "var(--border)" }}
                  >
                    Próxima →
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
