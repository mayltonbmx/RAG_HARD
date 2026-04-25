"use client";

interface WelcomeScreenProps {
  onSuggestionClick: (question: string) => void;
}

const suggestions = [
  { emoji: "📄", text: "Explorar a base de conhecimento", question: "O que há disponível na base de conhecimento?" },
  { emoji: "🔍", text: "Pesquisar documentos técnicos", question: "Quais documentos técnicos estão disponíveis?" },
  { emoji: "💡", text: "Tirar dúvidas especializadas", question: "Como posso obter respostas especializadas sobre os conteúdos?" },
  { emoji: "📊", text: "Resumir informações", question: "Faça um resumo dos principais temas abordados nos documentos." },
];

export default function WelcomeScreen({ onSuggestionClick }: WelcomeScreenProps) {
  return (
    <div className="welcome-screen">
      <div className="welcome-icon">⬡</div>
      <h2>Olá! Sou o assistente da FonteCerta</h2>
      <p>
        Faça perguntas sobre os documentos e conteúdos da base de conhecimento.
        Eu busco nos documentos indexados e respondo com inteligência.
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
