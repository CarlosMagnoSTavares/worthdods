"use client";

import { OccupancySignal } from "@/types";

interface OccupancyRiskProps {
  statusOcupacao?: string;
  riscoNivel?: string;
  prazoDesocupacao?: string;
  custoEstimado?: string;
  sinais?: OccupancySignal[];
}

const NIVEL_CONFIG: Record<string, { bg: string; text: string; border: string; label: string }> = {
  BAIXO: { bg: "#f0faf4", text: "#1a6b3c", border: "#4caf82", label: "Baixo Risco" },
  MEDIO: { bg: "#fffbf0", text: "#b8860b", border: "#e5c84a", label: "Médio Risco" },
  ALTO: { bg: "#fff5f0", text: "#e65100", border: "#ffb74d", label: "Alto Risco" },
  CRITICO: { bg: "#fff5f5", text: "#c0392b", border: "#e57373", label: "Risco Crítico" },
  DESCONHECIDO: { bg: "#f5f5f5", text: "#6b6055", border: "#ccc", label: "Desconhecido" },
};

const STATUS_LABELS: Record<string, string> = {
  OCUPADO: "Ocupado",
  DESOCUPADO: "Desocupado",
  DESCONHECIDO: "Status Desconhecido",
};

export function OccupancyRisk({
  statusOcupacao,
  riscoNivel,
  prazoDesocupacao,
  custoEstimado,
  sinais,
}: OccupancyRiskProps) {
  const nivel = riscoNivel || "DESCONHECIDO";
  const config = NIVEL_CONFIG[nivel] || NIVEL_CONFIG.DESCONHECIDO;

  return (
    <div className="space-y-4">
      {/* Risk badge */}
      <div
        className="flex items-center gap-3 p-4 rounded-lg"
        style={{ background: config.bg, border: `1px solid ${config.border}` }}
      >
        <div className="flex-shrink-0">
          <div
            className="w-12 h-12 rounded-full flex items-center justify-center text-white font-bold text-lg"
            style={{ background: config.text }}
          >
            {nivel === "BAIXO" ? "✓" : nivel === "CRITICO" ? "!" : "?"}
          </div>
        </div>
        <div className="flex-1">
          <div className="font-semibold text-sm" style={{ color: config.text }}>
            {config.label}
          </div>
          {statusOcupacao && (
            <div className="text-xs mt-0.5" style={{ color: "var(--mid)" }}>
              Status: {STATUS_LABELS[statusOcupacao] || statusOcupacao}
            </div>
          )}
        </div>
      </div>

      {/* Details grid */}
      <div className="grid grid-cols-2 gap-3">
        {prazoDesocupacao && (
          <div
            className="p-3 rounded-lg border"
            style={{ borderColor: "var(--border)" }}
          >
            <div className="text-xs uppercase tracking-wider font-semibold mb-1" style={{ color: "var(--mid)" }}>
              Prazo Estimado
            </div>
            <div className="text-sm font-medium" style={{ color: "var(--ink)" }}>
              {prazoDesocupacao}
            </div>
          </div>
        )}
        {custoEstimado && (
          <div
            className="p-3 rounded-lg border"
            style={{ borderColor: "var(--border)" }}
          >
            <div className="text-xs uppercase tracking-wider font-semibold mb-1" style={{ color: "var(--mid)" }}>
              Custo Estimado
            </div>
            <div className="text-sm font-medium" style={{ color: "var(--ink)" }}>
              {custoEstimado}
            </div>
          </div>
        )}
      </div>

      {/* Signals */}
      {sinais && sinais.length > 0 && (
        <div>
          <h5 className="text-xs uppercase tracking-wider font-semibold mb-2" style={{ color: "var(--mid)" }}>
            Sinais Detectados ({sinais.length})
          </h5>
          <div className="space-y-1.5">
            {sinais.map((sinal, i) => {
              const sinalConfig = NIVEL_CONFIG[sinal.nivel] || NIVEL_CONFIG.DESCONHECIDO;
              return (
                <div
                  key={i}
                  className="flex items-center gap-2 p-2 rounded text-sm"
                  style={{ background: sinalConfig.bg, border: `1px solid ${sinalConfig.border}` }}
                >
                  <span
                    className="text-xs px-1.5 py-0.5 rounded font-medium"
                    style={{ background: sinalConfig.text, color: "#fff" }}
                  >
                    {sinal.nivel}
                  </span>
                  <span style={{ color: "var(--ink)" }}>{sinal.descricao}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* No data */}
      {(!sinais || sinais.length === 0) && !statusOcupacao && (
        <div className="text-center py-4">
          <p className="text-sm" style={{ color: "var(--mid)" }}>
            Dados de ocupação não disponíveis. Execute a análise de IA para extrair sinais de ocupação.
          </p>
        </div>
      )}
    </div>
  );
}
