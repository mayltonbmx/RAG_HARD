"use client";

import { useState } from "react";
import { getSupabaseBrowser } from "@/lib/supabase-browser";

type Mode = "login" | "register" | "forgot";

export default function LoginScreen() {
  const [mode, setMode] = useState<Mode>("login");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const supabase = getSupabaseBrowser();

  const resetForm = () => {
    setError("");
    setSuccess("");
    setPassword("");
    setConfirmPassword("");
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password || loading) return;

    setLoading(true);
    setError("");

    try {
      const { error } = await supabase.auth.signInWithPassword({
        email: email.trim(),
        password,
      });
      if (error) throw error;
      window.location.href = "/";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao fazer login.");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!firstName.trim() || !lastName.trim() || !email.trim() || !password || loading) return;

    if (password !== confirmPassword) {
      setError("As senhas não coincidem.");
      return;
    }

    if (password.length < 6) {
      setError("A senha deve ter pelo menos 6 caracteres.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const { error } = await supabase.auth.signUp({
        email: email.trim(),
        password,
        options: {
          data: {
            first_name: firstName.trim(),
            last_name: lastName.trim(),
            full_name: `${firstName.trim()} ${lastName.trim()}`,
          },
        },
      });
      if (error) throw error;

      setSuccess("Conta criada! Verifique seu e-mail para confirmar o cadastro.");
      setMode("login");
      setPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar conta.");
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || loading) return;

    setLoading(true);
    setError("");

    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), {
        redirectTo: `${window.location.origin}/`,
      });
      if (error) throw error;
      setSuccess("E-mail de recuperação enviado. Verifique sua caixa de entrada.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao enviar e-mail.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-screen">
      <div className="login-card">
        <div className="login-icon">⬡</div>
        <h1>FonteCerta</h1>
        <p className="login-subtitle">Chat Especialista</p>

        {mode === "login" && (
          <>
            <p className="login-description">
              Acesse sua conta para continuar.
            </p>
            <form onSubmit={handleLogin} className="login-form">
              {error && <div className="login-error">{error}</div>}
              {success && <div className="login-success">{success}</div>}
              <div className="login-field">
                <label htmlFor="login-email">E-mail</label>
                <input
                  id="login-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="seu@email.com"
                  autoComplete="email"
                  autoFocus
                  required
                />
              </div>
              <div className="login-field">
                <label htmlFor="login-password">Senha</label>
                <input
                  id="login-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  required
                />
              </div>
              <button
                type="submit"
                className="btn-login-primary"
                disabled={loading || !email.trim() || !password}
              >
                {loading ? "Entrando..." : "Entrar"}
              </button>
              <div className="login-links">
                <button
                  type="button"
                  className="btn-link"
                  onClick={() => { resetForm(); setMode("forgot"); }}
                >
                  Esqueci minha senha
                </button>
                <button
                  type="button"
                  className="btn-link"
                  onClick={() => { resetForm(); setMode("register"); }}
                >
                  Criar conta
                </button>
              </div>
            </form>
          </>
        )}

        {mode === "register" && (
          <>
            <p className="login-description">
              Crie sua conta para acessar a plataforma.
            </p>
            <form onSubmit={handleRegister} className="login-form">
              {error && <div className="login-error">{error}</div>}
              <div className="login-row">
                <div className="login-field">
                  <label htmlFor="reg-first">Nome</label>
                  <input
                    id="reg-first"
                    type="text"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    placeholder="João"
                    autoFocus
                    required
                  />
                </div>
                <div className="login-field">
                  <label htmlFor="reg-last">Sobrenome</label>
                  <input
                    id="reg-last"
                    type="text"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    placeholder="Silva"
                    required
                  />
                </div>
              </div>
              <div className="login-field">
                <label htmlFor="reg-email">E-mail</label>
                <input
                  id="reg-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="seu@email.com"
                  autoComplete="email"
                  required
                />
              </div>
              <div className="login-field">
                <label htmlFor="reg-password">Senha</label>
                <input
                  id="reg-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Mínimo 6 caracteres"
                  autoComplete="new-password"
                  required
                />
              </div>
              <div className="login-field">
                <label htmlFor="reg-confirm">Confirmar senha</label>
                <input
                  id="reg-confirm"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Repita a senha"
                  autoComplete="new-password"
                  required
                />
              </div>
              <button
                type="submit"
                className="btn-login-primary"
                disabled={loading || !firstName.trim() || !lastName.trim() || !email.trim() || !password || !confirmPassword}
              >
                {loading ? "Criando..." : "Criar conta"}
              </button>
              <div className="login-links">
                <button
                  type="button"
                  className="btn-link"
                  onClick={() => { resetForm(); setMode("login"); }}
                >
                  ← Já tenho conta
                </button>
              </div>
            </form>
          </>
        )}

        {mode === "forgot" && (
          <>
            <p className="login-description">
              Informe seu e-mail para receber o link de recuperação.
            </p>
            <form onSubmit={handleForgotPassword} className="login-form">
              {error && <div className="login-error">{error}</div>}
              {success && <div className="login-success">{success}</div>}
              <div className="login-field">
                <label htmlFor="forgot-email">E-mail</label>
                <input
                  id="forgot-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="seu@email.com"
                  autoComplete="email"
                  autoFocus
                  required
                />
              </div>
              <button
                type="submit"
                className="btn-login-primary"
                disabled={loading || !email.trim()}
              >
                {loading ? "Enviando..." : "Enviar link"}
              </button>
              <div className="login-links">
                <button
                  type="button"
                  className="btn-link"
                  onClick={() => { resetForm(); setMode("login"); }}
                >
                  ← Voltar ao login
                </button>
              </div>
            </form>
          </>
        )}

        <p className="login-footer">
          Desenvolvido por <strong>Maylton Tavares</strong>
        </p>
      </div>
    </div>
  );
}
