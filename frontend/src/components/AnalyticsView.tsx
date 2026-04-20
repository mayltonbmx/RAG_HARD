"use client";

import { useState, useEffect } from "react";
import { getTopQueries, getAnalyticsStats, TopQuery, AnalyticsStats } from "@/lib/api";

export default function AnalyticsView() {
  const [stats, setStats] = useState<AnalyticsStats | null>(null);
  const [topQueries, setTopQueries] = useState<TopQuery[]>([]);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchData = async () => {
    setLoading(true);
    setError("");
    try {
      const [statsData, queriesData] = await Promise.all([
        getAnalyticsStats(days),
        getTopQueries(20, days),
      ]);
      setStats(statsData);
      setTopQueries(queriesData.queries);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar analytics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [days]);

  if (loading) {
    return (
      <div className="analytics-view">
        <div className="analytics-loading">
          <div className="loading-spinner" />
          <p>Carregando analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics-view">
        <div className="analytics-error">
          <p>❌ {error}</p>
          <button className="btn-retry" onClick={fetchData}>Tentar novamente</button>
        </div>
      </div>
    );
  }

  const intentColors: Record<string, string> = {
    tecnica: "#6c5ce7",
    comparacao: "#00b894",
    aplicacao: "#fdcb6e",
    geral: "#636e72",
  };

  return (
    <div className="analytics-view">
      <div className="analytics-header">
        <h2>📊 Analytics</h2>
        <div className="period-selector">
          {[7, 30, 90].map((d) => (
            <button
              key={d}
              className={`period-btn ${days === d ? "active" : ""}`}
              onClick={() => setDays(d)}
            >
              {d}d
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <span className="kpi-value">{stats?.total_queries || 0}</span>
          <span className="kpi-label">Total de Perguntas</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-value">{stats?.avg_latency_ms ? `${(stats.avg_latency_ms / 1000).toFixed(1)}s` : "—"}</span>
          <span className="kpi-label">Latência Média</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-value">{stats?.avg_chunks_used?.toFixed(1) || "—"}</span>
          <span className="kpi-label">Chunks Médios</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-value">{stats?.avg_score ? `${(stats.avg_score * 100).toFixed(0)}%` : "—"}</span>
          <span className="kpi-label">Score Médio</span>
        </div>
      </div>

      {/* Intent Distribution */}
      {stats?.intent_distribution && Object.keys(stats.intent_distribution).length > 0 && (
        <div className="analytics-section">
          <h3>🎯 Distribuição de Intents</h3>
          <div className="intent-bars">
            {Object.entries(stats.intent_distribution).map(([intent, count]) => {
              const total = Object.values(stats.intent_distribution).reduce((a, b) => a + b, 0);
              const pct = total > 0 ? (count / total) * 100 : 0;
              return (
                <div key={intent} className="intent-row">
                  <span className="intent-label">{intent}</span>
                  <div className="intent-bar-wrapper">
                    <div
                      className="intent-bar-fill"
                      style={{
                        width: `${pct}%`,
                        backgroundColor: intentColors[intent] || "#a29bfe",
                      }}
                    />
                  </div>
                  <span className="intent-count">{count} ({pct.toFixed(0)}%)</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Queries Per Day */}
      {stats?.queries_per_day && Object.keys(stats.queries_per_day).length > 0 && (
        <div className="analytics-section">
          <h3>📅 Perguntas por Dia</h3>
          <div className="day-chart">
            {(() => {
              const entries = Object.entries(stats.queries_per_day);
              const maxCount = Math.max(...entries.map(([, v]) => v), 1);
              return entries.slice(-14).map(([day, count]) => (
                <div key={day} className="day-bar-col">
                  <div
                    className="day-bar"
                    style={{ height: `${(count / maxCount) * 100}%` }}
                    title={`${day}: ${count} perguntas`}
                  />
                  <span className="day-label">{day.slice(5)}</span>
                </div>
              ));
            })()}
          </div>
        </div>
      )}

      {/* Top Queries */}
      <div className="analytics-section">
        <h3>🔥 Perguntas Mais Frequentes</h3>
        {topQueries.length === 0 ? (
          <p className="analytics-empty">Nenhuma pergunta registrada no período.</p>
        ) : (
          <div className="top-queries-list">
            {topQueries.map((q, i) => (
              <div key={q.query_hash} className="query-item">
                <span className="query-rank">#{i + 1}</span>
                <span className="query-text">{q.query}</span>
                <span className="query-count">{q.count}x</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
