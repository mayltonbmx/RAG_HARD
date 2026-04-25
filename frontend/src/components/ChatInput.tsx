"use client";

import { useRef, useEffect } from "react";

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  disabled: boolean;
}

export default function ChatInput({ value, onChange, onSend, disabled }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 160) + "px";
    }
  }, [value]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="chat-input-area">
      <div className="chat-input-box">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Faça sua pergunta ao especialista..."
          rows={1}
          disabled={disabled}
        />
        <button className="btn-send" onClick={onSend} disabled={disabled || !value.trim()}>
          ➤
        </button>
      </div>
      <div className="chat-footer">
        <p className="chat-disclaimer">
          Respostas geradas por IA com base nos documentos indexados. Verifique informações críticas.
        </p>
        <p className="chat-author">
          Desenvolvido por <strong>Maylton Tavares</strong>
        </p>
      </div>
    </div>
  );
}
