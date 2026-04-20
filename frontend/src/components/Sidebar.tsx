"use client";

import { useSession, signOut } from "next-auth/react";
import { ViewType } from "@/types";
import { adminLogout, getAdminToken } from "@/lib/api";
import { useState, useEffect } from "react";

interface SidebarProps {
  activeView: ViewType;
  onViewChange: (view: ViewType) => void;
  onNewChat: () => void;
  isAdminLoggedIn: boolean;
  onAdminLogout: () => void;
}

export default function Sidebar({ activeView, onViewChange, onNewChat, isAdminLoggedIn, onAdminLogout }: SidebarProps) {
  const { data: session } = useSession();

  const azureRoles: string[] = session?.roles ?? [];
  const isAdmin = azureRoles.includes("Admin") || isAdminLoggedIn;

  // Build nav items based on role
  const navItems: { id: ViewType; label: string; icon: string; adminOnly?: boolean }[] = [
    { id: "chat", label: "Chat", icon: "💬" },
    { id: "stats", label: "Stats", icon: "📊" },
    { id: "analytics", label: "Analytics", icon: "📈", adminOnly: true },
    { id: "upload", label: "Upload", icon: "📤", adminOnly: true },
    { id: "files", label: "Arquivos", icon: "📂", adminOnly: true },
  ];

  const visibleItems = navItems.filter((item) => !item.adminOnly || isAdmin);

  const handleLogout = () => {
    if (session?.user) {
      signOut({ callbackUrl: "/login" });
    } else if (isAdminLoggedIn) {
      adminLogout();
      onAdminLogout();
    }
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon">⬡</div>
        <div className="brand-text">
          <span className="brand-name">Hard Educação</span>
          <span className="brand-sub">CHAT INTELIGENTE</span>
        </div>
      </div>

      {/* User info */}
      {(session?.user || isAdminLoggedIn) && (
        <div className="sidebar-user">
          <div className="user-avatar">
            {session?.user?.image ? (
              <img src={session.user.image} alt="" className="user-avatar-img" />
            ) : (
              <span>{isAdminLoggedIn ? "A" : session?.user?.name?.charAt(0)?.toUpperCase() || "?"}</span>
            )}
          </div>
          <div className="user-info">
            <span className="user-name">{isAdminLoggedIn ? "Administrador" : session?.user?.name}</span>
            <span className="user-role">{isAdmin ? "Admin" : "Usuário"}</span>
          </div>
        </div>
      )}

      <nav className="sidebar-nav">
        {visibleItems.map((item) => (
          <button
            key={item.id}
            className={`nav-item ${activeView === item.id ? "active" : ""}`}
            onClick={() => onViewChange(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            <span>{item.label}</span>
            {item.adminOnly && <span className="admin-badge">ADMIN</span>}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <button className="btn-new-chat" onClick={onNewChat}>
          + Nova Conversa
        </button>

        {!isAdmin && !session?.user && (
          <button className="btn-admin-access" onClick={() => onViewChange("analytics")}>
            🔐 Acesso Admin
          </button>
        )}

        {(session?.user || isAdminLoggedIn) && (
          <button className="btn-logout" onClick={handleLogout}>
            ↪ Sair
          </button>
        )}

        <div className="tech-badges">
          <div className="tech-badge">
            <span className="badge-dot" /> Gemini 2.5 Flash
          </div>
          <div className="tech-badge">
            <span className="badge-dot pinecone" /> Pinecone Vector DB
          </div>
        </div>
        <div className="sidebar-author">
          Desenvolvido por Maylton Tavares
        </div>
      </div>
    </aside>
  );
}
