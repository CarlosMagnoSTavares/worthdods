"use client";

import { useState } from "react";
import { DividaItem } from "@/types";

interface DebtDetailsProps {
  dividas: DividaItem[];
}

const TIPO_LABELS: Record<string, string> = {
  IPTU: "IPTU",
  CONDOMINIO: "Condomínio",
  CONTRIBUICAO_MELHORIA: "Contribuição de Melhoria",
  PROPTER_REM: "Propter Rem",
  IPTU_TRANSFERIDO: "IPTU Transferido",
  CONDOMINIO_TRANSFERIDO: "Condomínio Transferido",
  ALUGUEL_ATRASADO: "Aluguel Atrasado",
  TAXA_LIXO: "Taxa de Lixo",
  CND_NAO_OBTIDA: "CND Não Obtida",
  HIPOTECA: "Hipoteca",
  PENHORA: "Penhora",
  OUTRO: "Outro",
};

const SEVERIDADE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  CRITICA: { bg: "#fff5f5", text: "#c0392b", border: "#e57373" },
  ALTA: { bg: "#fff8e1", text: "#e65100", border: "#ffb74d" },
  MEDIA: { bg: "#fffde7", text: "#f57f17", border: "#fff176" },
  BAIXA: { bg: "#f0faf4", text: "#1a6b3c", border: "#4caf82" },
};

const SEVERIDADE_BADGE: Record<string, string> = {
  CRITICA: "bg-red-100 text-red-700 border-red-300",
  ALTA: "bg-orange-100 text-orange-700 border-orange-300",
  MEDIA: "bg-yellow-100 text-yellow-700 border-yellow-300",
  BAIXA: "bg-green-100 text-green-700 border-green-300",
};

function formatCurrency(value?: number): string {
  if (!value) return "Não informado";
  return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function DebtDetails({ dividas }: DebtDetailsProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (!dividas || dividas.length === 0) {
    return (
      <div className="text-center py-4">
        <p className="text-sm" style={{ color: "var(--mid)" }}>
          Nenhuma dívida estruturada encontrada nesta análise.
        </p>
      </div>
    );
  }

  // Group by type
  const grouped = dividas.reduce((acc, d) => {
    const tipo = d.tipo || "OUTRO";
    if (!acc[tipo]) acc[tipo] = [];
    acc[tipo].push(d);
    return acc;
  }, {} as Record<string, DividaItem[]>);

  // Summary stats
  const transferidas = dividas.filter((d) => d.transferida_ao_comprador);
  const totalEstimado = dividas.reduce((sum, d) => sum + (d.valor_estimado || 0), 0);

  return (
    <div className="space-y-4">
      {/* Summary banner */}
      <div
        className="rounded-lg p-4"
        style={{
          background: transferidas.length > 0 ? "#fff5f5" : "#f0faf4",
          border: `1px solid ${transferidas.length > 0 ? "#e57373" : "#4caf82"}`,
        }}
      >
        <div className="flex items-center gap-2 mb-1">
          <span className="text-lg">
            {transferidas.length > 0 ? "⚠️" : "✅"}
          </span>
          <span className="font-semibold text-sm" style={{ color: "var(--ink)" }}>
            {transferidas.length > 0
              ? `${transferidas.length} débito(s) transferido(s) ao comprador`
              : "Nenhum débito transferido ao comprador"}
          </span>
        </div>
        {totalEstimado > 0 && (
          <p className="text-xs" style={{ color: "var(--mid)" }}>
            Valor total estimado: {formatCurrency(totalEstimado)}
          </p>
        )}
      </div>

      {/* Debt items grouped by type */}
      {Object.entries(grouped).map(([tipo, items]) => (
        <div key={tipo}>
          <h5 className="text-xs uppercase tracking-wider font-semibold mb-2" style={{ color: "var(--mid)" }}>
            {TIPO_LABELS[tipo] || tipo} ({items.length})
          </h5>
          <div className="space-y-2">
            {items.map((divida, i) => {
              const globalIndex = dividas.indexOf(divida);
              const isExpanded = expandedIndex === globalIndex;
              const sev = divida.severidade || "MEDIA";
              const colors = SEVERIDADE_COLORS[sev] || SEVERIDADE_COLORS.MEDIA;

              return (
                <div
                  key={i}
                  className="border rounded-lg overflow-hidden"
                  style={{ borderColor: colors.border }}
                >
                  <button
                    className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-50"
                    onClick={() => setExpandedIndex(isExpanded ? null : globalIndex)}
                  >
                    <div className="flex items-center gap-2 flex-wrap">
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full font-medium border ${SEVERIDADE_BADGE[sev] || SEVERIDADE_BADGE.MEDIA}`}
                      >
                        {sev}
                      </span>
                      {divida.transferida_ao_comprador && (
                        <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-red-100 text-red-700 border border-red-300">
                          Transferido
                        </span>
                      )}
                      <span className="text-sm font-medium" style={{ color: "var(--ink)" }}>
                        {divida.descricao?.substring(0, 60)}
                        {divida.descricao && divida.descricao.length > 60 ? "..." : ""}
                      </span>
                    </div>
                    <span style={{ color: "var(--mid)" }}>
                      {isExpanded ? "▲" : "▼"}
                    </span>
                  </button>

                  {isExpanded && (
                    <div
                      className="px-3 pb-3 text-sm space-y-2"
                      style={{ background: "var(--cream)" }}
                    >
                      <p>{divida.descricao}</p>

                      <div className="grid grid-cols-2 gap-2 text-xs">
                        {divida.valor_estimado && (
                          <div>
                            <span style={{ color: "var(--mid)" }}>Valor: </span>
                            <span className="font-medium" style={{ color: "var(--ink)" }}>
                              {formatCurrency(divida.valor_estimado)}
                            </span>
                          </div>
                        )}
                        {divida.valor_texto && (
                          <div>
                            <span style={{ color: "var(--mid)" }}>Valor (texto): </span>
                            <span className="font-medium" style={{ color: "var(--ink)" }}>
                              {divida.valor_texto}
                            </span>
                          </div>
                        )}
                        {divida.periodo && (
                          <div>
                            <span style={{ color: "var(--mid)" }}>Período: </span>
                            <span className="font-medium" style={{ color: "var(--ink)" }}>
                              {divida.periodo}
                            </span>
                          </div>
                        )}
                        {divida.responsavel && (
                          <div>
                            <span style={{ color: "var(--mid)" }}>Responsável: </span>
                            <span className="font-medium" style={{ color: "var(--ink)" }}>
                              {divida.responsavel === "COMPRADOR"
                                ? "Comprador"
                                : divida.responsavel === "VENDEDOR"
                                ? "Vendedor"
                                : divida.responsavel}
                            </span>
                          </div>
                        )}
                        {divida.base_legal && (
                          <div className="col-span-2">
                            <span style={{ color: "var(--mid)" }}>Base legal: </span>
                            <span className="font-medium" style={{ color: "var(--ink)" }}>
                              {divida.base_legal}
                            </span>
                          </div>
                        )}
                      </div>

                      {divida.clausula_documento && (
                        <blockquote
                          className="border-l-2 pl-3 text-xs italic mt-2"
                          style={{ borderColor: "var(--gold)" }}
                        >
                          {divida.clausula_documento}
                        </blockquote>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
