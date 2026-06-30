"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { IplBadge } from "@/components/IplBadge";
import { RiskFlags } from "@/components/RiskFlags";
import { AnalysisPanel } from "@/components/AnalysisPanel";
import { formatBRL, formatPercent, formatDate } from "@/lib/utils";
import { useNotifications } from "@/lib/notifications";
import { LegalReport } from "@/components/LegalReport";
import { PreBidChecklist } from "@/components/PreBidChecklist";
import type { PropertyDetail, Analysis } from "@/types";

interface PageProps {
  params: { id: string };
}

export default function ImovelPage({ params }: PageProps) {
  const { id } = params;
  const [property, setProperty] = useState<PropertyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzeMsg, setAnalyzeMsg] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"resumo" | "analise" | "juridico" | "checklist">("resumo");
  const { addNotification } = useNotifications();

  useEffect(() => {
    loadProperty();
  }, [id]);

  // Poll while analyzing — refresh property when background analysis finishes
  useEffect(() => {
    if (!isAnalyzing) return;
    if (property?.analyses && property.analyses.length > 0) return;

    const started = Date.now();
    const MAX_MS = 5 * 60 * 1000;

    const timer = setInterval(async () => {
      if (Date.now() - started > MAX_MS) {
        setIsAnalyzing(false);
        setAnalyzeMsg("Análise demorou demais. Tente novamente em alguns minutos.");
        setTimeout(() => setAnalyzeMsg(null), 6000);
        clearInterval(timer);
        return;
      }
      try {
        const data = await api.properties.get(id);
        if (data.analyses && data.analyses.length > 0) {
          setProperty(data);
          setIsAnalyzing(false);
          setActiveTab("analise");
          setAnalyzeMsg("Análise concluída ✅");
          setTimeout(() => setAnalyzeMsg(null), 4000);
          clearInterval(timer);
        }
      } catch {}
    }, 6000);

    return () => clearInterval(timer);
  }, [isAnalyzing, id, property?.analyses?.length]);

  async function loadProperty() {
    setLoading(true);
    try {
      const data = await api.properties.get(id);
      setProperty(data);
      // Switch to analise tab automatically if analyses exist
      if (data.analyses && data.analyses.length > 0) {
        setActiveTab("analise");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar imóvel");
    } finally {
      setLoading(false);
    }
  }

  async function handleAnalyze() {
    if (!property || isAnalyzing) return;

    // Already have analysis → just switch to tab (re-use)
    if (property.analyses && property.analyses.length > 0) {
      setActiveTab("analise");
      setAnalyzeMsg("Análise já disponível — exibindo resultados salvos.");
      setTimeout(() => setAnalyzeMsg(null), 4000);
      return;
    }

    setIsAnalyzing(true);
    setAnalyzeMsg(null);

    try {
      const result = await api.properties.analyze(id) as {
        status: string;
        analyses?: Analysis[];
        message?: string;
      };

      if (result.status === "cached" && result.analyses && result.analyses.length > 0) {
        // Server has cached analysis — inject directly, no need to re-fetch
        setProperty((prev) =>
          prev ? { ...prev, analyses: result.analyses! } : prev
        );
        setActiveTab("analise");
        setAnalyzeMsg("Análise já disponível — carregada do cache.");
        setTimeout(() => setAnalyzeMsg(null), 4000);
        setIsAnalyzing(false);
      } else {
        // Processing in background — register notification + start page polling
        addNotification({
          propertyId: id,
          propertyAddress: property.endereco,
          cidade: `${property.cidade} – ${property.uf}`,
          status: "processing",
        });
        setActiveTab("analise");
        setAnalyzeMsg("Analisando documentos... isto pode levar 1–3 minutos.");
        // Keep isAnalyzing true — the polling effect will flip it when result arrives
      }
    } catch {
      setAnalyzeMsg("Erro ao solicitar análise. Tente novamente.");
      setTimeout(() => setAnalyzeMsg(null), 5000);
      setIsAnalyzing(false);
    }
  }

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="h-8 w-48 rounded animate-pulse mb-4" style={{ background: "var(--cream)" }} />
        <div className="grid md:grid-cols-3 gap-6">
          <div className="md:col-span-2 h-96 rounded-xl animate-pulse" style={{ background: "var(--cream)" }} />
          <div className="h-64 rounded-xl animate-pulse" style={{ background: "var(--cream)" }} />
        </div>
      </div>
    );
  }

  if (error || !property) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8 text-center">
        <p className="text-xl font-semibold" style={{ color: "var(--red)" }}>
          {error || "Imóvel não encontrado"}
        </p>
        <Link href="/dashboard" className="mt-4 inline-block text-sm underline" style={{ color: "var(--gold)" }}>
          ← Voltar ao Dashboard
        </Link>
      </div>
    );
  }

  const editalAnalysis = property.analyses?.find((a: Analysis) => a.tipo === "edital");
  const matriculaAnalysis = property.analyses?.find((a: Analysis) => a.tipo === "matricula");
  const bestAnalysis = editalAnalysis || matriculaAnalysis;

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      {/* Breadcrumb */}
      <nav className="mb-5 text-sm" style={{ color: "var(--mid)" }}>
        <Link href="/dashboard" className="hover:underline" style={{ color: "var(--gold)" }}>
          Dashboard
        </Link>
        {" / "}
        <span>{property.cidade} – {property.uf}</span>
      </nav>

      {/* Mensagem de feedback */}
      {analyzeMsg && (
        <div
          className="mb-4 px-4 py-3 rounded-lg text-sm font-medium flex items-center gap-2 border"
          style={{
            background: analyzeMsg.includes("Erro") ? "#fff5f5" : "#f0faf4",
            borderColor: analyzeMsg.includes("Erro") ? "#e57373" : "#4caf82",
            color: analyzeMsg.includes("Erro") ? "var(--red)" : "#1a6b3c",
          }}
        >
          {analyzeMsg.includes("Erro") ? "⚠️" : "ℹ️"} {analyzeMsg}
        </div>
      )}

      {/* Header do imóvel */}
      <div
        className="rounded-xl p-6 mb-6 relative overflow-hidden"
        style={{ background: "var(--ink)", color: "var(--paper)" }}
      >
        <div
          className="absolute inset-0 opacity-50"
          style={{
            background:
              "repeating-linear-gradient(45deg, transparent, transparent 40px, rgba(184,134,11,0.04) 40px, rgba(184,134,11,0.04) 80px)",
          }}
        />
        <div className="relative z-10">
          <div
            className="inline-flex items-center gap-2 text-xs font-semibold tracking-widest uppercase px-3 py-1 rounded mb-4"
            style={{ background: "var(--gold)", color: "#fff" }}
          >
            📋 Imóvel Caixa Econômica Federal
          </div>
          <h1 className="font-serif text-2xl md:text-3xl mb-1" style={{ color: "var(--paper)" }}>
            {property.endereco}
          </h1>
          <p style={{ color: "#a09888" }}>
            {property.bairro ? `${property.bairro} · ` : ""}{property.cidade} – {property.uf}
          </p>
          <div className="flex flex-wrap gap-5 mt-5">
            {[
              { label: "Nº do Imóvel", value: property.imovel_numero },
              { label: "Tipo", value: property.tipo_imovel || "Imóvel" },
              { label: "Área", value: property.area_m2 ? `${property.area_m2} m²` : "—" },
              { label: "Quartos", value: property.quartos ? String(property.quartos) : "—" },
              { label: "Modalidade", value: property.modalidade || "—" },
            ].map((m) => (
              <div key={m.label}>
                <div className="text-xs uppercase tracking-wider" style={{ color: "#a09888" }}>{m.label}</div>
                <div className="text-sm font-semibold mt-0.5">{m.value}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="gold-divider mb-6" />

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Coluna principal (2/3) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Tabs */}
          <div className="flex border-b" style={{ borderColor: "var(--border)" }}>
            {(["resumo", "analise", "juridico", "checklist"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex-1 py-3 text-sm font-semibold transition-all ${activeTab === tab ? "border-b-2" : ""}`}
                style={{
                  borderColor: activeTab === tab ? "var(--gold)" : "transparent",
                  color: activeTab === tab ? "var(--gold)" : "var(--mid)",
                }}
              >
                {tab === "resumo" ? "📊 Resumo" : tab === "analise" ? "🤖 Análise IA" : tab === "juridico" ? "⚖️ Jurídico" : "✅ Checklist"}
                {tab === "analise" && property.analyses?.length > 0 && (
                  <span
                    className="ml-1.5 text-xs px-1.5 py-0.5 rounded-full"
                    style={{ background: "var(--gold-pale)", color: "var(--gold)" }}
                  >
                    ✓
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Tab: Resumo */}
          {activeTab === "resumo" && (
            <div className="space-y-5">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {[
                  {
                    label: "Valor de Avaliação",
                    value: property.valor_avaliacao ? formatBRL(property.valor_avaliacao) : "—",
                    color: "var(--gold)",
                    accent: "#b8860b",
                  },
                  {
                    label: "Preço Mínimo",
                    value: formatBRL(property.preco),
                    color: "var(--red)",
                    accent: "#c0392b",
                    badge: property.desconto_percentual
                      ? `-${formatPercent(property.desconto_percentual)}`
                      : undefined,
                  },
                  {
                    label: "Spread Bruto",
                    value: property.valor_avaliacao
                      ? formatBRL(property.valor_avaliacao - property.preco)
                      : "—",
                    color: "var(--green)",
                    accent: "#1a6b3c",
                  },
                ].map((c) => (
                  <div
                    key={c.label}
                    className="rounded-xl p-4 border relative"
                    style={{ background: "#fff", borderColor: "var(--border)", borderTop: `4px solid ${c.accent}` }}
                  >
                    <div className="text-xs uppercase tracking-wider mb-1" style={{ color: "var(--mid)" }}>
                      {c.label}
                    </div>
                    <div className="font-serif text-xl font-bold" style={{ color: c.color }}>
                      {c.value}
                    </div>
                    {c.badge && (
                      <span
                        className="absolute top-3 right-3 text-xs font-bold px-2 py-0.5 rounded-full"
                        style={{ background: "#fde8e8", color: "var(--red)" }}
                      >
                        {c.badge}
                      </span>
                    )}
                  </div>
                ))}
              </div>

              <div className="rounded-xl overflow-hidden border" style={{ borderColor: "var(--border)" }}>
                <div className="px-4 py-3 text-sm font-semibold" style={{ background: "var(--ink)", color: "var(--paper)" }}>
                  Ficha Técnica
                </div>
                <table className="w-full">
                  <tbody>
                    {[
                      ["Endereço", property.endereco],
                      ["Bairro / Cidade", `${property.bairro || "—"} · ${property.cidade} – ${property.uf}`],
                      ["Nº do Imóvel", property.imovel_numero],
                      ["Área", property.area_m2 ? `${property.area_m2} m²` : "—"],
                      ["Quartos", property.quartos ? String(property.quartos) : "—"],
                      ["Modalidade", property.modalidade || "—"],
                      ["Ocupação", property.status_ocupacao || "Não informado"],
                      ["Data do Leilão", property.data_leilao ? formatDate(property.data_leilao) : "Verificar edital"],
                      ["Aceita FGTS", property.aceita_fgts ? "Sim" : "Não"],
                      ["Aceita Financiamento", property.aceita_financiamento ? "Sim" : "Não"],
                    ].map(([label, value]) => (
                      <tr key={label} className="border-b last:border-b-0" style={{ borderColor: "var(--cream)" }}>
                        <td
                          className="px-4 py-2.5 text-xs uppercase tracking-wider w-2/5"
                          style={{ background: "var(--cream)", color: "var(--mid)" }}
                        >
                          {label}
                        </td>
                        <td className="px-4 py-2.5 text-sm font-medium" style={{ color: "var(--ink)" }}>
                          {value}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {property.descricao && (
                <div
                  className="rounded-xl p-4 border text-sm"
                  style={{ background: "#fff", borderColor: "var(--border)", color: "var(--mid)" }}
                >
                  <div className="text-xs uppercase tracking-wider font-semibold mb-2" style={{ color: "var(--mid)" }}>
                    Descrição
                  </div>
                  {property.descricao}
                </div>
              )}
            </div>
          )}

          {/* Tab: Análise IA */}
          {activeTab === "analise" && (
            <AnalysisPanel
              analyses={property.analyses || []}
              onAnalyze={handleAnalyze}
              isAnalyzing={isAnalyzing}
            />
          )}

          {/* Tab: Jurídico */}
          {activeTab === "juridico" && (
            <LegalReport
              legalChecks={property.legal_checks || []}
              legalSummary={property.legal_summary}
              analyses={property.analyses || []}
              onAnalyze={handleAnalyze}
              isAnalyzing={isAnalyzing}
              urlMatricula={property.url_matricula}
              urlEdital={property.url_edital}
              linkAcesso={property.link_acesso}
            />
          )}

          {/* Tab: Checklist */}
          {activeTab === "checklist" && (
            <PreBidChecklist
              property={property}
              analysis={property.analyses?.[0]}
            />
          )}
        </div>

        {/* Coluna lateral (1/3) */}
        <div className="space-y-4">
          <div className="rounded-xl border p-5" style={{ background: "#fff", borderColor: "var(--border)" }}>
            <div className="text-xs uppercase tracking-wider font-semibold mb-3" style={{ color: "var(--mid)" }}>
              Score de Arrematação
            </div>
            <IplBadge score={property.ipl_score} classificacao={property.ipl_classificacao} size="lg" />
            {property.ipl_score_margem !== undefined && (
              <div className="mt-3 space-y-1.5 text-xs" style={{ color: "var(--mid)" }}>
                <div className="flex justify-between">
                  <span>Score Margem (60%)</span>
                  <span className="font-semibold">{property.ipl_score_margem?.toFixed(1)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Score Risco (30%)</span>
                  <span className="font-semibold">{property.ipl_score_risco?.toFixed(1) || "5.0"}</span>
                </div>
                <div className="flex justify-between">
                  <span>Score Oport. (10%)</span>
                  <span className="font-semibold">5.0</span>
                </div>
              </div>
            )}
          </div>

          <div className="rounded-xl border p-5" style={{ background: "#fff", borderColor: "var(--border)" }}>
            <div className="text-xs uppercase tracking-wider font-semibold mb-3" style={{ color: "var(--mid)" }}>
              Flags de Risco
            </div>
            <RiskFlags analysis={bestAnalysis} />
          </div>

          <div className="rounded-xl border p-5 space-y-3" style={{ background: "#fff", borderColor: "var(--border)" }}>
            <div className="text-xs uppercase tracking-wider font-semibold" style={{ color: "var(--mid)" }}>
              Valores
            </div>
            {[
              { label: "Preço Mínimo", value: formatBRL(property.preco), color: "var(--red)" },
              {
                label: "Avaliação Caixa",
                value: property.valor_avaliacao ? formatBRL(property.valor_avaliacao) : "—",
                color: "var(--gold)",
              },
              {
                label: "Desconto",
                value: property.desconto_percentual ? formatPercent(property.desconto_percentual) : "—",
                color: "var(--green)",
              },
            ].map((v) => (
              <div key={v.label} className="flex justify-between items-center">
                <span className="text-xs" style={{ color: "var(--mid)" }}>{v.label}</span>
                <span className="font-serif text-base font-bold" style={{ color: v.color }}>{v.value}</span>
              </div>
            ))}
          </div>

          {/* Ações */}
          <div className="space-y-2">
            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              className="w-full py-3 text-sm font-semibold rounded-lg transition-all hover:opacity-90 disabled:opacity-50 flex items-center justify-center gap-2"
              style={{ background: "var(--gold)", color: "#fff" }}
            >
              {isAnalyzing ? (
                <>⏳ Enviando análise…</>
              ) : property.analyses?.length > 0 ? (
                <>📊 Ver Análise IA</>
              ) : (
                <>🔍 Analisar com IA</>
              )}
            </button>

            {property.link_acesso && (
              <a
                href={property.link_acesso}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 w-full py-3 text-sm font-semibold rounded-lg border hover:bg-gray-50"
                style={{ borderColor: "var(--border)", color: "var(--ink)" }}
              >
                🏦 Ver na Caixa
              </a>
            )}

            <a
              href={`https://www.google.com/maps/search/${encodeURIComponent(
                `${property.endereco}, ${property.cidade}, ${property.uf}, Brasil`
              )}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 w-full py-3 text-sm font-semibold rounded-lg border hover:bg-gray-50"
              style={{ borderColor: "var(--border)", color: "var(--blue)" }}
            >
              🗺️ Ver no Google Maps
            </a>
          </div>

          <div
            className="rounded-xl p-4 text-xs leading-relaxed"
            style={{ background: "var(--cream)", border: "1px solid var(--border)", color: "var(--mid)" }}
          >
            <strong>⚠ Atenção:</strong> Este relatório é informativo baseado em dados públicos.
            Não constitui assessoria jurídica ou financeira. Consulte um profissional antes de arrematar.
          </div>
        </div>
      </div>
    </div>
  );
}
