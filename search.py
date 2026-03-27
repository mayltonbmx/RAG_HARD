"""
search.py — Busca semântica multimodal no banco vetorial Pinecone.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from embeddings import embed_query
from pinecone_db import search as pinecone_search

console = Console()


def search(
    query: str,
    top_k: int = 5,
    file_type: str | None = None,
) -> list[dict]:
    """
    Realiza busca semântica no Pinecone.

    Args:
        query: Texto da consulta do usuário.
        top_k: Quantidade de resultados a retornar.
        file_type: Filtrar por tipo de arquivo (ex: '.pdf', '.png').

    Returns:
        Lista de resultados com score e metadados.
    """
    console.print(f"\n[bold blue]🔍 Buscando:[/bold blue] \"{query}\"\n")

    # Gera embedding da consulta
    console.print("[dim]Gerando embedding da consulta...[/dim]")
    query_vector = embed_query(query)

    # Filtro de metadados (opcional)
    filter_dict = None
    if file_type:
        filter_dict = {"file_type": {"$eq": file_type}}

    # Busca no Pinecone
    console.print("[dim]Consultando Pinecone...[/dim]\n")
    results = pinecone_search(
        query_vector=query_vector,
        top_k=top_k,
        filter_dict=filter_dict,
    )

    if not results:
        console.print("[yellow]⚠️  Nenhum resultado encontrado.[/yellow]")
        console.print("[dim]Verifique se os documentos foram ingeridos (python main.py ingest).[/dim]")
        return results

    # Exibe resultados
    display_results(results, query)

    return results


def display_results(results: list[dict], query: str) -> None:
    """Exibe resultados de busca formatados."""
    table = Table(
        title=f"📋 Resultados para: \"{query}\"",
        show_lines=True,
    )
    table.add_column("Rank", style="bold", width=5, justify="center")
    table.add_column("Score", style="magenta", width=8, justify="center")
    table.add_column("Tipo", width=16)
    table.add_column("Arquivo", style="cyan", max_width=50)
    table.add_column("Tamanho", justify="right", style="green", width=10)

    for i, result in enumerate(results, 1):
        meta = result.get("metadata", {})
        score = result.get("score", 0)

        # Barra visual de relevância
        score_color = "green" if score >= 0.8 else "yellow" if score >= 0.5 else "red"

        table.add_row(
            f"#{i}",
            f"[{score_color}]{score:.4f}[/{score_color}]",
            meta.get("type_label", "—"),
            meta.get("filename", "—"),
            f"{meta.get('size_mb', '?')} MB",
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(results)} resultado(s)[/dim]")
