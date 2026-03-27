import utf8_fix  # noqa: F401 — Corrige encoding UTF-8 no Windows

"""
test_connection.py — Verifica configuração e conexões com Gemini e Pinecone.

Uso:
    python test_connection.py
"""

from rich.console import Console
from rich.panel import Panel

console = Console()


def test_env_variables() -> bool:
    """Testa se as variáveis de ambiente estão configuradas."""
    console.print("\n[bold]1️⃣  Verificando variáveis de ambiente...[/bold]")
    try:
        from config import (
            GEMINI_API_KEY,
            PINECONE_API_KEY,
            PINECONE_INDEX_NAME,
            EMBEDDING_MODEL,
            EMBEDDING_DIMENSIONS,
        )
        console.print(f"   ✅ GEMINI_API_KEY: {'*' * 8}...{GEMINI_API_KEY[-4:]}")
        console.print(f"   ✅ PINECONE_API_KEY: {'*' * 8}...{PINECONE_API_KEY[-4:]}")
        console.print(f"   ✅ PINECONE_INDEX_NAME: {PINECONE_INDEX_NAME}")
        console.print(f"   ✅ EMBEDDING_MODEL: {EMBEDDING_MODEL}")
        console.print(f"   ✅ EMBEDDING_DIMENSIONS: {EMBEDDING_DIMENSIONS}")
        return True
    except SystemExit:
        console.print("   [red]❌ Variáveis de ambiente não configuradas.[/red]")
        console.print("   [dim]Edite o arquivo .env com suas chaves de API.[/dim]")
        return False


def test_gemini_connection() -> bool:
    """Testa conexão com a API do Gemini."""
    console.print("\n[bold]2️⃣  Testando conexão com Gemini...[/bold]")
    try:
        from embeddings import embed_text
        embedding = embed_text("Teste de conexão com Gemini Embedding 2")
        console.print(f"   ✅ Embedding gerado com sucesso!")
        console.print(f"   📐 Dimensões: {len(embedding)}")
        console.print(f"   📊 Primeiros 5 valores: {embedding[:5]}")
        return True
    except Exception as e:
        console.print(f"   [red]❌ Erro na conexão com Gemini: {e}[/red]")
        return False


def test_pinecone_connection() -> bool:
    """Testa conexão com o Pinecone."""
    console.print("\n[bold]3️⃣  Testando conexão com Pinecone...[/bold]")
    try:
        from pinecone_db import init_index, get_stats
        init_index()
        stats = get_stats()
        console.print(f"   ✅ Conexão com Pinecone OK!")
        console.print(f"   📊 Stats: {stats}")
        return True
    except Exception as e:
        console.print(f"   [red]❌ Erro na conexão com Pinecone: {e}[/red]")
        return False


def main() -> None:
    console.print(Panel(
        "[bold cyan]🔧 Teste de Conexões — RAG Multimodal[/bold cyan]\n"
        "Verificando ambiente, Gemini e Pinecone...",
        border_style="cyan",
    ))

    results = {
        "Variáveis de Ambiente": test_env_variables(),
        "Gemini API": test_gemini_connection(),
        "Pinecone": test_pinecone_connection(),
    }

    console.print("\n" + "=" * 50)
    console.print("[bold]📋 Resumo dos Testes:[/bold]\n")
    all_passed = True
    for name, passed in results.items():
        status = "[green]✅ OK[/green]" if passed else "[red]❌ FALHOU[/red]"
        console.print(f"   {name}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        console.print("\n[bold green]🎉 Tudo pronto! Rode 'python main.py ingest' para começar.[/bold green]\n")
    else:
        console.print("\n[bold red]⚠️  Corrija os erros acima antes de continuar.[/bold red]\n")


if __name__ == "__main__":
    main()
