"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { ChatMessage, Persona, SourceItem } from "@/types";
import { sendChat, sendChatStream, getPersonas } from "@/lib/api";
import ChatMessageBubble, { ThinkingIndicator } from "./ChatMessage";
import ChatInput from "./ChatInput";
import WelcomeScreen from "./WelcomeScreen";

interface ChatMsg extends ChatMessage {
  personaSwitch?: string; // marca quando houve troca de persona
}

interface ChatViewProps {
  isLoggedIn?: boolean;
}

export default function ChatView({ isLoggedIn = false }: ChatViewProps) {
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Persona state
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [selectedPersona, setSelectedPersona] = useState<string>("");
  const [selectorOpen, setSelectorOpen] = useState(false);
  const selectorRef = useRef<HTMLDivElement>(null);

  // Load personas on mount
  useEffect(() => {
    getPersonas()
      .then((data) => {
        setPersonas(data.personas);
        // Selecionar default apenas entre personas acessíveis
        const accessible = data.personas.filter(
          (p) => p.access_level === "public" || isLoggedIn
        );
        const defaultP = accessible.find((p) => p.is_default);
        if (defaultP) setSelectedPersona(defaultP.id);
        else if (accessible.length > 0) setSelectedPersona(accessible[0].id);
      })
      .catch(() => {
        // Silently fail — chat still works without persona selector
      });
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (selectorRef.current && !selectorRef.current.contains(e.target as Node)) {
        setSelectorOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, isStreaming, scrollToBottom]);

  const currentPersona = personas.find((p) => p.id === selectedPersona);

  function isPersonaAccessible(persona: Persona): boolean {
    if (isLoggedIn) return true;
    return persona.access_level === "public";
  }

  function handlePersonaChange(personaId: string) {
    if (personaId === selectedPersona) {
      setSelectorOpen(false);
      return;
    }

    const newPersona = personas.find((p) => p.id === personaId);
    if (newPersona && !isPersonaAccessible(newPersona)) return; // bloqueado
    setSelectedPersona(personaId);
    setSelectorOpen(false);

    // Insere divisor visual se já tem mensagens
    if (messages.length > 0 && newPersona) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "",
          personaSwitch: newPersona.name,
        },
      ]);
    }
  }

  /** Fallback: usa endpoint clássico /api/chat quando streaming não está disponível */
  const handleFallbackChat = async (
    message: string,
    history: { role: string; content: string }[]
  ) => {
    const response = await sendChat({
      message,
      history,
      top_k: 8,
      persona_id: selectedPersona || undefined,
    });
    const assistantMsg: ChatMsg = {
      role: "assistant",
      content: response.answer,
      sources: response.sources,
    };
    setMessages((prev) => [...prev, assistantMsg]);
  };

  const handleSend = async (text?: string) => {
    const message = (text || input).trim();
    if (!message || isLoading || isStreaming) return;

    const userMsg: ChatMsg = { role: "user", content: message };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    // Build history (exclui divisores de troca de persona)
    const history = messages
      .filter((m) => !m.personaSwitch)
      .map((m) => ({
        role: m.role,
        content: m.content,
      }));

    try {
      // Tenta streaming primeiro
      const assistantMsg: ChatMsg = {
        role: "assistant",
        content: "",
        sources: [],
      };

      setIsLoading(false);
      setIsStreaming(true);
      setMessages((prev) => [...prev, assistantMsg]);

      let fullContent = "";

      await sendChatStream(
        {
          message,
          history,
          top_k: 8,
          persona_id: selectedPersona || undefined,
        },
        {
          onToken: (token: string) => {
            fullContent += token;
            setMessages((prev) => {
              const updated = [...prev];
              const lastMsg = updated[updated.length - 1];
              if (lastMsg.role === "assistant") {
                updated[updated.length - 1] = {
                  ...lastMsg,
                  content: fullContent,
                };
              }
              return updated;
            });
          },
          onMeta: (meta: { sources: SourceItem[]; model: string; chunks_used: number }) => {
            setMessages((prev) => {
              const updated = [...prev];
              const lastMsg = updated[updated.length - 1];
              if (lastMsg.role === "assistant") {
                updated[updated.length - 1] = {
                  ...lastMsg,
                  sources: meta.sources,
                };
              }
              return updated;
            });
          },
          onError: (error: string) => {
            setMessages((prev) => {
              const updated = [...prev];
              const lastMsg = updated[updated.length - 1];
              if (lastMsg.role === "assistant") {
                updated[updated.length - 1] = {
                  ...lastMsg,
                  content: `❌ Erro: ${error}`,
                };
              }
              return updated;
            });
          },
          onDone: () => {
            setIsStreaming(false);
          },
        }
      );
    } catch (err) {
      // Fallback: se streaming falhar (404, rede), tenta endpoint clássico
      const errorMessage = err instanceof Error ? err.message : "";
      const isStreamingUnavailable = errorMessage.includes("Not Found") ||
        errorMessage.includes("404") ||
        errorMessage.includes("Failed to fetch") ||
        errorMessage.includes("Streaming não suportado");

      if (isStreamingUnavailable) {
        console.warn("Streaming indisponível, usando fallback clássico");
        // Remove mensagem vazia do assistente (do streaming)
        setMessages((prev) => prev.filter((m, i) =>
          !(i === prev.length - 1 && m.role === "assistant" && !m.content)
        ));
        setIsStreaming(false);
        setIsLoading(true);

        try {
          await handleFallbackChat(message, history);
        } catch (fallbackErr) {
          setMessages((prev) => [...prev, {
            role: "assistant" as const,
            content: `❌ Erro: ${fallbackErr instanceof Error ? fallbackErr.message : "Erro desconhecido"}`,
          }]);
        }
      } else {
        setMessages((prev) => {
          const cleaned = prev.filter((m, i) =>
            !(i === prev.length - 1 && m.role === "assistant" && !m.content)
          );
          return [...cleaned, {
            role: "assistant" as const,
            content: `❌ Erro: ${errorMessage || "Erro desconhecido"}`,
          }];
        });
      }
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
    }
  };

  return (
    <div className="chat-wrapper">
      {/* Persona Selector Bar */}
      {personas.length > 0 && (
        <div className="persona-selector-bar">
          <div className="persona-selector" ref={selectorRef}>
            <button
              className="persona-selector-trigger"
              onClick={() => setSelectorOpen(!selectorOpen)}
              disabled={isLoading || isStreaming}
            >
              <span className="selector-avatar">
                {currentPersona?.name?.charAt(0)?.toUpperCase() || "?"}
              </span>
              <span className="selector-info">
                <span className="selector-label">Falar com</span>
                <span className="selector-name">
                  {currentPersona?.name || "Selecione"}
                </span>
              </span>
              <span className={`selector-arrow ${selectorOpen ? "open" : ""}`}>▾</span>
            </button>

            {selectorOpen && (
              <div className="persona-dropdown">
                {personas.map((p) => {
                  const accessible = isPersonaAccessible(p);
                  return (
                    <button
                      key={p.id}
                      className={`persona-dropdown-item ${p.id === selectedPersona ? "active" : ""} ${!accessible ? "locked" : ""}`}
                      onClick={() => accessible && handlePersonaChange(p.id)}
                      disabled={!accessible}
                    >
                      <span className="dropdown-avatar">{p.name.charAt(0).toUpperCase()}</span>
                      <div className="dropdown-info">
                        <span className="dropdown-name">{p.name}</span>
                        <span className="dropdown-desc">{p.description}</span>
                      </div>
                      {!accessible && <span className="dropdown-lock">🔒<small>Assinantes</small></span>}
                      {accessible && p.id === selectedPersona && <span className="dropdown-check">✓</span>}
                      {accessible && p.access_level === "public" && p.id !== selectedPersona && <span className="dropdown-badge free">Free</span>}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      <div className="chat-messages">
        {messages.length === 0 && !isLoading ? (
          <WelcomeScreen onSuggestionClick={(q) => handleSend(q)} />
        ) : (
          <>
            {messages.map((msg, i) =>
              msg.personaSwitch ? (
                <div key={i} className="persona-switch-divider">
                  <div className="divider-line" />
                  <span className="divider-label">🔄 {msg.personaSwitch} entrou na conversa</span>
                  <div className="divider-line" />
                </div>
              ) : (
                <ChatMessageBubble key={i} message={msg} />
              )
            )}
            {isLoading && <ThinkingIndicator />}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>
      <ChatInput value={input} onChange={setInput} onSend={() => handleSend()} disabled={isLoading || isStreaming} />
    </div>
  );
}

