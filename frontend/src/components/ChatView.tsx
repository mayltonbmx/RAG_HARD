"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { ChatMessage, SourceItem } from "@/types";
import { sendChatStream } from "@/lib/api";
import ChatMessageBubble, { ThinkingIndicator } from "./ChatMessage";
import ChatInput from "./ChatInput";
import WelcomeScreen from "./WelcomeScreen";

export default function ChatView() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, isStreaming, scrollToBottom]);

  const handleSend = async (text?: string) => {
    const message = (text || input).trim();
    if (!message || isLoading || isStreaming) return;

    const userMsg: ChatMessage = { role: "user", content: message };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const history = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      // Cria mensagem do assistente vazia para streaming
      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: "",
        sources: [],
      };

      setIsLoading(false);
      setIsStreaming(true);
      setMessages((prev) => [...prev, assistantMsg]);

      let fullContent = "";

      await sendChatStream(
        { message, history, top_k: 8 },
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
      const errorMsg: ChatMessage = {
        role: "assistant",
        content: `❌ Erro: ${err instanceof Error ? err.message : "Erro desconhecido"}`,
      };
      setMessages((prev) => {
        // Remove empty assistant message if exists
        const cleaned = prev.filter((m, i) => !(i === prev.length - 1 && m.role === "assistant" && !m.content));
        return [...cleaned, errorMsg];
      });
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
    }
  };

  return (
    <div className="chat-wrapper">
      <div className="chat-messages">
        {messages.length === 0 && !isLoading ? (
          <WelcomeScreen onSuggestionClick={(q) => handleSend(q)} />
        ) : (
          <>
            {messages.map((msg, i) => (
              <ChatMessageBubble key={i} message={msg} />
            ))}
            {isLoading && <ThinkingIndicator />}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>
      <ChatInput value={input} onChange={setInput} onSend={() => handleSend()} disabled={isLoading || isStreaming} />
    </div>
  );
}

