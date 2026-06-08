import { Analysis } from "@/types";

interface RiskFlagsProps {
  analysis?: Analysis;
  compact?: boolean;
}

const flags = [
  { key: "risco_evicao", label: "Evicção", good: false },
  { key: "risco_divida_iptu", label: "IPTU", good: false },
  { key: "risco_divida_condominio", label: "Condomínio", good: false },
  { key: "risco_ocupacao", label: "Ocupado", good: false },
  { key: "risco_processo_judicial", label: "Processos", good: false },
  { key: "risco_irregularidade", label: "Irregular", good: false },
  { key: "risco_ambiental", label: "Ambiental", good: false },
] as const;

export function RiskFlags({ analysis, compact = false }: RiskFlagsProps) {
  if (!analysis) {
    return (
      <div className="flex flex-wrap gap-1.5">
        <span
          className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium"
          style={{ background: "var(--cream)", color: "var(--mid)" }}
        >
          🔵 Análise pendente
        </span>
      </div>
    );
  }

  return (
    <div className="flex flex-wrap gap-1.5">
      {flags.map(({ key, label }) => {
        const hasRisk = analysis[key as keyof Analysis] as boolean;
        return (
          <span
            key={key}
            className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium"
            style={
              hasRisk
                ? { background: "#fde8e8", color: "#c0392b" }
                : { background: "#d4edda", color: "#1a6b3c" }
            }
          >
            {hasRisk ? "🔴" : "🟢"} {label}
          </span>
        );
      })}
    </div>
  );
}
