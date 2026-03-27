import utf8_fix  # noqa: F401 — Corrige encoding UTF-8 no Windows

"""
main.py — CLI principal do RAG Multimodal.

Uso:
    python main.py ingest [--dir CAMINHO]    Ingere arquivos do diretório
    python main.py search "sua consulta"     Busca semântica
    python main.py stats                     Estatísticas do índice
"""

import argparse
import sys

from rich.console import Console
from rich.panel import Panel

console = Console()

BANNER = """
[bold cyan]╔══════════════════════════════════════════════════╗
║          🧠 RAG Multimodal — Hard CMP            ║
║    Gemini Embedding 2 + Pinecone Vector DB       ║
╚══════════════════════════════════════════════════╝[/bold cyan]
"""


def cmd_ingest(args: argparse.Namespace) -> None:
    """Comando de ingestão de documentos."""
    from ingest import ingest_directory
    ingest_directory(args.dir)


def cmd_search(args: argparse.Namespace) -> None:
    """Comando de busca semântica."""
    from search import search
    search(
        query=args.query,
        top_k=args.top_k,
        file_type=args.type,
    )


def cmd_stats(args: argparse.Namespace) -> None:
    """Comando de estatísticas do índice."""
    from pinecone_db import get_stats
    stats = get_stats()

    console.print("\n[bold blue]📊 Estatísticas do Índice Pinecone[/bold blue]\n")
    console.print(Panel(str(stats), title="Index Stats", border_style="blue"))


def main() -> None:
    console.print(BANNER)

    parser = argparse.ArgumentParser(
        description="RAG Multimodal — Gemini Embedding 2 + Pinecone",
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # --- ingest ---
    ingest_parser = subparsers.add_parser(
        "ingest",
        help="Ingere arquivos de um diretório no banco vetorial",
    )
    ingest_parser.add_argument(
        "--dir",
        type=str,
        default="./data",
        help="Diretório para escanear (default: ./data)",
    )

    # --- search ---
    search_parser = subparsers.add_parser(
        "search",
        help="Busca semântica nos documentos",
    )
    search_parser.add_argument(
        "query",
        type=str,
        help="Texto da consulta de busca",
    )
    search_parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        dest="top_k",
        help="Número de resultados (default: 5)",
    )
    search_parser.add_argument(
        "--type",
        type=str,
        default=None,
        choices=[".pdf", ".png", ".jpg", ".jpeg", ".mp4", ".mp3"],
        help="Filtrar por tipo de arquivo",
    )

    # --- stats ---
    subparsers.add_parser(
        "stats",
        help="Exibe estatísticas do índice Pinecone",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    commands = {
        "ingest": cmd_ingest,
        "search": cmd_search,
        "stats": cmd_stats,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
