"use client";

import { useState, useEffect } from "react";
import { getStats } from "@/lib/api";
import { StatsData } from "@/types";

export default function StatsView() {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getStats()
      .then(setStats)
      .catch(() => setStats(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-container"><div className="loading-spinner" /><p>Carregando...</p></div>;
  if (!stats) return <div className="no-results"><h3>Erro ao carregar estatisticas</h3></div>;

  const cards = [
    { label: "Vetores", value: stats.total_vectors, detail: "documentos indexados" },
    { label: "Dimensao", value: stats.dimension, detail: "dimensoes por vetor" },
    { label: "Arquivos", value: stats.total_files, detail: "no diretorio data/" },
    { label: "Modelo", value: stats.model, detail: "Gemini Embedding", small: true },
  ];

  return (
    <div className="view-content">
      <div className="view-header">
        <h1>Estatisticas</h1>
        <p className="view-subtitle">Informacoes do indice vetorial no Pinecone</p>
      </div>
      <div className="stats-grid">
        {cards.map((c, i) => (
          <div key={i} className="stat-card">
            <span className="stat-label">{c.label}</span>
            <span className={`stat-value ${c.small ? "small" : ""}`}>{c.value}</span>
            <span className="stat-detail">{c.detail}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
