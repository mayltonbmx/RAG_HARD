"use client";

import { useState } from "react";
import { adminLogin } from "@/lib/api";

interface AdminLoginProps {
  onLoginSuccess: () => void;
}

export default function AdminLoginScreen({ onLoginSuccess }: AdminLoginProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) return;

    setLoading(true);
    setError("");

    try {
      await adminLogin(username, password);
      onLoginSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao fazer login");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-login-overlay">
      <form className="admin-login-card" onSubmit={handleSubmit}>
        <div className="admin-login-icon">🔐</div>
        <h2>Acesso Administrativo</h2>
        <p className="admin-login-desc">
          Faça login para gerenciar arquivos de treinamento e visualizar analytics.
        </p>

        {error && <div className="admin-login-error">{error}</div>}

        <div className="admin-field">
          <label htmlFor="admin-user">Usuário</label>
          <input
            id="admin-user"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="admin"
            autoComplete="username"
            autoFocus
          />
        </div>

        <div className="admin-field">
          <label htmlFor="admin-pass">Senha</label>
          <input
            id="admin-pass"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            autoComplete="current-password"
          />
        </div>

        <button type="submit" className="btn-admin-login" disabled={loading || !username || !password}>
          {loading ? "Entrando..." : "Entrar"}
        </button>
      </form>
    </div>
  );
}
