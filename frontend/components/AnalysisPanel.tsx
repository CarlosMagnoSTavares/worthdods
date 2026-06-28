"use client";

import { useState } from "react";
import { Analysis } from "@/types";
import { RiskFlags } from "./RiskFlags";
import { DebtDetails } from "./DebtDetails";
import { OccupancyRisk } from "./OccupancyRisk";
import { severidadeBadge } from "@/lib/utils";

interface AnalysisPanelProps {
  analyses: Analysis[];
  onAnalyze: () => void;
  isAnalyzing: boolean;
}

export function AnalysisPanel({ analyses, onAnalyze, isAnalyzing }: AnalysisPanelProps) {
  const [activeTab, setActiveTab] = useState<"matricula" | "edital" | "dividas">("edital");
  const [openRisk, setOpenRisk] = useState<number | null>(null);

  const analysis = analyses.find((a) => a.tipo === activeTab);
  const debtAnalysis = analyses.find((a) => a.tipo === "dividas");
  const hasAny = analyses.length > 0;

  return (
    <div
      className="rounded-xl border"
      style={{ background: "#fff", borderColor: "var(--border)" }}
    >
      {/* Tabs */}
      <div
        className="flex border-b"
        style={{ borderColor: "var(--border)" }}
      >
        {(["edital", "matricula", "dividas"] as const).map((tab) => {
          const has = tab === "dividas" ? !!debtAnalysis : analyses.some((a) => a.tipo === tab);
          return (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-3 text-sm font-semibold capitalize transition-all ${
                activeTab === tab ? "border-b-2" : ""
              }`}
              style={{
                borderColor: activeTab === tab ? "var(--gold)" : "transparent",
                color: activeTab === tab ? "var(--gold)" : "var(--mid)",
              }}
            >
              {tab === "edital" ? "📋 Edital" : tab === "matricula" ? "📄 Matrícula" : "💰 Débitos"}
              {has && (
                <span
                  className="ml-1.5 text-xs px-1.5 py-0.5 rounded-full"
                  style={{ background: "var(--gold-pale)", color: "var(--gold)" }}
                >
                  IA ✓
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div className="p-5">
        {!hasAny ? (
          /* Sem análise */
          <div className="text-center py-8">
            <div className="text-4xl mb-3">🔍</div>
            <h3
              className="font-serif text-lg mb-2"
              style={{ color: "var(--ink)" }}
            >
              Análise IA disponível
            </h3>
            <p className="text-sm mb-5" style={{ color: "var(--mid)" }}>
              Nossa IA analisa a matrícula e o edital e extrai os riscos
              jurídicos automaticamente.
            </p>
            <button
              onClick={onAnalyze}
              disabled={isAnalyzing}
              className="px-6 py-3 text-sm font-semibold rounded-lg transition-all hover:opacity-90 disabled:opacity-50"
              style={{ background: "var(--gold)", color: "#fff" }}
            >
              {isAnalyzing ? "⏳ Analisando..." : "🔍 Analisar Agora"}
            </button>
            <p className="text-xs mt-3" style={{ color: "var(--mid)" }}>
              Pode levar 1–3 minutos. Os resultados ficam salvos.
            </p>
          </div>
        ) : !analysis ? (
          /* Aba sem análise */
          <div className="text-center py-6">
            <p className="text-sm" style={{ color: "var(--mid)" }}>
              {activeTab === "edital"
                ? "Análise do edital não disponível."
                : activeTab === "matricula"
                ? "Análise da matrícula não disponível."
                : "Análise de débitos não disponível."}
            </p>
            <button
              onClick={onAnalyze}
              disabled={isAnalyzing}
              className="mt-4 px-5 py-2 text-sm font-semibold rounded-lg"
              style={{ background: "var(--gold)", color: "#fff" }}
            >
              {isAnalyzing ? "Analisando..." : "Solicitar Análise"}
            </button>
          </div>
        ) : analysis.erro_analise ? (
          /* Erro */
          <div
            className="rounded-lg p-4"
            style={{ background: "#fff5f5", border: "1px solid #e57373" }}
          >
            <p className="text-sm font-semibold" style={{ color: "var(--red)" }}>
              Erro na análise
            </p>
            <p className="text-xs mt-1" style={{ color: "var(--mid)" }}>
              {analysis.erro_analise}
            </p>
          </div>
        ) : activeTab === "dividas" && debtAnalysis ? (
          /* Análise de débitos */
          <div className="space-y-5">
            {/* Alerta de débitos */}
            {debtAnalysis.alerta_comprador && (
              <div
                className="rounded-lg p-4"
                style={{ background: "#fff8e1", border: "1px solid #ffb74d" }}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg">⚠️</span>
                  <span className="font-semibold text-sm" style={{ color: "var(--ink)" }}>
                    Alerta para o Comprador
                  </span>
                </div>
                <p className="text-sm" style={{ color: "var(--ink)" }}>
                  {debtAnalysis.alerta_comprador}
                </p>
              </div>
            )}

            {/* Resumo de débitos */}
            {debtAnalysis.resumo_dividas && (
              <div>
                <h4 className="text-xs uppercase tracking-wider font-semibold mb-2" style={{ color: "var(--mid)" }}>
                  Resumo dos Débitos
                </h4>
                <p className="text-sm leading-relaxed" style={{ color: "var(--ink)" }}>
                  {debtAnalysis.resumo_dividas}
                </p>
              </div>
            )}

            {/* Estatísticas de débitos */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="rounded-lg p-3 border" style={{ background: "#fff", borderColor: "var(--border)" }}>
                <div className="text-xs uppercase tracking-wider" style={{ color: "var(--mid)" }}>Total Débitos</div>
                <div className="font-serif text-lg font-bold" style={{ color: "var(--ink)" }}>
                  {debtAnalysis.dividas?.length || 0}
                </div>
              </div>
              <div className="rounded-lg p-3 border" style={{ background: "#fff", borderColor: "var(--border)" }}>
                <div className="text-xs uppercase tracking-wider" style={{ color: "var(--mid)" }}>Transferidos</div>
                <div className="font-serif text-lg font-bold" style={{ color: "var(--red)" }}>
                  {debtAnalysis.total_dividas_transferidas || 0}
                </div>
              </div>
              <div className="rounded-lg p-3 border" style={{ background: "#fff", borderColor: "var(--border)" }}>
                <div className="text-xs uppercase tracking-wider" style={{ color: "var(--mid)" }}>Valor Total</div>
                <div className="font-serif text-lg font-bold" style={{ color: "var(--gold)" }}>
                  {debtAnalysis.valor_total_transferido
                    ? `R$ ${debtAnalysis.valor_total_transferido.toLocaleString("pt-BR")}`
                    : "—"}
                </div>
              </div>
              <div className="rounded-lg p-3 border" style={{ background: "#fff", borderColor: "var(--border)" }}>
                <div className="text-xs uppercase tracking-wider" style={{ color: "var(--mid)" }}>Score Risco</div>
                <div className="font-serif text-lg font-bold" style={{ color: debtAnalysis.risco_dividas_score ? "var(--red)" : "var(--green)" }}>
                  {debtAnalysis.risco_dividas_score?.toFixed(1) || "0.0"}
                </div>
              </div>
            </div>

            {/* Flags de débitos */}
            <div className="flex flex-wrap gap-2">
              {debtAnalysis.tem_iptu_pendente && (
                <span className="px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700 border border-red-300">
                  IPTU Pendente
                </span>
              )}
              {debtAnalysis.tem_condominio_pendente && (
                <span className="px-3 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-700 border border-orange-300">
                  Condomínio Pendente
                </span>
              )}
              {debtAnalysis.tem_contribuicao_melhoria && (
                <span className="px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700 border border-yellow-300">
                  Contribuição de Melhoria
                </span>
              )}
              {debtAnalysis.tem_propter_rem && (
                <span className="px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-700 border border-purple-300">
                  Propter Rem
                </span>
              )}
            </div>

            {/* Lista de débitos */}
            {debtAnalysis.dividas && debtAnalysis.dividas.length > 0 && (
              <div>
                <h4 className="text-xs uppercase tracking-wider font-semibold mb-2" style={{ color: "var(--mid)" }}>
                  Débitos e Encumbrâncias ({debtAnalysis.dividas.length})
                </h4>
                <DebtDetails dividas={debtAnalysis.dividas} />
              </div>
            )}

            {/* Footer */}
            <div
              className="text-xs pt-3 border-t"
              style={{ color: "var(--mid)", borderColor: "var(--border)" }}
            >
              Analisado por {debtAnalysis.modelo_ia} ·{" "}
              {debtAnalysis.created_at && new Date(debtAnalysis.created_at).toLocaleDateString("pt-BR")}
            </div>
          </div>
        ) : (
          /* Análise disponível */
          <div className="space-y-5">
            {/* Recomendação */}
            {analysis.recomendacao && (
              <div
                className="flex items-center gap-3 p-4 rounded-lg"
                style={
                  analysis.recomendacao === "COMPRAR"
                    ? { background: "#f0faf4", border: "1px solid #4caf82" }
                    : analysis.recomendacao === "EVITAR"
                    ? { background: "#fff5f5", border: "1px solid #e57373" }
                    : { background: "#fffbf0", border: "1px solid #e5c84a" }
                }
              >
                <span className="text-2xl">
                  {analysis.recomendacao === "COMPRAR"
                    ? "✅"
                    : analysis.recomendacao === "EVITAR"
                    ? "🚨"
                    : "⚠️"}
                </span>
                <div>
                  <div className="font-semibold text-sm">
                    {analysis.recomendacao === "COMPRAR"
                      ? "Compra Recomendada"
                      : analysis.recomendacao === "EVITAR"
                      ? "Evitar — Alto Risco"
                      : "Analisar com Cuidado"}
                  </div>
                  <div className="text-xs mt-0.5" style={{ color: "var(--mid)" }}>
                    Nível de risco: {analysis.nivel_risco}
                  </div>
                </div>
              </div>
            )}

            {/* Resumo executivo */}
            {analysis.resumo_executivo && (
              <div>
                <h4 className="text-xs uppercase tracking-wider font-semibold mb-2" style={{ color: "var(--mid)" }}>
                  Resumo Executivo
                </h4>
                <p className="text-sm leading-relaxed" style={{ color: "var(--ink)" }}>
                  {analysis.resumo_executivo}
                </p>
              </div>
            )}

            {/* Flags de risco */}
            <div>
              <h4 className="text-xs uppercase tracking-wider font-semibold mb-2" style={{ color: "var(--mid)" }}>
                Flags de Risco
              </h4>
              <RiskFlags analysis={analysis} />
            </div>

            {/* Débitos detalhados */}
            {analysis.dividas && analysis.dividas.length > 0 && (
              <div>
                <h4 className="text-xs uppercase tracking-wider font-semibold mb-2" style={{ color: "var(--mid)" }}>
                  Débitos e Encumbrâncias ({analysis.dividas.length})
                </h4>
                <DebtDetails dividas={analysis.dividas} />
              </div>
            )}

            {/* Risco de ocupação */}
            {analysis.tipo === "edital" && (
              <div>
                <h4 className="text-xs uppercase tracking-wider font-semibold mb-2" style={{ color: "var(--mid)" }}>
                  Risco de Ocupação
                </h4>
                <OccupancyRisk
                  statusOcupacao={analysis.status_ocupacao}
                  riscoNivel={analysis.ocupacao_risco_nivel}
                  prazoDesocupacao={analysis.ocupacao_prazo_desocupacao}
                  custoEstimado={analysis.ocupacao_custo_estimado}
                  sinais={analysis.ocupacao_sinais}
                />
              </div>
            )}

            {/* Alerta de débitos (se disponível) */}
            {analysis.alerta_comprador && (
              <div
                className="rounded-lg p-4"
                style={{ background: "#fff8e1", border: "1px solid #ffb74d" }}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg">⚠️</span>
                  <span className="font-semibold text-sm" style={{ color: "var(--ink)" }}>
                    Alerta para o Comprador
                  </span>
                </div>
                <p className="text-sm" style={{ color: "var(--ink)" }}>
                  {analysis.alerta_comprador}
                </p>
              </div>
            )}

            {/* Resumo de débitos (se disponível) */}
            {analysis.resumo_dividas && (
              <div>
                <h4 className="text-xs uppercase tracking-wider font-semibold mb-2" style={{ color: "var(--mid)" }}>
                  Resumo dos Débitos
                </h4>
                <p className="text-sm leading-relaxed" style={{ color: "var(--ink)" }}>
                  {analysis.resumo_dividas}
                </p>
              </div>
            )}

            {/* Riscos detalhados */}
            {analysis.riscos_detalhados?.length > 0 && (
              <div>
                <h4 className="text-xs uppercase tracking-wider font-semibold mb-2" style={{ color: "var(--mid)" }}>
                  Riscos Identificados ({analysis.riscos_detalhados.length})
                </h4>
                <div className="space-y-2">
                  {analysis.riscos_detalhados.map((risco, i) => (
                    <div
                      key={i}
                      className="border rounded-lg overflow-hidden"
                      style={{ borderColor: "var(--border)" }}
                    >
                      <button
                        className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-50"
                        onClick={() => setOpenRisk(openRisk === i ? null : i)}
                      >
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-xs px-2 py-0.5 rounded-full font-medium ${severidadeBadge(risco.severidade)}`}
                          >
                            {risco.severidade}
                          </span>
                          <span className="text-sm font-medium" style={{ color: "var(--ink)" }}>
                            {risco.tipo}
                          </span>
                        </div>
                        <span style={{ color: "var(--mid)" }}>{openRisk === i ? "▲" : "▼"}</span>
                      </button>
                      {openRisk === i && (
                        <div
                          className="px-3 pb-3 text-sm"
                          style={{ color: "var(--mid)", background: "var(--cream)" }}
                        >
                          <p className="mb-1">{risco.descricao}</p>
                          {risco.clausula && (
                            <blockquote
                              className="border-l-2 pl-3 text-xs italic mt-2"
                              style={{ borderColor: "var(--gold)" }}
                            >
                              {risco.clausula}
                            </blockquote>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Pontos positivos */}
            {analysis.pontos_positivos?.length > 0 && (
              <div>
                <h4 className="text-xs uppercase tracking-wider font-semibold mb-2" style={{ color: "var(--mid)" }}>
                  Pontos Positivos
                </h4>
                <ul className="space-y-1.5">
                  {analysis.pontos_positivos.map((p, i) => (
                    <li key={i} className="text-sm flex gap-2">
                      <span style={{ color: "var(--green)" }}>✓</span>
                      <span style={{ color: "var(--ink)" }}>{p}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Footer */}
            <div
              className="text-xs pt-3 border-t"
              style={{ color: "var(--mid)", borderColor: "var(--border)" }}
            >
              Analisado por {analysis.modelo_ia} ·{" "}
              {analysis.created_at && new Date(analysis.created_at).toLocaleDateString("pt-BR")}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
