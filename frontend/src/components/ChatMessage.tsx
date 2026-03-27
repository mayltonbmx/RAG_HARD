"use client";

import { ChatMessage, SourceItem } from "@/types";
import ReactMarkdown from "react-markdown";

interface ChatMessageProps {
  message: ChatMessage;
}

function getTagClass(fileType: string): string {
  if (fileType === ".pdf") return "tag-pdf";
  if ([".png", ".jpg", ".jpeg", ".webp"].includes(fileType)) return "tag-image";
  if (fileType === ".mp4") return "tag-video";
  return "";
}

function Sources({ sources }: { sources: SourceItem[] }) {
  return (
    <div className="msg-sources">
      <div className="msg-sources-title">📚 DOCUMENTOS CONSULTADOS</div>
      {sources.map((s, i) => (
        <div key={i} className="source-item">
          <span className="source-score">{(s.score * 100).toFixed(1)}%</span>
          <span className={`tag ${getTagClass(s.file_type)}`}>
            {(s.file_type || "").replace(".", "").toUpperCase()}
          </span>
          <span>{s.filename}</span>
        </div>
      ))}
    </div>
  );
}

export default function ChatMessageBubble({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div className={`chat-msg ${isUser ? "user" : "assistant"}`}>
      <div className="msg-avatar">{isUser ? "Eu" : "AI"}</div>
      <div className="msg-content">
        <div className="msg-bubble">
          {isUser ? (
            <p>{message.content}</p>
          ) : (
            <ReactMarkdown>{message.content}</ReactMarkdown>
          )}
        </div>
        {message.sources && message.sources.length > 0 && (
          <Sources sources={message.sources} />
        )}
      </div>
    </div>
  );
}

export function ThinkingIndicator() {
  return (
    <div className="chat-msg assistant">
      <div className="msg-avatar">AI</div>
      <div className="msg-content">
        <div className="thinking-indicator">
          <div className="thinking-dots">
            <span /><span /><span />
          </div>
          Buscando nos documentos e gerando resposta...
        </div>
      </div>
    </div>
  );
}
