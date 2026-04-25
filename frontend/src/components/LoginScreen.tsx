"use client";

import { useState, useRef, useEffect } from "react";
import { getSupabaseBrowser } from "@/lib/supabase-browser";

type Step = "email" | "otp";

export default function LoginScreen() {
  const [step, setStep] = useState<Step>("email");
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const supabase = getSupabaseBrowser();

  // Countdown timer for resend
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
        options: {
          shouldCreateUser: true,
        },
      });

      if (error) throw error;

      setStep("otp");
      setCountdown(60);
      // Focus first OTP input
      setTimeout(() => inputRefs.current[0]?.focus(), 100);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao enviar código.");
    } finally {
      setLoading(false);
    }
  };

  const handleOtpChange = (index: number, value: string) => {
    if (value.length > 1) {
      // Handle paste of full code
      const digits = value.replace(/\D/g, "").slice(0, 6).split("");
      const newOtp = [...otp];
      digits.forEach((d, i) => {
        if (index + i < 6) newOtp[index + i] = d;
      });
      setOtp(newOtp);
      const nextIndex = Math.min(index + digits.length, 5);
      inputRefs.current[nextIndex]?.focus();
      return;
    }

    const digit = value.replace(/\D/g, "");
    const newOtp = [...otp];
    newOtp[index] = digit;
    setOtp(newOtp);

    if (digit && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    const code = otp.join("");
    if (code.length !== 6 || loading) return;

    setLoading(true);
    setError("");

    try {
      const { error } = await supabase.auth.verifyOtp({
        email: email.trim(),
        token: code,
        type: "email",
      });

      if (error) throw error;

      // Auth state change will trigger redirect via middleware
      window.location.href = "/";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Código inválido.");
      setOtp(["", "", "", "", "", ""]);
      inputRefs.current[0]?.focus();
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (countdown > 0) return;
    setOtp(["", "", "", "", "", ""]);
    setError("");
    setLoading(true);

    try {
      const { error } = await supabase.auth.signInWithOtp({
        email: email.trim(),
        options: { shouldCreateUser: true },
      });
      if (error) throw error;
      setCountdown(60);
      inputRefs.current[0]?.focus();
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
              Enviamos um código de 6 dígitos para <strong>{email}</strong>
            </p>
            <form onSubmit={handleVerifyOtp} className="login-form">
              {error && <div className="login-error">{error}</div>}
              <div className="otp-inputs">
                {otp.map((digit, i) => (
                  <input
                    key={i}
                    ref={(el) => { inputRefs.current[i] = el; }}
                    type="text"
                    inputMode="numeric"
                    maxLength={6}
                    value={digit}
                    onChange={(e) => handleOtpChange(i, e.target.value)}
                    onKeyDown={(e) => handleOtpKeyDown(i, e)}
                    className="otp-input"
                    autoComplete="one-time-code"
                  />
                ))}
              </div>
              <button
                type="submit"
                className="btn-login-primary"
                disabled={loading || otp.join("").length !== 6}
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
                  {countdown > 0
                    ? `Reenviar em ${countdown}s`
                    : "Reenviar código"}
                </button>
                <button
                  type="button"
                  className="btn-back"
                  onClick={() => {
                    setStep("email");
                    setOtp(["", "", "", "", "", ""]);
                    setError("");
                  }}
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
