"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";

export interface AppNotification {
  id: string;
  propertyId: string;
  propertyAddress: string;
  cidade: string;
  status: "processing" | "done" | "error";
  triggeredAt: number;
  read: boolean;
}

interface NotificationsContextType {
  notifications: AppNotification[];
  addNotification: (n: Omit<AppNotification, "id" | "triggeredAt" | "read">) => void;
  markAllRead: () => void;
  clearNotification: (id: string) => void;
  unreadCount: number;
}

const Ctx = createContext<NotificationsContextType>({
  notifications: [],
  addNotification: () => {},
  markAllRead: () => {},
  clearNotification: () => {},
  unreadCount: 0,
});

const STORAGE_KEY = "worthdods_notifications_v1";
const POLL_MS = 12000;
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const [notifications, setNotifications] = useState<AppNotification[]>(() => {
    if (typeof window === "undefined") return [];
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(notifications));
    } catch {}
  }, [notifications]);

  // Poll processing notifications
  useEffect(() => {
    const processing = notifications.filter((n) => n.status === "processing");
    if (processing.length === 0) return;

    const timer = setInterval(async () => {
      for (const notif of processing) {
        try {
          const res = await fetch(`${API_URL}/api/v1/properties/${notif.propertyId}/analysis`);
          if (!res.ok) continue;
          const data = await res.json();
          if (data.analyses && data.analyses.length > 0) {
            setNotifications((prev) =>
              prev.map((n) =>
                n.id === notif.id ? { ...n, status: "done", read: false } : n
              )
            );
          }
        } catch {}
      }
    }, POLL_MS);

    return () => clearInterval(timer);
  }, [notifications]);

  const addNotification = useCallback(
    (n: Omit<AppNotification, "id" | "triggeredAt" | "read">) => {
      setNotifications((prev) => {
        // If already tracking this property, update status
        const idx = prev.findIndex((x) => x.propertyId === n.propertyId);
        if (idx !== -1) {
          const updated = [...prev];
          updated[idx] = { ...updated[idx], status: n.status, read: false, triggeredAt: Date.now() };
          return updated;
        }
        return [
          { ...n, id: `${n.propertyId}-${Date.now()}`, triggeredAt: Date.now(), read: false },
          ...prev.slice(0, 19),
        ];
      });
    },
    []
  );

  const markAllRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  }, []);

  const clearNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const unreadCount = notifications.filter((n) => !n.read && n.status === "done").length;

  return (
    <Ctx.Provider value={{ notifications, addNotification, markAllRead, clearNotification, unreadCount }}>
      {children}
    </Ctx.Provider>
  );
}

export const useNotifications = () => useContext(Ctx);
