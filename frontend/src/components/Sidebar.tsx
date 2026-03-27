"use client";

import { ViewType } from "@/types";

interface SidebarProps {
  activeView: ViewType;
  onViewChange: (view: ViewType) => void;
  onNewChat: () => void;
}

const navItems: { id: ViewType; label: string; icon: string }[] = [
  { id: "chat", label: "Chat", icon: "💬" },
  { id: "upload", label: "Upload", icon: "📤" },
  { id: "files", label: "Arquivos", icon: "📂" },
  { id: "stats", label: "Stats", icon: "📊" },
];

export default function Sidebar({ activeView, onViewChange, onNewChat }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon">⬡</div>
        <div className="brand-text">
          <span className="brand-name">RAG Hard</span>
          <span className="brand-sub">CHAT INTELIGENTE</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={`nav-item ${activeView === item.id ? "active" : ""}`}
            onClick={() => onViewChange(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <button className="btn-new-chat" onClick={onNewChat}>
          + Nova Conversa
        </button>
        <div className="tech-badges">
          <div className="tech-badge">
            <span className="badge-dot" /> Gemini 2.5 Flash
          </div>
          <div className="tech-badge">
            <span className="badge-dot pinecone" /> Pinecone Vector DB
          </div>
        </div>
      </div>
    </aside>
  );
}
