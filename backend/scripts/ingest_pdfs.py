"""
ingest_pdfs.py — Script CLI para ingerir PDFs diretamente no Pinecone.
Uso: python scripts/ingest_pdfs.py caminho/do/arquivo.pdf [outro.pdf ...]

Pode ser executado de dentro da pasta backend/:
  python scripts/ingest_pdfs.py data/documentos/novo_catalogo.pdf
"""

import sys
import os

# Adiciona o diretorio backend/ ao path para importar os modulos da app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ingest import ingest_pdf_chunked
from app.services.pinecone_db import init_index, upsert_vectors


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/ingest_pdfs.py <arquivo1.pdf> [arquivo2.pdf ...]")
        sys.exit(1)

    pdf_paths = sys.argv[1:]

    print("=" * 50)
    print("Hard Educacao — Ingestao de PDFs")
    print("=" * 50)

    # Inicializa Pinecone
    print("\n[1/3] Conectando ao Pinecone...")
    init_index()
    print("      Conectado!")

    total_vectors = 0

    for pdf_path in pdf_paths:
        if not os.path.exists(pdf_path):
            print(f"\n[ERRO] Arquivo nao encontrado: {pdf_path}")
            continue

        if not pdf_path.lower().endswith(".pdf"):
            print(f"\n[ERRO] Nao e um PDF: {pdf_path}")
            continue

        filename = os.path.basename(pdf_path)
        size_mb = round(os.path.getsize(pdf_path) / (1024 * 1024), 2)

        print(f"\n[2/3] Processando: {filename} ({size_mb} MB)")
        print(f"      Extraindo texto e criando chunks...")

        try:
            vectors = ingest_pdf_chunked(pdf_path, filename, size_mb)
            print(f"      {len(vectors)} chunks criados")

            print(f"[3/3] Enviando para o Pinecone...")
            upsert_vectors(vectors)
            print(f"      {len(vectors)} vetores inseridos com sucesso!")

            total_vectors += len(vectors)

        except Exception as e:
            print(f"      [ERRO] Falha ao processar {filename}: {e}")

    print(f"\n{'=' * 50}")
    print(f"Concluido! {total_vectors} vetores inseridos no total.")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
