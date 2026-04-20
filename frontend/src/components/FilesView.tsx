"use client";

import { useState, useEffect } from "react";
import { FileItem } from "@/types";
import { getFiles, deleteFile, standbyFile } from "@/lib/api";

export default function FilesView() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [confirmAction, setConfirmAction] = useState<{ filename: string; type: "delete" | "standby" } | null>(null);

  const fetchFiles = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await getFiles();
      setFiles(data.files);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar arquivos");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const handleAction = async (filename: string, type: "delete" | "standby") => {
    setActionLoading(filename);
    try {
      if (type === "delete") {
        await deleteFile(filename);
      } else {
        await standbyFile(filename);
      }
      setConfirmAction(null);
      await fetchFiles();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro na operação");
    } finally {
      setActionLoading(null);
    }
  };

  const getFileIcon = (ext: string) => {
    switch (ext) {
      case ".pdf": return "📄";
      case ".png": case ".jpg": case ".jpeg": case ".webp": return "🖼️";
      case ".mp4": return "🎬";
      case ".mp3": case ".wav": return "🎵";
      default: return "📎";
    }
  };

  if (loading) {
    return (
      <div className="files-view">
        <div className="analytics-loading">
          <div className="loading-spinner" />
          <p>Carregando arquivos...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="files-view">
      <div className="files-header">
        <h2>📂 Arquivos de Treinamento</h2>
        <span className="files-count">{files.length} arquivos</span>
      </div>

      {error && <div className="files-error">❌ {error}</div>}

      {/* Confirmation modal */}
      {confirmAction && (
        <div className="confirm-overlay" onClick={() => setConfirmAction(null)}>
          <div className="confirm-modal" onClick={(e) => e.stopPropagation()}>
            <h3>{confirmAction.type === "delete" ? "⚠️ Excluir Permanentemente" : "⏸️ Desativar Arquivo"}</h3>
            <p>
              {confirmAction.type === "delete"
                ? `Tem certeza que deseja excluir "${confirmAction.filename}"? Esta ação é irreversível — o arquivo será removido do disco e do Pinecone.`
                : `Desativar "${confirmAction.filename}" da base de treinamento? O arquivo será mantido no disco mas seus vetores serão removidos do Pinecone.`
              }
            </p>
            <div className="confirm-actions">
              <button className="btn-cancel" onClick={() => setConfirmAction(null)}>Cancelar</button>
              <button
                className={confirmAction.type === "delete" ? "btn-danger" : "btn-warning"}
                onClick={() => handleAction(confirmAction.filename, confirmAction.type)}
                disabled={actionLoading === confirmAction.filename}
              >
                {actionLoading === confirmAction.filename
                  ? "Processando..."
                  : confirmAction.type === "delete" ? "Excluir" : "Desativar"
                }
              </button>
            </div>
          </div>
        </div>
      )}

      {files.length === 0 ? (
        <div className="analytics-empty">Nenhum arquivo encontrado.</div>
      ) : (
        <div className="files-list">
          {files.map((file) => (
            <div key={file.path} className="file-item">
              <span className="file-icon">{getFileIcon(file.extension)}</span>
              <div className="file-info">
                <span className="file-name">{file.name}</span>
                <span className="file-meta">{file.size_mb} MB • {file.modified?.slice(0, 10)}</span>
              </div>
              <div className="file-actions">
                <button
                  className="btn-file-standby"
                  title="Desativar da base de treinamento"
                  onClick={() => setConfirmAction({ filename: file.name, type: "standby" })}
                  disabled={actionLoading !== null}
                >
                  ⏸️
                </button>
                <button
                  className="btn-file-delete"
                  title="Excluir permanentemente"
                  onClick={() => setConfirmAction({ filename: file.name, type: "delete" })}
                  disabled={actionLoading !== null}
                >
                  🗑️
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
