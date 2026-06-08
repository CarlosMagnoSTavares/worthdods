import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Worthdods — O Score de Arrematação Mais Preciso do Brasil",
  description:
    "Análise profunda de imóveis em leilão da Caixa com IA. Score IPL, análise de matrícula, edital e processos judiciais.",
  keywords: "leilão imóvel, caixa econômica, score leilão, análise imóvel leilão",
  openGraph: {
    title: "Worthdods",
    description: "O Score de Arrematação Mais Preciso do Brasil",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="min-h-screen" style={{ background: "var(--paper)" }}>
        {children}
      </body>
    </html>
  );
}
