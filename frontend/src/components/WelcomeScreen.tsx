"use client";

interface WelcomeScreenProps {
  onSuggestionClick: (question: string) => void;
}

const suggestions = [
  { emoji: "🔩", text: "Fixadores autoperfurantes", question: "Quais fixadores autoperfurantes estao disponiveis?" },
  { emoji: "🏠", text: "Coberturas sem goteiras", question: "Como evitar goteiras na cobertura?" },
  { emoji: "📋", text: "Linhas de produtos", question: "Quais sao as linhas de produtos da Hard?" },
  { emoji: "⚙️", text: "Linha ZAPHIR", question: "Me fale sobre a linha ZAPHIR" },
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
