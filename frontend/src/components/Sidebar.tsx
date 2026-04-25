"use client";

import { useAuth } from "./AuthProvider";
import { ViewType } from "@/types";
import { adminLogout, getAdminToken } from "@/lib/api";

interface SidebarProps {
  activeView: ViewType;
  onViewChange: (view: ViewType) => void;
  onNewChat: () => void;
  isAdminLoggedIn: boolean;
  onAdminLogout: () => void;
}

export default function Sidebar({ activeView, onViewChange, onNewChat, isAdminLoggedIn, onAdminLogout }: SidebarProps) {
  const { user, signOut } = useAuth();

  const isAdmin = isAdminLoggedIn;

  // Build nav items based on role
  const navItems: { id: ViewType; label: string; icon: string; adminOnly?: boolean }[] = [
    { id: "chat", label: "Chat", icon: "💬" },
    { id: "stats", label: "Stats", icon: "📊" },
    { id: "analytics", label: "Analytics", icon: "📈", adminOnly: true },
    { id: "upload", label: "Upload", icon: "📤", adminOnly: true },
    { id: "files", label: "Arquivos", icon: "📂", adminOnly: true },
    { id: "personas", label: "Especialistas", icon: "🧠", adminOnly: true },
  ];

  const visibleItems = navItems.filter((item) => !item.adminOnly || isAdmin);

  const handleLogout = async () => {
    if (isAdminLoggedIn) {
      adminLogout();
      onAdminLogout();
    }
    // Always sign out from Supabase
    await signOut();
  };

  const displayName = user?.user_metadata?.full_name || user?.user_metadata?.first_name || user?.email?.split("@")[0] || "Usuário";

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon">⬡</div>
        <div className="brand-text">
          <span className="brand-name">FonteCerta</span>
          <span className="brand-sub">CHAT ESPECIALISTA</span>
        </div>
      </div>

      {/* User info */}
      {user && (
        <div className="sidebar-user">
          <div className="user-avatar">
            <span>{isAdminLoggedIn ? "A" : displayName.charAt(0).toUpperCase()}</span>
          </div>
          <div className="user-info">
            <span className="user-name">{isAdminLoggedIn ? "Administrador" : displayName}</span>
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

        {!isAdmin && (
          <button className="btn-admin-access" onClick={() => onViewChange("analytics")}>
            🔐 Acesso Admin
          </button>
        )}

        <button className="btn-logout" onClick={handleLogout}>
          ↪ Sair
        </button>

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
