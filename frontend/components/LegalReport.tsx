"use client";

import { useState } from "react";
import type { LegalCheck, LegalSummary, Analysis } from "@/types";
import { severidadeBadge } from "@/lib/utils";
import { formatDate } from "@/lib/utils";

const TIPO_RISCO_LABEL: Record<string, string> = {
  EVICAO: "Evicção",
  DIVIDA_CONDOMINIO: "Dívida Condominial",
  DIVIDA_IPTU: "IPTU / Dívida Ativa",
  PENHORA: "Penhora",
  HIPOTECA: "Hipoteca",
  ALIENACAO_FIDUCIARIA: "Alienação Fiduciária",
  PROCESSO_JUDICIAL: "Processo Judicial",
};

const TIPO_RISCO_ICON: Record<string, string> = {
  EVICAO: "⛔",
  DIVIDA_CONDOMINIO: "🏢",
  DIVIDA_IPTU: "🏛️",
  PENHORA: "🔒",
  HIPOTECA: "🏦",
  ALIENACAO_FIDUCIARIA: "📋",
  PROCESSO_JUDICIAL: "⚖️",
};

const SEVERIDADE_COLOR: Record<string, { bg: string; text: string; border: string }> = {
  CRITICA: { bg: "#fff0f0", text: "#c0392b", border: "#e57373" },
  ALTA:    { bg: "#fff5ed", text: "#c0642b", border: "#e59a73" },
  MEDIA:   { bg: "#fffbf0", text: "#b8860b", border: "#e5c84a" },
  BAIXA:   { bg: "#f0f9f4", text: "#1a6b3c", border: "#4caf82" },
};

function ScoreGauge({ score }: { score: number }) {
  const color = score >= 7 ? "#1a6b3c" : score >= 4 ? "#b8860b" : "#c0392b";
  const label = score >= 7 ? "Baixo Risco" : score >= 4 ? "Risco Moderado" : "Alto Risco";
  return (
    <div className="flex items-center gap-4">
      <div
        className="w-16 h-16 rounded-full flex items-center justify-center font-serif text-2xl font-bold border-4"
        style={{ borderColor: color, color, background: "#fff" }}
      >
        {score.toFixed(0)}
      </div>
      <div>
        <div className="font-semibold text-sm" style={{ color }}>
          {label}
        </div>
        <div className="text-xs" style={{ color: "var(--mid)" }}>
          Score Jurídico (0–10)
        </div>
      </div>
    </div>
  );
}

interface RiskCategoryRowProps {
  icon: string;
  label: string;
  active: boolean;
  severidade?: string;
}

function RiskCategoryRow({ icon, label, active, severidade }: RiskCategoryRowProps) {
  const sev = severidade || (active ? "ALTA" : "BAIXA");
  const style = active ? SEVERIDADE_COLOR[sev] || SEVERIDADE_COLOR.ALTA : undefined;
  return (
    <div
      className="flex items-center justify-between px-3 py-2 rounded-lg border text-sm"
      style={
        active
          ? { background: style!.bg, borderColor: style!.border }
          : { background: "var(--cream)", borderColor: "var(--border)" }
      }
    >
      <span style={{ color: active ? style!.text : "var(--mid)" }}>
        {icon} {label}
      </span>
      <span
        className="text-xs font-semibold px-2 py-0.5 rounded-full"
        style={
          active
            ? { background: style!.text, color: "#fff" }
            : { background: "#e0e0e0", color: "var(--mid)" }
        }
      >
        {active ? (sev === "CRITICA" ? "CRÍTICO" : sev) : "OK"}
      </span>
    </div>
  );
}

interface LegalReportProps {
  legalChecks: LegalCheck[];
  legalSummary?: LegalSummary;
  analyses: Analysis[];
  onAnalyze: () => void;
  isAnalyzing: boolean;
  urlMatricula?: string;
  urlEdital?: string;
  linkAcesso?: string;
}

