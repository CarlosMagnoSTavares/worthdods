import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Hero */}
      <div
        className="relative overflow-hidden"
        style={{ background: "var(--ink)", color: "var(--paper)" }}
      >
        {/* Diagonal gold pattern */}
        <div
          className="absolute inset-0"
          style={{
            background:
              "repeating-linear-gradient(45deg, transparent, transparent 40px, rgba(184,134,11,0.04) 40px, rgba(184,134,11,0.04) 80px)",
          }}
        />
        <div className="relative z-10 max-w-5xl mx-auto px-6 py-20">
          <div
            className="inline-flex items-center gap-2 text-xs font-semibold tracking-widest uppercase px-3 py-1.5 rounded mb-8"
            style={{ background: "var(--gold)", color: "#fff" }}
          >
            <span>🏆</span> O Score de Arrematação Mais Preciso do Brasil
          </div>
          <h1
            className="font-serif text-5xl md:text-7xl leading-tight mb-6"
            style={{ color: "var(--paper)" }}
          >
            Compre imóveis em leilão{" "}
            <span style={{ color: "var(--gold-light)" }}>com segurança</span>
          </h1>
          <p className="text-lg max-w-xl mb-10" style={{ color: "#a09888" }}>
            Análise profunda do edital e da matrícula via IA. Score IPL,
            riscos jurídicos, processos judiciais — tudo em um relatório claro.
          </p>
          <div className="flex flex-wrap gap-4">
            <Link
              href="/dashboard"
              className="px-8 py-4 text-base font-semibold rounded-lg transition-all hover:opacity-90"
              style={{ background: "var(--gold)", color: "#fff" }}
            >
              Ver Imóveis em Leilão →
            </Link>
            <a
              href="#como-funciona"
              className="px-8 py-4 text-base font-semibold rounded-lg border transition-all hover:bg-white/10"
              style={{ borderColor: "var(--border)", color: "var(--paper)" }}
            >
              Como Funciona
            </a>
          </div>
        </div>
        <div className="gold-divider" />
      </div>

      {/* Stats */}
      <div
        className="py-12"
        style={{ background: "var(--cream)", borderBottom: "1px solid var(--border)" }}
      >
        <div className="max-w-5xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-8">
          {[
            { label: "Imóveis Monitorados", value: "5.000+", sub: "27 estados" },
            { label: "Análises IA", value: "Matrícula + Edital", sub: "Documentos reais" },
            { label: "Score IPL", value: "0–10", sub: "Baseado em dados" },
            { label: "Processos Judiciais", value: "CNJ Datajud", sub: "API oficial" },
          ].map((s) => (
            <div key={s.label} className="text-center">
              <div className="font-serif text-2xl md:text-3xl" style={{ color: "var(--gold)" }}>
                {s.value}
              </div>
              <div className="text-sm font-semibold mt-1" style={{ color: "var(--ink)" }}>
                {s.label}
              </div>
              <div className="text-xs mt-0.5" style={{ color: "var(--mid)" }}>
                {s.sub}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Como Funciona */}
      <div id="como-funciona" className="py-20 max-w-5xl mx-auto px-6">
        <div className="text-center mb-14">
          <h2 className="font-serif text-4xl mb-3" style={{ color: "var(--ink)" }}>
            Como o Worthdods funciona
          </h2>
          <p style={{ color: "var(--mid)" }}>
            Da busca à análise jurídica em minutos
          </p>
        </div>
        <div className="grid md:grid-cols-3 gap-8">
          {[
            {
              n: "1",
              title: "Busque imóveis",
              desc: "Filtramos todos os imóveis em leilão da Caixa por estado, preço, score IPL e modalidade.",
              icon: "🔍",
            },
            {
              n: "2",
              title: "Score IPL automático",
              desc: "O Índice de Potencial de Leilão calcula desconto, risco jurídico e oportunidade em um score 0–10.",
              icon: "📊",
            },
            {
              n: "3",
              title: "Análise IA do edital",
              desc: "Nossa IA lê a matrícula e o edital e extrai: evicção, dívidas, ocupação e processos judiciais.",
              icon: "⚖️",
            },
          ].map((s) => (
            <div
              key={s.n}
              className="rounded-xl p-6 border shadow-sm"
              style={{ background: "#fff", borderColor: "var(--border)" }}
            >
              <div className="text-3xl mb-3">{s.icon}</div>
              <div
                className="font-serif text-xl mb-2"
                style={{ color: "var(--ink)" }}
              >
                {s.title}
              </div>
              <p className="text-sm leading-relaxed" style={{ color: "var(--mid)" }}>
                {s.desc}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* CTA */}
      <div
        className="py-16 text-center"
        style={{ background: "var(--ink)", color: "var(--paper)" }}
      >
        <h2 className="font-serif text-3xl mb-4">
          Pronto para arrematar com <span style={{ color: "var(--gold-light)" }}>segurança</span>?
        </h2>
        <p className="mb-8" style={{ color: "#a09888" }}>
          Acesse gratuitamente e veja os imóveis com maior potencial hoje.
        </p>
        <Link
          href="/dashboard"
          className="inline-block px-10 py-4 text-base font-semibold rounded-lg transition-all hover:opacity-90"
          style={{ background: "var(--gold)", color: "#fff" }}
        >
          Acessar Dashboard Gratuito →
        </Link>
      </div>

      {/* Footer */}
      <footer
        className="py-8 text-center text-sm"
        style={{
          background: "var(--cream)",
          borderTop: "1px solid var(--border)",
          color: "var(--mid)",
        }}
      >
        <p>
          © 2024 Worthdods · Dados: Caixa Econômica Federal · CNJ Datajud ·
          Análise IA: OpenRouter
        </p>
        <p className="mt-1 text-xs">
          Não constitui assessoria jurídica ou financeira. Consulte um profissional antes de arrematar.
        </p>
      </footer>
    </div>
  );
}
