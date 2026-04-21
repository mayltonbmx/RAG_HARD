"use client";

import { useState, useEffect } from "react";
import { FileItem } from "@/types";
import { getFiles, deleteFile, standbyFile, activateFile } from "@/lib/api";

type FileCategory = "documents" | "images" | "videos";

interface CategoryConfig {
  key: FileCategory;
  label: string;
  icon: string;
  extensions: string[];
  accentColor: string;
}

const CATEGORIES: CategoryConfig[] = [
  {
    key: "documents",
    label: "Documentos",
    icon: "📄",
    extensions: [".pdf"],
    accentColor: "#f87171",
  },
  {
    key: "images",
    label: "Imagens",
    icon: "🖼️",
    extensions: [".png", ".jpg", ".jpeg", ".webp"],
    accentColor: "#34d399",
  },
  {
    key: "videos",
    label: "Vídeos",
    icon: "🎬",
    extensions: [".mp4", ".mp3", ".wav"],
    accentColor: "#fbbf24",
  },
];

function getCategory(ext: string): FileCategory {
  for (const cat of CATEGORIES) {
    if (cat.extensions.includes(ext)) return cat.key;
  }
  return "documents";
}

export default function FilesView() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [confirmAction, setConfirmAction] = useState<{
    filename: string;
    type: "delete" | "standby" | "activate";
    currentStatus: "active" | "standby";
  } | null>(null);

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

  const handleAction = async (filename: string, type: "delete" | "standby" | "activate") => {
    setActionLoading(filename);
    try {
      if (type === "delete") {
        await deleteFile(filename);
      } else if (type === "standby") {
        await standbyFile(filename);
      } else if (type === "activate") {
        await activateFile(filename);
      }
      setConfirmAction(null);
      await fetchFiles();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro na operação");
    } finally {
      setActionLoading(null);
    }
  };

  // Group files by category
  const grouped: Record<FileCategory, { active: FileItem[]; standby: FileItem[] }> = {
    documents: { active: [], standby: [] },
    images: { active: [], standby: [] },
    videos: { active: [], standby: [] },
  };

  for (const file of files) {
    const cat = getCategory(file.extension);
    if (file.status === "active") {
      grouped[cat].active.push(file);
    } else {
      grouped[cat].standby.push(file);
    }
  }

  const totalActive = files.filter((f) => f.status === "active").length;
  const totalStandby = files.filter((f) => f.status === "standby").length;

  if (loading) {
    return (
      <div className="files-view">
        <div className="analytics-loading">
          <div className="loading-spinner" />
          <p>Consultando base de treinamento...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="files-view">
      <div className="files-header">
        <h2>📂 Arquivos de Treinamento</h2>
        <div className="files-header-stats">
          <span className="files-count files-count-active">
            <span className="status-dot status-active" />
            {totalActive} ativos no Pinecone
          </span>
          {totalStandby > 0 && (
            <span className="files-count files-count-standby">
              <span className="status-dot status-standby" />
              {totalStandby} em standby
            </span>
          )}
        </div>
      </div>

      {error && <div className="files-error">❌ {error}</div>}

      {/* Confirmation modal */}
      {confirmAction && (
        <div className="confirm-overlay" onClick={() => setConfirmAction(null)}>
          <div className="confirm-modal" onClick={(e) => e.stopPropagation()}>
            <h3>
              {confirmAction.type === "delete"
                ? "⚠️ Excluir Permanentemente"
                : confirmAction.type === "activate"
                  ? "🔄 Reativar na Base de Treinamento"
                  : "⏸️ Desativar da Base de Treinamento"}
            </h3>
            <p>
              {confirmAction.type === "delete"
                ? `Tem certeza que deseja excluir "${confirmAction.filename}"? Esta ação é irreversível — o arquivo será removido do disco e do Pinecone.`
                : confirmAction.type === "activate"
                  ? `Reativar "${confirmAction.filename}" na base de treinamento? O arquivo será re-processado e seus vetores serão inseridos no Pinecone. Isso consome créditos da API de embeddings.`
                  : `Desativar "${confirmAction.filename}" da base de treinamento? O arquivo será mantido no disco mas seus vetores serão removidos do Pinecone.`}
            </p>
            <div className="confirm-actions">
              <button className="btn-cancel" onClick={() => setConfirmAction(null)}>
                Cancelar
              </button>
              <button
                className={
                  confirmAction.type === "delete"
                    ? "btn-danger"
                    : confirmAction.type === "activate"
                      ? "btn-success"
                      : "btn-warning"
                }
                onClick={() => handleAction(confirmAction.filename, confirmAction.type)}
                disabled={actionLoading === confirmAction.filename}
              >
                {actionLoading === confirmAction.filename
                  ? "Processando..."
                  : confirmAction.type === "delete"
                    ? "Excluir"
                    : confirmAction.type === "activate"
                      ? "Reativar"
                      : "Desativar"}
              </button>
            </div>
          </div>
        </div>
      )}

      {files.length === 0 ? (
        <div className="analytics-empty">Nenhum arquivo encontrado.</div>
      ) : (
        <div className="files-columns">
          {CATEGORIES.map((cat) => {
            const catFiles = grouped[cat.key];
            const total = catFiles.active.length + catFiles.standby.length;

            return (
              <div key={cat.key} className="files-column" data-category={cat.key}>
                <div className="column-header" style={{ borderColor: cat.accentColor }}>
                  <span className="column-icon">{cat.icon}</span>
                  <span className="column-title">{cat.label}</span>
                  <span className="column-count">{total}</span>
                </div>

                <div className="column-content">
                  {/* Active files */}
                  {catFiles.active.length > 0 && (
                    <div className="column-section">
                      <div className="section-label section-label-active">
                        <span className="status-dot status-active" />
                        Ativos ({catFiles.active.length})
                      </div>
                      {catFiles.active.map((file) => (
                        <FileCard
                          key={file.path}
                          file={file}
                          accentColor={cat.accentColor}
                          actionLoading={actionLoading}
                          onStandby={() =>
                            setConfirmAction({
                              filename: file.name,
                              type: "standby",
                              currentStatus: "active",
                            })
                          }
                          onDelete={() =>
                            setConfirmAction({
                              filename: file.name,
                              type: "delete",
                              currentStatus: "active",
                            })
                          }
                          onActivate={undefined}
                        />
                      ))}
                    </div>
                  )}

                  {/* Standby files */}
                  {catFiles.standby.length > 0 && (
                    <div className="column-section">
                      <div className="section-label section-label-standby">
                        <span className="status-dot status-standby" />
                        Em Standby ({catFiles.standby.length})
                      </div>
                      {catFiles.standby.map((file) => (
                        <FileCard
                          key={file.path}
                          file={file}
                          accentColor={cat.accentColor}
                          actionLoading={actionLoading}
                          onStandby={undefined}
                          onDelete={() =>
                            setConfirmAction({
                              filename: file.name,
                              type: "delete",
                              currentStatus: "standby",
                            })
                          }
                          onActivate={() =>
                            setConfirmAction({
                              filename: file.name,
                              type: "activate",
                              currentStatus: "standby",
                            })
                          }
                        />
                      ))}
                    </div>
                  )}

                  {total === 0 && (
                    <div className="column-empty">Nenhum arquivo</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ── File Card sub-component ── */

interface FileCardProps {
  file: FileItem;
  accentColor: string;
  actionLoading: string | null;
  onStandby: (() => void) | undefined;
  onDelete: (() => void) | undefined;
  onActivate: (() => void) | undefined;
}

function FileCard({ file, accentColor, actionLoading, onStandby, onDelete, onActivate }: FileCardProps) {
  const isStandby = file.status === "standby";

  return (
    <div
      className={`file-card-v2 ${isStandby ? "file-standby" : ""}`}
      style={{ "--file-accent": accentColor } as React.CSSProperties}
    >
      <div className="file-card-top">
        <div className="file-card-info">
          <span className="file-card-name" title={file.name}>
            {file.name}
          </span>
          <span className="file-card-meta">
            {file.size_mb} MB
            {file.vectors_count > 0 && ` • ${file.vectors_count} vetores`}
            {file.modified ? ` • ${file.modified.slice(0, 10)}` : ""}
          </span>
        </div>
        <span className={`file-status-badge ${isStandby ? "badge-standby" : "badge-active"}`}>
          {isStandby ? "Standby" : "Ativo"}
        </span>
      </div>
      <div className="file-card-actions">
        {onActivate && (
          <button
            className="btn-file-activate"
            title="Reativar na base de treinamento"
            onClick={onActivate}
            disabled={actionLoading !== null}
          >
            ▶️ Ativar
          </button>
        )}
        {onStandby && (
          <button
            className="btn-file-standby"
            title="Desativar da base de treinamento"
            onClick={onStandby}
            disabled={actionLoading !== null}
          >
            ⏸️ Pausar
          </button>
        )}
        {onDelete && (
          <button
            className="btn-file-delete"
            title="Excluir permanentemente"
            onClick={onDelete}
            disabled={actionLoading !== null}
          >
            🗑️
          </button>
        )}
      </div>
    </div>
  );
}
