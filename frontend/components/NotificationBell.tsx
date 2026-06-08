"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useNotifications } from "@/lib/notifications";
import type { AppNotification } from "@/lib/notifications";

function timeAgo(ts: number) {
  const diff = Math.floor((Date.now() - ts) / 1000);
  if (diff < 60) return "agora";
  if (diff < 3600) return `${Math.floor(diff / 60)}min atrás`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h atrás`;
  return `${Math.floor(diff / 86400)}d atrás`;
}

function NotifItem({ n, onClose }: { n: AppNotification; onClose: () => void }) {
  const router = useRouter();
  const { clearNotification } = useNotifications();

  return (
    <div
      className="flex items-start gap-3 px-4 py-3 border-b hover:bg-gray-50 transition-colors"
      style={{ borderColor: "var(--cream)" }}
    >
      <button
        className="flex items-start gap-3 flex-1 text-left"
        onClick={() => {
          router.push(`/imovel/${n.propertyId}`);
          onClose();
        }}
      >
        <span className="text-lg mt-0.5 flex-shrink-0">
          {n.status === "processing" ? "⏳" : n.status === "done" ? "✅" : "❌"}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold truncate" style={{ color: "var(--ink)" }}>
            {n.propertyAddress}
          </p>
          <p className="text-xs mt-0.5" style={{ color: "var(--mid)" }}>
            {n.cidade}
          </p>
          <p
            className="text-xs mt-0.5 font-medium"
            style={{
              color:
                n.status === "processing"
                  ? "var(--gold)"
                  : n.status === "done"
                  ? "var(--green)"
                  : "var(--red)",
            }}
          >
            {n.status === "processing"
              ? "Analisando… aguarde"
              : n.status === "done"
              ? "Análise concluída ✓"
              : "Erro na análise"}
          </p>
          <p className="text-xs mt-0.5" style={{ color: "var(--mid)", opacity: 0.7 }}>
            {timeAgo(n.triggeredAt)}
          </p>
        </div>
        {!n.read && n.status === "done" && (
          <span
            className="w-2 h-2 rounded-full mt-1.5 flex-shrink-0"
            style={{ background: "var(--gold)" }}
          />
        )}
      </button>
      <button
        onClick={(e) => {
          e.stopPropagation();
          clearNotification(n.id);
        }}
        className="text-xs opacity-40 hover:opacity-80 flex-shrink-0 mt-0.5"
        title="Remover"
        style={{ color: "var(--mid)" }}
      >
        ✕
      </button>
    </div>
  );
}

export function NotificationBell() {
  const { notifications, unreadCount, markAllRead } = useNotifications();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const processingCount = notifications.filter((n) => n.status === "processing").length;

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  function toggle() {
    if (!open && unreadCount > 0) markAllRead();
    setOpen((v) => !v);
  }

  const recent = notifications.slice(0, 10);

  return (
    <div className="relative" ref={ref}>
      {/* Bell button */}
      <button
        onClick={toggle}
        className="relative p-2 rounded-lg transition-colors"
        style={{ color: "var(--paper)" }}
        title="Notificações de análise"
      >
        {/* Animated bell when processing */}
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={processingCount > 0 ? "animate-bounce" : ""}
        >
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>

        {/* Badge: unread done */}
        {unreadCount > 0 && (
          <span
            className="absolute -top-0.5 -right-0.5 w-4 h-4 flex items-center justify-center rounded-full font-bold"
            style={{ background: "var(--red)", color: "#fff", fontSize: "10px" }}
          >
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}

        {/* Pulse: processing */}
        {processingCount > 0 && unreadCount === 0 && (
          <span
            className="absolute -top-0.5 -right-0.5 w-3 h-3 rounded-full animate-ping"
            style={{ background: "var(--gold)", opacity: 0.75 }}
          />
        )}
      </button>

      {/* Dropdown */}
      {open && (
        <div
          className="absolute right-0 top-full mt-2 w-80 rounded-xl shadow-2xl border overflow-hidden z-50"
          style={{ background: "#fff", borderColor: "var(--border)" }}
        >
          {/* Header */}
          <div
            className="px-4 py-3 flex items-center justify-between border-b"
            style={{ background: "var(--ink)", borderColor: "rgba(184,134,11,0.3)" }}
          >
            <span className="text-sm font-semibold" style={{ color: "var(--paper)" }}>
              Análises IA
            </span>
            {processingCount > 0 && (
              <span
                className="text-xs px-2 py-0.5 rounded-full font-medium"
                style={{ background: "rgba(184,134,11,0.2)", color: "var(--gold-light)" }}
              >
                {processingCount} em andamento
              </span>
            )}
          </div>

          {/* List */}
          {recent.length === 0 ? (
            <div className="px-4 py-8 text-center">
              <p className="text-sm" style={{ color: "var(--mid)" }}>
                Nenhuma análise solicitada
              </p>
              <p className="text-xs mt-1" style={{ color: "var(--mid)", opacity: 0.7 }}>
                Clique em "Analisar com IA" em qualquer imóvel
              </p>
            </div>
          ) : (
            <div className="max-h-80 overflow-y-auto">
              {recent.map((n) => (
                <NotifItem key={n.id} n={n} onClose={() => setOpen(false)} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
