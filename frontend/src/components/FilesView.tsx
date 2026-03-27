"use client";

import { useState, useEffect } from "react";
import { getFiles } from "@/lib/api";
import { FileItem } from "@/types";

export default function FilesView() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getFiles()
      .then((data) => setFiles(data.files))
      .catch(() => setFiles([]))
      .finally(() => setLoading(false));
  }, []);

  const getIcon = (ext: string) => {
    const icons: Record<string, string> = {
      ".pdf": "📄", ".png": "🖼️", ".jpg": "🖼️", ".jpeg": "🖼️",
      ".webp": "🖼️", ".mp4": "🎬", ".mp3": "🎵",
    };
    return icons[ext] || "📁";
  };

  if (loading) return <div className="loading-container"><div className="loading-spinner" /><p>Carregando...</p></div>;

  return (
    <div className="view-content">
      <div className="view-header">
        <h1>Arquivos no Banco</h1>
        <p className="view-subtitle">Documentos disponiveis para busca semantica</p>
      </div>
      <div className="files-grid">
        {files.length === 0 ? (
          <div className="no-results" style={{ gridColumn: "1 / -1" }}>
            <h3>Nenhum arquivo</h3><p>Use Upload para adicionar.</p>
          </div>
        ) : (
          files.map((f, i) => (
            <div key={i} className="file-card">
              <div className="file-card-icon">{getIcon(f.extension)}</div>
              <div className="file-card-name">{f.name}</div>
              <div className="file-card-meta">
                <span className="tag">{f.extension.replace(".", "").toUpperCase()}</span>
                <span>{f.size_mb} MB</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
