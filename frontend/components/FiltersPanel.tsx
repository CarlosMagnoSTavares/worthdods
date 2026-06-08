"use client";

import { Filters } from "@/types";

const UFS = [
  "AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS",
  "MT","PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC",
  "SE","SP","TO",
];

interface FiltersPanelProps {
  filters: Filters;
  onChange: (f: Filters) => void;
}

export function FiltersPanel({ filters, onChange }: FiltersPanelProps) {
  const set = (key: keyof Filters, value: unknown) =>
    onChange({ ...filters, [key]: value || undefined, page: 1 });

  return (
    <aside
      className="rounded-xl border p-5 space-y-5 sticky top-4"
      style={{
        background: "#fff",
        borderColor: "var(--border)",
        boxShadow: "0 2px 8px rgba(13,17,23,0.08)",
      }}
    >
      <h2 className="font-serif text-lg" style={{ color: "var(--ink)" }}>
        Filtros
      </h2>

      {/* Estado */}
      <div>
        <label className="text-xs uppercase tracking-wider font-semibold block mb-1.5" style={{ color: "var(--mid)" }}>
          Estado
        </label>
        <select
          value={filters.uf || ""}
          onChange={(e) => set("uf", e.target.value)}
          className="w-full px-3 py-2 text-sm rounded-lg border outline-none focus:border-yellow-600"
          style={{ borderColor: "var(--border)", background: "var(--cream)" }}
        >
          <option value="">Todos os estados</option>
          {UFS.map((uf) => (
            <option key={uf} value={uf}>{uf}</option>
          ))}
        </select>
      </div>

      {/* Cidade */}
      <div>
        <label className="text-xs uppercase tracking-wider font-semibold block mb-1.5" style={{ color: "var(--mid)" }}>
          Cidade
        </label>
        <input
          type="text"
          placeholder="Ex: Campinas"
          value={filters.cidade || ""}
          onChange={(e) => set("cidade", e.target.value)}
          className="w-full px-3 py-2 text-sm rounded-lg border outline-none focus:border-yellow-600"
          style={{ borderColor: "var(--border)", background: "var(--cream)" }}
        />
      </div>

      {/* Score IPL mínimo */}
      <div>
        <label className="text-xs uppercase tracking-wider font-semibold block mb-1.5" style={{ color: "var(--mid)" }}>
          Score IPL mínimo: {filters.ipl_min || 0}
        </label>
        <input
          type="range"
          min={0}
          max={10}
          step={0.5}
          value={filters.ipl_min || 0}
          onChange={(e) => set("ipl_min", Number(e.target.value) || undefined)}
          className="w-full accent-yellow-700"
        />
        <div className="flex justify-between text-xs mt-1" style={{ color: "var(--mid)" }}>
          <span>0</span><span>10</span>
        </div>
      </div>

      {/* Preço máximo */}
      <div>
        <label className="text-xs uppercase tracking-wider font-semibold block mb-1.5" style={{ color: "var(--mid)" }}>
          Preço máximo (R$)
        </label>
        <input
          type="number"
          placeholder="Ex: 500000"
          value={filters.preco_max || ""}
          onChange={(e) => set("preco_max", Number(e.target.value) || undefined)}
          className="w-full px-3 py-2 text-sm rounded-lg border outline-none focus:border-yellow-600"
          style={{ borderColor: "var(--border)", background: "var(--cream)" }}
        />
      </div>

      {/* Toggles */}
      <div className="space-y-2.5">
        {[
          { key: "aceita_fgts", label: "Aceita FGTS" },
          { key: "aceita_financiamento", label: "Aceita Financiamento" },
        ].map(({ key, label }) => (
          <label key={key} className="flex items-center gap-2.5 cursor-pointer">
            <input
              type="checkbox"
              checked={!!filters[key as keyof Filters]}
              onChange={(e) => set(key as keyof Filters, e.target.checked || undefined)}
              className="rounded accent-yellow-700 w-4 h-4"
            />
            <span className="text-sm" style={{ color: "var(--ink)" }}>
              {label}
            </span>
          </label>
        ))}
      </div>

      {/* Ordenação */}
      <div>
        <label className="text-xs uppercase tracking-wider font-semibold block mb-1.5" style={{ color: "var(--mid)" }}>
          Ordenar por
        </label>
        <select
          value={`${filters.order_by || "ipl_score"}_${filters.order_dir || "desc"}`}
          onChange={(e) => {
            const [by, dir] = e.target.value.split("_");
            onChange({ ...filters, order_by: by, order_dir: dir, page: 1 });
          }}
          className="w-full px-3 py-2 text-sm rounded-lg border outline-none"
          style={{ borderColor: "var(--border)", background: "var(--cream)" }}
        >
          <option value="ipl_score_desc">Maior Score IPL</option>
          <option value="desconto_percentual_desc">Maior Desconto</option>
          <option value="preco_asc">Menor Preço</option>
          <option value="preco_desc">Maior Preço</option>
          <option value="updated_at_desc">Mais Recentes</option>
        </select>
      </div>

      {/* Limpar filtros */}
      <button
        onClick={() => onChange({ page: 1, order_by: "ipl_score", order_dir: "desc" })}
        className="w-full py-2 text-sm rounded-lg border transition-all hover:bg-gray-50"
        style={{ borderColor: "var(--border)", color: "var(--mid)" }}
      >
        Limpar filtros
      </button>
    </aside>
  );
}
