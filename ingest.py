"""
ingest.py — Pipeline de ingestão de documentos, imagens e vídeos.

Para PDFs: extrai texto, fatia em chunks e gera um embedding por chunk.
Para outros: gera um embedding por arquivo inteiro.
"""

import os
import hashlib
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from config import SUPPORTED_EXTENSIONS
from embeddings import embed_file, embed_text
from pinecone_db import init_index, upsert_vectors
from chunker import chunk_pdf, get_pdf_info

console = Console()


def _generate_id(file_path: str, chunk_index: int | None = None) -> str:
    """Gera um ID único baseado no caminho do arquivo e chunk."""
    base = file_path
    if chunk_index is not None:
        base = f"{file_path}::chunk::{chunk_index}"
    return hashlib.md5(base.encode("utf-8")).hexdigest()


def _get_file_type_label(extension: str) -> str:
    labels = {
        ".pdf": "📄 PDF", ".png": "🖼️ Imagem PNG",
        ".jpg": "🖼️ Imagem JPEG", ".jpeg": "🖼️ Imagem JPEG",
        ".mp4": "🎬 Vídeo MP4", ".mp3": "🎵 Áudio MP3",
        ".wav": "🎵 Áudio WAV", ".webp": "🖼️ Imagem WebP",
    }
    return labels.get(extension, "📁 Arquivo")


def scan_directory(directory: str) -> list[dict]:
    """Escaneia um diretório em busca de arquivos suportados."""
    files = []
    dir_path = Path(directory)
    if not dir_path.exists():
        console.print(f"[red]❌ Diretório não encontrado: {directory}[/red]")
        return files

    for file_path in dir_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            ext = file_path.suffix.lower()
            stat = file_path.stat()
            files.append({
                "path": str(file_path.resolve()),
                "name": file_path.name,
                "extension": ext,
                "mime_type": SUPPORTED_EXTENSIONS[ext],
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "type_label": _get_file_type_label(ext),
            })
    return files


