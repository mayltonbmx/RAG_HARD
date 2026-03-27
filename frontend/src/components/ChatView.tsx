"use client";

import { useState, useRef, useEffect } from "react";
import { ChatMessage } from "@/types";
import { sendChat } from "@/lib/api";
import ChatMessageBubble, { ThinkingIndicator } from "./ChatMessage";
import ChatInput from "./ChatInput";
import WelcomeScreen from "./WelcomeScreen";

export default function ChatView() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (text?: string) => {
    const message = (text || input).trim();
    if (!message || isLoading) return;

    const userMsg: ChatMessage = { role: "user", content: message };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const history = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const response = await sendChat({
        message,
        history,
        top_k: 8,
      });

      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: response.answer,
        sources: response.sources,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const errorMsg: ChatMessage = {
        role: "assistant",
        content: `❌ Erro: ${err instanceof Error ? err.message : "Erro desconhecido"}`,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setInput("");
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
      <ChatInput value={input} onChange={setInput} onSend={() => handleSend()} disabled={isLoading} />
    </div>
  );
}

// Export for use in parent
export { type ChatView };
