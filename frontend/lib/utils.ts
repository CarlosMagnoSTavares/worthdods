import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatBRL(value: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatBRLFull(value: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(value);
}

export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

export function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

export function iplColor(classificacao: string): string {
  const map: Record<string, string> = {
    Excelente: "#1a6b3c",
    Bom: "#4a7c2f",
    Regular: "#b8860b",
    Ruim: "#c0642b",
    "Crítico": "#c0392b",
  };
  return map[classificacao] || "#6b6055";
}

export function iplBgColor(classificacao: string): string {
  const map: Record<string, string> = {
    Excelente: "bg-green-600",
    Bom: "bg-lime-600",
    Regular: "bg-yellow-600",
    Ruim: "bg-orange-600",
    "Crítico": "bg-red-600",
  };
  return map[classificacao] || "bg-gray-500";
}

export function severidadeBadge(severidade: string): string {
  const map: Record<string, string> = {
    BAIXA: "bg-blue-100 text-blue-800",
    MEDIA: "bg-yellow-100 text-yellow-800",
    ALTA: "bg-orange-100 text-orange-800",
    CRITICA: "bg-red-100 text-red-800",
  };
  return map[severidade] || "bg-gray-100 text-gray-800";
}
