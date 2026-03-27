import utf8_fix  # noqa: F401

"""
app.py — Aplicação Web RAG Chat com Gemini + Pinecone.
"""

import os
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

from config import SUPPORTED_EXTENSIONS, EMBEDDING_DIMENSIONS, EMBEDDING_MODEL
from embeddings import embed_query, embed_file
from pinecone_db import init_index, upsert_vectors, search as pinecone_search, get_stats
from ingest import scan_directory, _generate_id
from chat import chat as rag_chat

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "data")

# Garante que o índice existe ao iniciar
init_index()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """API de chat RAG — Busca contexto + gera resposta via Gemini."""
    try:
        data = request.get_json()
        message = data.get("message", "").strip()
        history = data.get("history", [])
        top_k = data.get("top_k", 5)

        if not message:
            return jsonify({"error": "Mensagem vazia."}), 400

        result = rag_chat(message=message, history=history, top_k=top_k)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/search", methods=["POST"])
def api_search():
    """API de busca semântica (retorna apenas documentos)."""
    try:
        data = request.get_json()
        query = data.get("query", "").strip()
        top_k = data.get("top_k", 5)
        file_type = data.get("file_type")

        if not query:
            return jsonify({"error": "Consulta vazia."}), 400

        query_vector = embed_query(query)
        filter_dict = None
        if file_type and file_type != "all":
            filter_dict = {"file_type": {"$eq": file_type}}

        results = pinecone_search(
            query_vector=query_vector,
            top_k=top_k,
            filter_dict=filter_dict,
        )
        return jsonify({"results": results, "query": query})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/upload", methods=["POST"])
def api_upload():
    """Upload e ingestão de arquivos."""
    try:
        if "files" not in request.files:
            return jsonify({"error": "Nenhum arquivo enviado."}), 400

        files = request.files.getlist("files")
        results = {"success": [], "errors": []}

        for file in files:
            if not file.filename:
                continue

            filename = secure_filename(file.filename)
            ext = Path(filename).suffix.lower()

            if ext not in SUPPORTED_EXTENSIONS:
                results["errors"].append({"file": filename, "error": f"Tipo não suportado: {ext}"})
                continue

            subfolder = "documentos" if ext == ".pdf" else \
                        "imagens" if ext in (".png", ".jpg", ".jpeg", ".webp") else \
                        "videos" if ext == ".mp4" else "documentos"

            save_dir = os.path.join(app.config["UPLOAD_FOLDER"], subfolder)
            os.makedirs(save_dir, exist_ok=True)
            filepath = os.path.join(save_dir, filename)
            file.save(filepath)

            try:
                mime_type = SUPPORTED_EXTENSIONS[ext]
                embedding = embed_file(filepath, mime_type)
                vector = {
                    "id": _generate_id(filepath),
                    "values": embedding,
                    "metadata": {
                        "filename": filename, "filepath": filepath,
                        "file_type": ext, "mime_type": mime_type,
                        "size_mb": round(os.path.getsize(filepath) / (1024 * 1024), 2),
                        "type_label": _get_type_label(ext),
                    },
                }
                upsert_vectors([vector])
                results["success"].append(filename)
            except Exception as e:
                results["errors"].append({"file": filename, "error": str(e)})

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stats")
def api_stats():
    try:
        stats = get_stats()
        files = scan_directory(app.config["UPLOAD_FOLDER"])
        return jsonify({
            "total_vectors": stats.get("total_vector_count", 0),
            "dimension": stats.get("dimension", EMBEDDING_DIMENSIONS),
            "index_fullness": stats.get("index_fullness", 0),
            "model": EMBEDDING_MODEL,
            "total_files": len(files),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/files")
def api_files():
    try:
        files = scan_directory(app.config["UPLOAD_FOLDER"])
        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _get_type_label(ext):
    labels = {
        ".pdf": "PDF", ".png": "Imagem PNG", ".jpg": "Imagem JPEG",
        ".jpeg": "Imagem JPEG", ".mp4": "Vídeo MP4", ".mp3": "Áudio MP3",
        ".wav": "Áudio WAV", ".webp": "Imagem WebP",
    }
    return labels.get(ext, "Arquivo")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
