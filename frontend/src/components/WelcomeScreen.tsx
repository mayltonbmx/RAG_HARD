"use client";

interface WelcomeScreenProps {
  onSuggestionClick: (question: string) => void;
}

const suggestions = [
  { emoji: "🔩", text: "Linha de autoperfurantes", question: "Me fale sobre a linha de autoperfurantes da Hard" },
  { emoji: "🧴", text: "Linha de selantes", question: "Me fale sobre a linha de selantes da Hard" },
  { emoji: "🔧", text: "Linha de chumbadores químicos e mecânicos", question: "Me fale sobre a linha de chumbadores quimicos e mecanicos da Hard" },
  { emoji: "🏠", text: "Cobertura sem goteiras", question: "Como evitar goteiras na cobertura?" },
];

export default function WelcomeScreen({ onSuggestionClick }: WelcomeScreenProps) {
  return (
    <div className="welcome-screen">
      <div className="welcome-icon">⬡</div>
      <h2>Olá! Sou o assistente da Hard Educação</h2>
      <p>
        Faça perguntas sobre catálogos, desenhos técnicos, fixadores e produtos.
        Eu busco nos documentos e respondo com inteligência.
      </p>
      <div className="welcome-suggestions">
        {suggestions.map((s, i) => (
          <button key={i} className="suggestion-chip" onClick={() => onSuggestionClick(s.question)}>
            {s.emoji} {s.text}
          </button>
        ))}
      </div>
    </div>
  );
}
