"use client";

import Link from "next/link";
import { NotificationProvider } from "@/lib/notifications";
import { NotificationBell } from "@/components/NotificationBell";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <NotificationProvider>
      <div className="min-h-screen flex flex-col">
        {/* Navbar */}
        <nav
          className="sticky top-0 z-40 border-b"
          style={{
            background: "var(--ink)",
            borderColor: "rgba(184,134,11,0.3)",
          }}
        >
          <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-14">
            <Link href="/" className="flex items-center gap-2">
              <span className="font-serif text-xl" style={{ color: "var(--gold-light)" }}>
                Worthdods
              </span>
              <span
                className="hidden sm:inline text-xs px-2 py-0.5 rounded"
                style={{ background: "var(--gold)", color: "#fff" }}
              >
                BETA
              </span>
            </Link>
            <div className="flex items-center gap-3">
              <Link
                href="/dashboard"
                className="text-sm font-medium hover:opacity-80"
                style={{ color: "var(--paper)" }}
              >
                Dashboard
              </Link>
              <a
                href="/"
                className="text-sm font-medium hover:opacity-80"
                style={{ color: "var(--mid)" }}
              >
                Início
              </a>
              <NotificationBell />
            </div>
          </div>
          <div className="gold-divider" />
        </nav>

        {/* Content */}
        <main className="flex-1">{children}</main>

        {/* Footer */}
        <footer
          className="py-6 text-center text-xs border-t"
          style={{
            background: "var(--cream)",
            borderColor: "var(--border)",
            color: "var(--mid)",
          }}
        >
          Worthdods · Dados da Caixa Econômica Federal · Não constitui assessoria jurídica ou financeira
        </footer>
      </div>
    </NotificationProvider>
  );
}
