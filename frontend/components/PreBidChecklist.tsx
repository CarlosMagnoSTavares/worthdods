"use client";

import { useState, useMemo } from "react";
import type { PropertyDetail, Analysis } from "@/types";

interface ChecklistItem {
  id: string;
  label: string;
  description: string;
  required: boolean;
  autoChecked: boolean;
  sourceUrl?: string;
  sourceLabel?: string;
  riskLevel?: "green" | "yellow" | "red";
  category: "edital" | "matricula" | "debt" | "occupancy" | "manual";
}

interface PreBidChecklistProps {
  property: PropertyDetail;
  analysis?: Analysis;
}

const sourceLinks: Record<string, { url: string; label: string }> = {
  caixa: {
    url: "https://venda-imoveis.caixa.gov.br/",
    label: "Portal Caixa",
  },
  matricula: {
    url: "https://www.registroimoveis.org.br/",
    label: "Cartório de Registro",
  },
  iptu: {
    url: "https://www.prefeitura.sp.gov.br/",
    label: "Prefeitura (IPTU)",
  },
  condominio: {
    url: "#",
    label: "Síndico / Administração",
  },
  certidoes: {
    url: "https://www.registros.net/",
    label: "Certidões Online",
  },
  google_maps: {
    url: "https://maps.google.com",
    label: "Google Maps",
  },
};

function buildChecklist(property: PropertyDetail, analysis?: Analysis): ChecklistItem[] {
  const items: ChecklistItem[] = [];

  items.push({
    id: "read-edital",
    label: "Ler edital completo",
    description: "Verificar todas as cláusulas, prazos e condições do leilão",
    required: true,
    autoChecked: !!analysis,
    sourceUrl: property.url_edital,
    sourceLabel: "📄 Edital",
    category: "edital",
  });

  items.push({
    id: "check-matricula",
    description: "Verificar matrícula atualizada no cartório",
    label: "Analisar matrícula",
    required: true,
    autoChecked: !!analysis && analysis.tipo === "matricula",
    sourceUrl: property.url_matricula,
    sourceLabel: "📜 Matrícula",
    category: "matricula",
  });

  items.push({
    id: "verify-debts",
    label: "Verificar débitos (IPTU, condomínio, taxas)",
    description: "Confirmar inexistência de débitos transferidos ao comprador",
    required: true,
    autoChecked: !!analysis?.dividas && analysis.dividas.length > 0,
    riskLevel: analysis?.risco_divida_iptu || analysis?.risco_divida_condominio ? "red" : "green",
    sourceUrl: sourceLinks.iptu.url,
    sourceLabel: "💰 Débitos",
    category: "debt",
  });

  items.push({
    id: "check-occupancy",
    label: "Confirmar situação de ocupação",
    description: "Verificar se imóvel está desocupado ou possui posse pendente",
    required: true,
    autoChecked: !!analysis?.status_ocupacao,
    riskLevel: analysis?.risco_ocupacao ? "red" : analysis?.ocupacao_risco_nivel === "MEDIO" ? "yellow" : "green",
    sourceLabel: "🏠 Ocupação",
    category: "occupancy",
  });

  items.push({
    id: "check-structural",
    label: "Avaliar estado estrutural",
    description: "Verificar fotos e descrição para danos visíveis",
    required: false,
    autoChecked: false,
    sourceUrl: sourceLinks.google_maps.url,
    sourceLabel: "🗺️ Mapa",
    category: "manual",
  });

  items.push({
    id: "check-litigation",
    label: "Verificar processos judiciais",
    description: "Confirmar inexistência de ações judiciais sobre o imóvel",
    required: true,
    autoChecked: !!analysis?.risco_processo_judicial !== undefined,
    riskLevel: analysis?.risco_processo_judicial ? "red" : "green",
    sourceLabel: "⚖️ Jurídico",
    category: "manual",
  });

  items.push({
    id: "calculate-costs",
    label: "Calcular custos totais",
    description: "Somar: preço + ITBI + registro + eventuais débitos + honorários",
    required: true,
    autoChecked: false,
    sourceLabel: "🧮 Custos",
    category: "manual",
  });

  items.push({
    id: "check-fgts",
    label: "Verificar financiamento / FGTS",
    description: "Confirmar condições de pagamento aceitas pelo leiloeiro",
    required: false,
    autoChecked: property.aceita_financiamento || property.aceita_fgts,
    category: "manual",
  });

  items.push({
    id: "check-certificate",
    label: "Solicitar certidões negativas",
    description: "Certidão negativa de débitos, protestos e ações reais",
    required: true,
    autoChecked: false,
    sourceUrl: sourceLinks.certidoes.url,
    sourceLabel: "📋 Certidões",
    category: "manual",
  });

  items.push({
    id: "verify-irregularity",
    label: "Verificar irregularidades",
    description: "Checar construção irregular, área não registrada, etc.",
    required: true,
    autoChecked: !!analysis?.risco_irregularidade !== undefined,
    riskLevel: analysis?.risco_irregularidade ? "red" : "green",
    sourceLabel: "🔍 Irregularidade",
    category: "manual",
  });

  return items;
}

