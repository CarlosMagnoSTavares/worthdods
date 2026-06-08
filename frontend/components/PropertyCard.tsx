import Link from "next/link";
import { Property, Analysis } from "@/types";
import { IplBadge } from "./IplBadge";
import { RiskFlags } from "./RiskFlags";
import { formatBRL, formatPercent } from "@/lib/utils";

interface PropertyCardProps {
  property: Property;
  analysis?: Analysis;
}

export function PropertyCard({ property, analysis }: PropertyCardProps) {
  const discountColor =
    (property.desconto_percentual || 0) >= 30
      ? "var(--green)"
      : (property.desconto_percentual || 0) >= 15
      ? "var(--gold)"
      : "var(--red)";

  return (
    <div
      className="rounded-xl overflow-hidden border shadow-sm hover:shadow-md transition-shadow"
      style={{ background: "#fff", borderColor: "var(--border)" }}
    >
      {/* Foto / Placeholder */}
      <div
        className="h-40 flex items-center justify-center text-4xl"
        style={{
          background: "var(--cream)",
          backgroundImage: property.fotos?.[0]
            ? `url(${property.fotos[0]})`
            : undefined,
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      >
        {!property.fotos?.[0] && "🏠"}
      </div>

      <div className="p-4">
        {/* Header: endereço + IPL */}
        <div className="flex gap-3 items-start mb-3">
          <div className="flex-1 min-w-0">
            <div className="font-semibold text-sm truncate" style={{ color: "var(--ink)" }}>
              {property.endereco}
            </div>
            <div className="text-xs mt-0.5" style={{ color: "var(--mid)" }}>
              {property.bairro ? `${property.bairro} · ` : ""}
              {property.cidade} – {property.uf}
            </div>
          </div>
          <div className="flex-shrink-0 w-16">
            <IplBadge score={property.ipl_score} classificacao={property.ipl_classificacao} size="sm" />
          </div>
        </div>

        {/* Preços */}
        <div className="flex items-end justify-between mb-3">
          <div>
            <div
              className="font-serif text-xl font-bold"
              style={{ color: "var(--ink)" }}
            >
              {formatBRL(property.preco)}
            </div>
            {property.valor_avaliacao && (
              <div className="text-xs" style={{ color: "var(--mid)" }}>
                Avaliação: {formatBRL(property.valor_avaliacao)}
              </div>
            )}
          </div>
          {property.desconto_percentual && (
            <div
              className="text-sm font-bold px-2 py-0.5 rounded"
              style={{ background: "var(--cream)", color: discountColor }}
            >
              -{formatPercent(property.desconto_percentual)}
            </div>
          )}
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-1.5 mb-3">
          {property.aceita_fgts && (
            <span
              className="text-xs px-2 py-0.5 rounded-full font-medium"
              style={{ background: "#d4edda", color: "var(--green)" }}
            >
              FGTS
            </span>
          )}
          {property.aceita_financiamento && (
            <span
              className="text-xs px-2 py-0.5 rounded-full font-medium"
              style={{ background: "#dce8f5", color: "var(--blue)" }}
            >
              Financiamento
            </span>
          )}
          {property.modalidade && (
            <span
              className="text-xs px-2 py-0.5 rounded-full"
              style={{ background: "var(--cream)", color: "var(--mid)" }}
            >
              {property.modalidade}
            </span>
          )}
        </div>

        {/* Risk flags */}
        <div className="mb-3">
          <RiskFlags analysis={analysis} compact />
        </div>

        {/* CTA */}
        <Link
          href={`/imovel/${property.id}`}
          className="block w-full text-center py-2 text-sm font-semibold rounded-lg transition-all hover:opacity-90"
          style={{ background: "var(--ink)", color: "var(--gold-light)" }}
        >
          Ver Análise Completa →
        </Link>
      </div>
    </div>
  );
}
