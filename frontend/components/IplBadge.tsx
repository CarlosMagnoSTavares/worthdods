import { iplBgColor } from "@/lib/utils";

interface IplBadgeProps {
  score?: number;
  classificacao?: string;
  size?: "sm" | "md" | "lg";
}

export function IplBadge({ score, classificacao, size = "md" }: IplBadgeProps) {
  if (!score || !classificacao) {
    return (
      <div
        className="rounded-lg p-3 text-center"
        style={{ background: "var(--cream)", border: "1px solid var(--border)" }}
      >
        <div className="text-sm font-medium" style={{ color: "var(--mid)" }}>
          Sem score
        </div>
      </div>
    );
  }

  const bgClass = iplBgColor(classificacao);
  const sizes = {
    sm: { score: "text-lg", label: "text-xs", sub: "hidden" },
    md: { score: "text-2xl", label: "text-xs", sub: "text-xs opacity-75" },
    lg: { score: "text-4xl", label: "text-sm", sub: "text-xs opacity-75" },
  };
  const s = sizes[size];

  return (
    <div className={`${bgClass} text-white rounded-lg p-3 text-center`}>
      <div className={`${s.score} font-bold font-serif`}>{score.toFixed(1)}</div>
      <div className={`${s.label} font-semibold`}>{classificacao}</div>
      <div className={s.sub}>Score IPL</div>
    </div>
  );
}