export function LegalReport({
  legalChecks,
  legalSummary,
  analyses,
  onAnalyze,
  isAnalyzing,
  urlMatricula,
  urlEdital,
  linkAcesso,
}: LegalReportProps) {
  const [openProcess, setOpenProcess] = useState<string | null>(null);

  const hasAnyData = legalChecks.length > 0 || analyses.length > 0;
  const editalAnalysis = analyses.find((a) => a.tipo === "edital");
  const matriculaAnalysis = analyses.find((a) => a.tipo === "matricula");

  // Risk flags from all analyses
  const risco_evicao =
    editalAnalysis?.risco_evicao || matriculaAnalysis?.risco_evicao || false;
  const risco_iptu = editalAnalysis?.risco_divida_iptu || false;
  const risco_condominio = editalAnalysis?.risco_divida_condominio || false;
  const risco_ocupacao = editalAnalysis?.risco_ocupacao || false;
  const risco_processo = editalAnalysis?.risco_processo_judicial || false;
  const risco_irregularidade = editalAnalysis?.risco_irregularidade || false;
  const risco_ambiental = editalAnalysis?.risco_ambiental || false;

  // Worst severidade in legal_checks
  const sevPriority = { CRITICA: 4, ALTA: 3, MEDIA: 2, BAIXA: 1 };
  const worstSev = legalChecks.reduce<string | undefined>((acc, c) => {
    if (!c.severidade) return acc;
    if (!acc) return c.severidade;
    return (sevPriority[c.severidade as keyof typeof sevPriority] || 0) >
      (sevPriority[acc as keyof typeof sevPriority] || 0)
      ? c.severidade
      : acc;
  }, undefined);

  const summary = legalSummary || {
    total_processos: legalChecks.length,
    tem_risco_critico: worstSev === "CRITICA",
    tipos_risco: Array.from(new Set(legalChecks.map((c) => c.tipo_risco).filter(Boolean))) as string[],
    score_juridico:
      legalChecks.length === 0 && !analyses.length ? 10 : legalChecks.length === 0 ? 8 : 5,
    resumo: legalChecks.length === 0 ? "Nenhum processo identificado." : `${legalChecks.length} processo(s) encontrado(s).`,
  };

  if (!hasAnyData) {
    return (
      <div className="rounded-xl border p-6 text-center" style={{ background: "#fff", borderColor: "var(--border)" }}>
        <div className="text-4xl mb-3">⚖️</div>
        <h3 className="font-serif text-lg mb-2" style={{ color: "var(--ink)" }}>
          Due Diligence Jurídica
        </h3>
        <p className="text-sm mb-5 max-w-sm mx-auto" style={{ color: "var(--mid)" }}>
          Execute a análise para buscar processos judiciais no CNJ Datajud e avaliar
          riscos de evicção, dívidas e pendências jurídicas.
        </p>
        <button
          onClick={onAnalyze}
          disabled={isAnalyzing}
          className="px-6 py-3 text-sm font-semibold rounded-lg transition-all hover:opacity-90 disabled:opacity-50"
          style={{ background: "var(--gold)", color: "#fff" }}
        >
          {isAnalyzing ? "⏳ Analisando..." : "🔍 Iniciar Due Diligence"}
        </button>
        <p className="text-xs mt-3" style={{ color: "var(--mid)" }}>
          Consulta CNJ Datajud + análise IA da matrícula e edital
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Cabeçalho — Score Jurídico */}
      <div
        className="rounded-xl border p-5"
        style={{
          background: summary.tem_risco_critico ? "#fff0f0" : "#fff",
          borderColor: summary.tem_risco_critico ? "#e57373" : "var(--border)",
        }}
      >
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <div className="text-xs uppercase tracking-wider font-semibold mb-2" style={{ color: "var(--mid)" }}>
              Relatório de Due Diligence Jurídica
            </div>
            <ScoreGauge score={summary.score_juridico} />
          </div>
          <div className="text-right">
            <div className="text-xs uppercase tracking-wider mb-1" style={{ color: "var(--mid)" }}>Processos encontrados</div>
            <div
              className="font-serif text-3xl font-bold"
              style={{ color: summary.total_processos > 0 ? "#c0392b" : "#1a6b3c" }}
            >
              {summary.total_processos}
            </div>
          </div>
        </div>
        {summary.tem_risco_critico && (
          <div
            className="mt-4 flex items-center gap-2 p-3 rounded-lg text-sm font-semibold"
            style={{ background: "#c0392b", color: "#fff" }}
          >
            ⛔ Risco crítico identificado — recomendamos consulta jurídica antes de arrematar
          </div>
        )}
        {!summary.tem_risco_critico && summary.total_processos === 0 && (
          <p className="mt-3 text-sm" style={{ color: "var(--mid)" }}>
            ✅ Nenhum processo judicial identificado no CNJ Datajud para este imóvel.
          </p>
        )}
      </div>

      {/* Mapa de Riscos */}
      <div className="rounded-xl border p-5" style={{ background: "#fff", borderColor: "var(--border)" }}>
        <h3 className="font-serif text-base mb-4" style={{ color: "var(--ink)" }}>
          Mapa de Riscos
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <RiskCategoryRow icon="⛔" label="Evicção" active={risco_evicao} severidade="CRITICA" />
          <RiskCategoryRow icon="🏢" label="Dívida Condominial" active={risco_condominio} severidade="ALTA" />
          <RiskCategoryRow icon="🏛️" label="IPTU / Dívida Ativa" active={risco_iptu} severidade="ALTA" />
          <RiskCategoryRow icon="🔒" label="Penhora" active={summary.tipos_risco.includes("PENHORA")} severidade="ALTA" />
          <RiskCategoryRow icon="🏦" label="Hipoteca" active={summary.tipos_risco.includes("HIPOTECA")} severidade="MEDIA" />
          <RiskCategoryRow icon="🏠" label="Imóvel Ocupado" active={risco_ocupacao} severidade="ALTA" />
          <RiskCategoryRow icon="⚖️" label="Processo Judicial" active={risco_processo || summary.total_processos > 0} severidade={worstSev || "MEDIA"} />
          <RiskCategoryRow icon="🌿" label="Irregularidade Ambiental" active={risco_ambiental} severidade="MEDIA" />
        </div>
      </div>

      {/* Processos CNJ */}
      {legalChecks.length > 0 && (
        <div className="rounded-xl border p-5" style={{ background: "#fff", borderColor: "var(--border)" }}>
          <h3 className="font-serif text-base mb-4" style={{ color: "var(--ink)" }}>
            Processos Judiciais — CNJ Datajud ({legalChecks.length})
          </h3>
          <div className="space-y-3">
            {legalChecks.map((check) => {
              const sev = check.severidade || "MEDIA";
              const style = SEVERIDADE_COLOR[sev] || SEVERIDADE_COLOR.MEDIA;
              const isOpen = openProcess === check.id;
              return (
                <div
                  key={check.id}
                  className="rounded-lg border overflow-hidden"
                  style={{ borderColor: style.border }}
                >
                  <button
                    className="w-full text-left p-3 hover:opacity-90 transition-opacity"
                    style={{ background: style.bg }}
                    onClick={() => setOpenProcess(isOpen ? null : check.id)}
                  >
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span
                          className="text-xs font-bold px-2 py-0.5 rounded"
                          style={{ background: "var(--ink)", color: "var(--gold-light)" }}
                        >
                          {check.tribunal}
                        </span>
                        {check.tipo_risco && (
                          <span
                            className="text-xs font-semibold px-2 py-0.5 rounded-full"
                            style={{ background: style.text, color: "#fff" }}
                          >
                            {TIPO_RISCO_ICON[check.tipo_risco] || "⚖️"}{" "}
                            {TIPO_RISCO_LABEL[check.tipo_risco] || check.tipo_risco}
                          </span>
                        )}
                        <span
                          className="text-xs px-2 py-0.5 rounded-full font-medium"
                          style={{ background: "#fff", color: style.text, border: `1px solid ${style.border}` }}
                        >
                          {sev === "CRITICA" ? "CRÍTICO" : sev}
                        </span>
                      </div>
                      <span style={{ color: "var(--mid)", fontSize: 12 }}>{isOpen ? "▲" : "▼"}</span>
                    </div>
                    <div className="mt-2">
                      <p className="text-sm font-semibold" style={{ color: "var(--ink)" }}>
                        {check.numero_processo || "Número não disponível"}
                      </p>
                      {check.classe_processual && (
                        <p className="text-xs mt-0.5" style={{ color: "var(--mid)" }}>
                          {check.classe_processual}
                          {check.grau && ` · ${check.grau}° Grau`}
                        </p>
                      )}
                    </div>
                  </button>

                  {isOpen && (
                    <div
                      className="px-4 py-3 border-t space-y-2"
                      style={{ borderColor: style.border, background: "#fff" }}
                    >
                      {check.assunto && (
                        <div>
                          <div className="text-xs uppercase tracking-wider font-semibold mb-1" style={{ color: "var(--mid)" }}>
                            Assunto
                          </div>
                          <p className="text-sm" style={{ color: "var(--ink)" }}>
                            {check.assunto}
                          </p>
                        </div>
                      )}
                      {check.data_ajuizamento && (
                        <div className="text-xs" style={{ color: "var(--mid)" }}>
                          Ajuizado em: {formatDate(check.data_ajuizamento)}
                        </div>
                      )}
                      <div className="text-xs" style={{ color: "var(--mid)" }}>
                        Verificado em: {formatDate(check.checked_at)}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Riscos detalhados da IA (filtrando para os jurídicos) */}
      {(editalAnalysis || matriculaAnalysis) && (() => {
        const allRisks = [
          ...(editalAnalysis?.riscos_detalhados || []),
          ...(matriculaAnalysis?.riscos_detalhados || []),
        ].filter((r) =>
          ["EVICAO", "ONUS", "HIPOTECA", "PENHORA", "ALIENACAO_FIDUCIARIA",
           "RESTRICAO_JUDICIAL", "DIVIDA_IPTU", "DIVIDA_CONDOMINIO",
           "PROCESSO_JUDICIAL"].includes(r.tipo)
        );

        if (allRisks.length === 0) return null;

        return (
          <div className="rounded-xl border p-5" style={{ background: "#fff", borderColor: "var(--border)" }}>
            <h3 className="font-serif text-base mb-4" style={{ color: "var(--ink)" }}>
              Riscos Identificados pela IA ({allRisks.length})
            </h3>
            <div className="space-y-2">
              {allRisks.map((risco, i) => (
                <div
                  key={i}
                  className="p-3 rounded-lg border"
                  style={{
                    borderColor: (SEVERIDADE_COLOR[risco.severidade] || SEVERIDADE_COLOR.MEDIA).border,
                    background: (SEVERIDADE_COLOR[risco.severidade] || SEVERIDADE_COLOR.MEDIA).bg,
                  }}
                >
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${severidadeBadge(risco.severidade)}`}>
                      {risco.severidade === "CRITICA" ? "CRÍTICO" : risco.severidade}
                    </span>
                    <span className="text-xs font-semibold" style={{ color: "var(--ink)" }}>
                      {TIPO_RISCO_LABEL[risco.tipo] || risco.tipo}
                    </span>
                    {risco.responsavel && risco.responsavel !== "NAO_INFORMADO" && (
                      <span
                        className="text-xs px-2 py-0.5 rounded-full"
                        style={{
                          background: risco.responsavel === "COMPRADOR" ? "#ffe0e0" : "#e0ffe0",
                          color: risco.responsavel === "COMPRADOR" ? "#c0392b" : "#1a6b3c",
                        }}
                      >
                        Responsável: {risco.responsavel === "COMPRADOR" ? "Comprador" : "Vendedor"}
                      </span>
                    )}
                  </div>
                  <p className="text-sm" style={{ color: "var(--ink)" }}>{risco.descricao}</p>
                  {risco.clausula && (
                    <blockquote
                      className="border-l-2 pl-3 text-xs italic mt-2"
                      style={{ borderColor: "var(--gold)", color: "var(--mid)" }}
                    >
                      {risco.clausula}
                    </blockquote>
                  )}
                </div>
              ))}
            </div>
          </div>
        );
      })()}

      {/* Documentos */}
      {(urlMatricula || urlEdital || linkAcesso) && (
        <div className="rounded-xl border p-5" style={{ background: "#fff", borderColor: "var(--border)" }}>
          <h3 className="font-serif text-base mb-3" style={{ color: "var(--ink)" }}>Documentos</h3>
          <div className="space-y-2">
            {urlMatricula && (
              <a href={urlMatricula} target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-2 text-sm p-3 rounded-lg border hover:bg-gray-50 transition-colors"
                style={{ borderColor: "var(--border)", color: "var(--gold)" }}>
                📄 Matrícula do Imóvel (PDF)
                <span className="ml-auto text-xs" style={{ color: "var(--mid)" }}>↗</span>
              </a>
            )}
            {urlEdital && (
              <a href={urlEdital} target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-2 text-sm p-3 rounded-lg border hover:bg-gray-50 transition-colors"
                style={{ borderColor: "var(--border)", color: "var(--gold)" }}>
                📋 Edital do Leilão (PDF)
                <span className="ml-auto text-xs" style={{ color: "var(--mid)" }}>↗</span>
              </a>
            )}
            {linkAcesso && (
              <a href={linkAcesso} target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-2 text-sm p-3 rounded-lg border hover:bg-gray-50 transition-colors"
                style={{ borderColor: "var(--border)", color: "var(--blue, #1a5276)" }}>
                🔗 Página na Caixa Econômica
                <span className="ml-auto text-xs" style={{ color: "var(--mid)" }}>↗</span>
              </a>
            )}
          </div>
        </div>
      )}

      {/* Analisar botão se não analisou ainda */}
      {analyses.length === 0 && legalChecks.length > 0 && (
        <div
          className="rounded-xl border p-4 flex items-center justify-between gap-3"
          style={{ background: "#fffbf0", borderColor: "#e5c84a" }}
        >
          <p className="text-sm" style={{ color: "var(--ink)" }}>
            ⚠️ Análise IA da matrícula/edital ainda não realizada. Solicite para obter riscos detalhados.
          </p>
          <button
            onClick={onAnalyze}
            disabled={isAnalyzing}
            className="shrink-0 px-4 py-2 text-sm font-semibold rounded-lg hover:opacity-90 disabled:opacity-50"
            style={{ background: "var(--gold)", color: "#fff" }}
          >
            {isAnalyzing ? "Analisando..." : "Analisar IA"}
          </button>
        </div>
      )}
    </div>
  );
}