export function PreBidChecklist({ property, analysis }: PreBidChecklistProps) {
  const [checked, setChecked] = useState<Set<string>>(() => {
    const initial = new Set<string>();
    const items = buildChecklist(property, analysis);
    items.forEach((item) => {
      if (item.autoChecked) initial.add(item.id);
    });
    return initial;
  });

  const items = useMemo(() => buildChecklist(property, analysis), [property, analysis]);

  const toggle = (id: string) => {
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const requiredItems = items.filter((i) => i.required);
  const requiredChecked = requiredItems.filter((i) => checked.has(i.id)).length;
  const allRequired = requiredChecked === requiredItems.length;
  const progress = Math.round((requiredChecked / requiredItems.length) * 100);

  const riskColor = (level?: string) => {
    if (level === "red") return "#c0392b";
    if (level === "yellow") return "#d4a017";
    return "#1a6b3c";
  };

  const riskBg = (level?: string) => {
    if (level === "red") return "#fde8e8";
    if (level === "yellow") return "#fff8e1";
    return "#d4edda";
  };

  const grouped = {
    edital: items.filter((i) => i.category === "edital"),
    matricula: items.filter((i) => i.category === "matricula"),
    debt: items.filter((i) => i.category === "debt"),
    occupancy: items.filter((i) => i.category === "occupancy"),
    manual: items.filter((i) => i.category === "manual"),
  };

  const categoryLabels: Record<string, { icon: string; label: string }> = {
    edital: { icon: "📄", label: "Edital" },
    matricula: { icon: "📜", label: "Matrícula" },
    debt: { icon: "💰", label: "Débitos" },
    occupancy: { icon: "🏠", label: "Ocupação" },
    manual: { icon: "🔍", label: "Verificações Manuais" },
  };

  return (
    <div className="space-y-5">
      {/* Ready to Bid badge */}
      <div
        className={`rounded-xl p-5 border-2 transition-all ${
          allRequired ? "border-green-500" : "border-gray-200"
        }`}
        style={{
          background: allRequired ? "#f0faf4" : "#fff",
        }}
      >
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-serif text-lg font-bold" style={{ color: "var(--ink)" }}>
              {allRequired ? "✅ Pronto para Dar Lance" : "⏳ Checklist Pré-Leilão"}
            </h3>
            <p className="text-sm mt-1" style={{ color: "var(--mid)" }}>
              {allRequired
                ? "Todos os itens obrigatórios foram verificados"
                : `${requiredChecked} de ${requiredItems.length} itens obrigatórios verificados`}
            </p>
          </div>
          {allRequired && (
            <div
              className="px-4 py-2 rounded-full text-sm font-bold"
              style={{ background: "#1a6b3c", color: "#fff" }}
            >
              🎯 Pode Dar Lance
            </div>
          )}
        </div>

        {/* Progress bar */}
        <div className="mt-4">
          <div className="flex justify-between text-xs mb-1" style={{ color: "var(--mid)" }}>
            <span>Progresso</span>
            <span className="font-semibold">{progress}%</span>
          </div>
          <div className="h-2 rounded-full" style={{ background: "var(--cream)" }}>
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${progress}%`,
                background: allRequired ? "#1a6b3c" : "var(--gold)",
              }}
            />
          </div>
        </div>
      </div>

      {/* Checklist items grouped by category */}
      {Object.entries(grouped).map(([cat, catItems]) => {
        if (catItems.length === 0) return null;
        const meta = categoryLabels[cat];
        return (
          <div key={cat} className="rounded-xl border overflow-hidden" style={{ borderColor: "var(--border)" }}>
            <div className="px-4 py-3 flex items-center gap-2" style={{ background: "var(--ink)", color: "var(--paper)" }}>
              <span>{meta.icon}</span>
              <span className="text-sm font-semibold">{meta.label}</span>
            </div>
            <div className="divide-y" style={{ borderColor: "var(--cream)" }}>
              {catItems.map((item) => (
                <div
                  key={item.id}
                  className="px-4 py-3 flex items-start gap-3 cursor-pointer hover:bg-gray-50 transition-colors"
                  onClick={() => toggle(item.id)}
                >
                  {/* Checkbox */}
                  <div
                    className={`mt-0.5 w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 transition-all ${
                      checked.has(item.id) ? "border-green-500" : "border-gray-300"
                    }`}
                    style={{
                      background: checked.has(item.id) ? "#1a6b3c" : "#fff",
                    }}
                  >
                    {checked.has(item.id) && (
                      <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-sm font-medium ${checked.has(item.id) ? "line-through opacity-60" : ""}`}
                        style={{ color: "var(--ink)" }}
                      >
                        {item.label}
                      </span>
                      {item.required && (
                        <span
                          className="text-xs px-1.5 py-0.5 rounded font-medium"
                          style={{ background: "#fff3e0", color: "#e65100" }}
                        >
                          Obrigatório
                        </span>
                      )}
                      {item.autoChecked && (
                        <span
                          className="text-xs px-1.5 py-0.5 rounded font-medium"
                          style={{ background: "#e3f2fd", color: "#1565c0" }}
                        >
                          IA ✓
                        </span>
                      )}
                    </div>
                    <p className="text-xs mt-0.5" style={{ color: "var(--mid)" }}>
                      {item.description}
                    </p>
                    <div className="flex items-center gap-3 mt-1.5">
                      {item.riskLevel && (
                        <span
                          className="text-xs font-medium px-2 py-0.5 rounded-full"
                          style={{ background: riskBg(item.riskLevel), color: riskColor(item.riskLevel) }}
                        >
                          {item.riskLevel === "red" ? "🔴 Risco" : item.riskLevel === "yellow" ? "🟡 Médio" : "🟢 OK"}
                        </span>
                      )}
                      {item.sourceUrl && (
                        <a
                          href={item.sourceUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs underline"
                          style={{ color: "var(--gold)" }}
                          onClick={(e) => e.stopPropagation()}
                        >
                          {item.sourceLabel || "🔗 Verificar"} →
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}

      {/* Info box */}
      <div
        className="rounded-xl p-4 text-xs leading-relaxed"
        style={{ background: "var(--cream)", border: "1px solid var(--border)", color: "var(--mid)" }}
      >
        <strong>ℹ️ Sobre este checklist:</strong> Itens marcados com "IA ✓" foram automaticamente
        verificados pela análise de inteligência artificial. Itens manuais requerem sua verificação
        diretamente nos portais oficiais. Este checklist não substitui assessoria jurídica
        profissional.
      </div>
    </div>
  );
}