"use client";

import { useState, useRef, useEffect } from "react";
import { getSupabaseBrowser } from "@/lib/supabase-browser";

export default function LoginScreen() {
  const [step, setStep] = useState<"email" | "otp">("email");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const codeRef = useRef<HTMLInputElement>(null);

  const supabase = getSupabaseBrowser();

  useEffect(() => {
    if (countdown <= 0) return;
    const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
    return () => clearTimeout(timer);
  }, [countdown]);

  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || loading) return;

    setLoading(true);
    setError("");

    try {
      const { error } = await supabase.auth.signInWithOtp({
        email: email.trim(),
        options: { shouldCreateUser: true },
      });
      if (error) throw error;

      setStep("otp");
      setCountdown(60);
      setTimeout(() => codeRef.current?.focus(), 100);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao enviar código.");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = code.trim();
    if (trimmed.length < 6 || loading) return;

    setLoading(true);
    setError("");

    try {
      const { error } = await supabase.auth.verifyOtp({
        email: email.trim(),
        token: trimmed,
        type: "email",
      });
      if (error) throw error;

      window.location.href = "/";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Código inválido.");
      setCode("");
      codeRef.current?.focus();
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (countdown > 0) return;
    setCode("");
    setError("");
    setLoading(true);

    try {
      const { error } = await supabase.auth.signInWithOtp({
        email: email.trim(),
        options: { shouldCreateUser: true },
      });
      if (error) throw error;
      setCountdown(60);
      codeRef.current?.focus();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao reenviar.");
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

        {step === "email" ? (
          <>
            <p className="login-description">
              Insira seu e-mail para receber um código de acesso seguro.
            </p>
            <form onSubmit={handleSendOtp} className="login-form">
              {error && <div className="login-error">{error}</div>}
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
              <button
                type="submit"
                className="btn-login-primary"
                disabled={loading || !email.trim()}
              >
                {loading ? "Enviando..." : "Enviar código"}
              </button>
            </form>
          </>
        ) : (
          <>
            <p className="login-description">
              Enviamos um código para <strong>{email}</strong>
            </p>
            <form onSubmit={handleVerifyOtp} className="login-form">
              {error && <div className="login-error">{error}</div>}
              <div className="login-field">
                <label htmlFor="login-code">Código de verificação</label>
                <input
                  id="login-code"
                  ref={codeRef}
                  type="text"
                  inputMode="numeric"
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
                  placeholder="Digite o código recebido"
                  autoComplete="one-time-code"
                  style={{ textAlign: "center", letterSpacing: "4px", fontSize: "1.2rem", fontWeight: 600 }}
                />
              </div>
              <button
                type="submit"
                className="btn-login-primary"
                disabled={loading || code.trim().length < 6}
              >
                {loading ? "Verificando..." : "Verificar"}
              </button>
              <div className="otp-actions">
                <button
                  type="button"
                  className="btn-resend"
                  onClick={handleResend}
                  disabled={countdown > 0}
                >
                  {countdown > 0 ? `Reenviar em ${countdown}s` : "Reenviar código"}
                </button>
                <button
                  type="button"
                  className="btn-back"
                  onClick={() => { setStep("email"); setCode(""); setError(""); }}
                >
                  ← Trocar e-mail
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