def display_files_table(files: list[dict]) -> None:
    """Exibe tabela formatada dos arquivos encontrados."""
    table = Table(title="📂 Arquivos Encontrados", show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Tipo", width=16)
    table.add_column("Nome do Arquivo", style="cyan", max_width=50)
    table.add_column("Tamanho", justify="right", style="green")

    for i, f in enumerate(files, 1):
        table.add_row(str(i), f["type_label"], f["name"], f"{f['size_mb']} MB")
    console.print(table)


def _ingest_pdf_chunked(file_info: dict) -> list[dict]:
    """
    Ingere um PDF usando chunking: extrai texto, fatia e gera embedddings por chunk.

    Returns:
        Lista de vetores prontos para o Pinecone.
    """
    filepath = file_info["path"]
    filename = file_info["name"]

    # Verifica se o PDF tem texto extraível
    pdf_info = get_pdf_info(filepath)

    if not pdf_info["has_text"]:
        # PDF sem texto (só imagens) — fallback para embedding de arquivo inteiro
        console.print(f"  [yellow]⚠️ {filename}: PDF sem texto, usando embedding de arquivo[/yellow]")
        embedding = embed_file(filepath, "application/pdf")
        return [{
            "id": _generate_id(filepath),
            "values": embedding,
            "metadata": {
                "filename": filename,
                "filepath": filepath,
                "file_type": ".pdf",
                "mime_type": "application/pdf",
                "size_mb": file_info["size_mb"],
                "type_label": "PDF",
                "content_type": "file_embedding",
                "text": f"[PDF sem texto extraível: {filename}]",
            },
        }]

    # Extrai chunks do PDF
    chunks = chunk_pdf(filepath)

    if not chunks:
        console.print(f"  [yellow]⚠️ {filename}: Nenhum chunk gerado, usando embedding de arquivo[/yellow]")
        embedding = embed_file(filepath, "application/pdf")
        return [{
            "id": _generate_id(filepath),
            "values": embedding,
            "metadata": {
                "filename": filename,
                "filepath": filepath,
                "file_type": ".pdf",
                "mime_type": "application/pdf",
                "size_mb": file_info["size_mb"],
                "type_label": "PDF",
                "content_type": "file_embedding",
                "text": f"[PDF com pouco texto: {filename}]",
            },
        }]

    console.print(
        f"  [cyan]📑 {filename}: {pdf_info['page_count']} páginas → {len(chunks)} chunks[/cyan]"
    )

    vectors = []
    for chunk in chunks:
        # Gera embedding do texto do chunk
        embedding = embed_text(chunk["text"], task_type="RETRIEVAL_DOCUMENT")

        # Trunca texto para metadados do Pinecone (máx ~40KB por registro)
        text_for_metadata = chunk["text"][:8000]

        page_label = f"p.{chunk['page_start']}"
        if chunk["page_end"] != chunk["page_start"]:
            page_label = f"p.{chunk['page_start']}-{chunk['page_end']}"

        vectors.append({
            "id": _generate_id(filepath, chunk["chunk_index"]),
            "values": embedding,
            "metadata": {
                "filename": filename,
                "filepath": filepath,
                "file_type": ".pdf",
                "mime_type": "application/pdf",
                "size_mb": file_info["size_mb"],
                "type_label": f"PDF {page_label}",
                "content_type": "text_chunk",
                "chunk_index": chunk["chunk_index"],
                "page_start": chunk["page_start"],
                "page_end": chunk["page_end"],
                "word_count": chunk["word_count"],
                "text": text_for_metadata,
            },
        })

    return vectors


def _ingest_file_whole(file_info: dict) -> list[dict]:
    """Ingere um arquivo não-PDF como embedding de arquivo inteiro."""
    filepath = file_info["path"]
    embedding = embed_file(filepath, file_info["mime_type"])

    return [{
        "id": _generate_id(filepath),
        "values": embedding,
        "metadata": {
            "filename": file_info["name"],
            "filepath": filepath,
            "file_type": file_info["extension"],
            "mime_type": file_info["mime_type"],
            "size_mb": file_info["size_mb"],
            "type_label": file_info["type_label"],
            "content_type": "file_embedding",
            "text": f"[{file_info['type_label']}: {file_info['name']}]",
        },
    }]


def ingest_directory(directory: str) -> dict:
    """
    Pipeline completo de ingestão com chunking para PDFs.
    """
    console.print(f"\n[bold blue]🚀 Iniciando ingestão do diretório:[/bold blue] {directory}\n")

    files = scan_directory(directory)
    if not files:
        console.print("[yellow]⚠️  Nenhum arquivo suportado encontrado.[/yellow]")
        return {"total": 0, "success": 0, "errors": 0, "chunks": 0}

    display_files_table(files)
    console.print(f"\n[bold]Total: {len(files)} arquivo(s) para processar[/bold]\n")

    console.print("[bold blue]📡 Conectando ao Pinecone...[/bold blue]")
    init_index()
    console.print()

    all_vectors = []
    errors = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Processando arquivos...", total=len(files))

        for file_info in files:
            try:
                progress.update(
                    task,
                    description=f"Processando: {file_info['name'][:40]}..."
                )

                if file_info["extension"] == ".pdf":
                    vectors = _ingest_pdf_chunked(file_info)
                else:
                    vectors = _ingest_file_whole(file_info)

                all_vectors.extend(vectors)

            except Exception as e:
                errors.append({"file": file_info["name"], "error": str(e)})
                console.print(f"[red]  ❌ Erro em '{file_info['name']}': {e}[/red]")

            progress.advance(task)

    # Upsert no Pinecone
    if all_vectors:
        console.print(
            f"\n[bold blue]📤 Enviando {len(all_vectors)} vetor(es) para o Pinecone...[/bold blue]"
        )
        upserted = upsert_vectors(all_vectors)
        console.print(f"[green]✅ {upserted} vetor(es) inseridos com sucesso![/green]")

    stats = {
        "total_files": len(files),
        "total_vectors": len(all_vectors),
        "success_files": len(files) - len(errors),
        "errors": len(errors),
    }

    console.print(f"\n[bold]📊 Resumo da Ingestão:[/bold]")
    console.print(f"   Arquivos processados: {stats['total_files']}")
    console.print(f"   Vetores gerados: [cyan]{stats['total_vectors']}[/cyan]")
    console.print(f"   ✅ Sucesso: [green]{stats['success_files']}[/green]")
    if errors:
        console.print(f"   ❌ Erros: [red]{stats['errors']}[/red]")
        for err in errors:
            console.print(f"      - {err['file']}: {err['error']}")

    return stats
