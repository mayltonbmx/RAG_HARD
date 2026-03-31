"use client";

import { signIn } from "next-auth/react";

export default function LoginScreen() {
  return (
    <div className="login-screen">
      <div className="login-card">
        <div className="login-icon">⬡</div>
        <h1>Hard Educação</h1>
        <p className="login-subtitle">Chat Inteligente</p>
        <p className="login-description">
          Acesse com sua conta corporativa Microsoft para consultar
          catálogos, desenhos técnicos e produtos.
        </p>
        <button
          className="btn-microsoft"
          onClick={() => signIn("microsoft-entra-id", { callbackUrl: "/" })}
        >
          <svg className="ms-icon" viewBox="0 0 21 21" xmlns="http://www.w3.org/2000/svg">
            <rect x="1" y="1" width="9" height="9" fill="#f25022" />
            <rect x="1" y="11" width="9" height="9" fill="#00a4ef" />
            <rect x="11" y="1" width="9" height="9" fill="#7fba00" />
            <rect x="11" y="11" width="9" height="9" fill="#ffb900" />
          </svg>
          Entrar com Microsoft
        </button>
        <p className="login-footer">
          Desenvolvido por <strong>Maylton Tavares</strong>
        </p>
      </div>
    </div>
  );
}
