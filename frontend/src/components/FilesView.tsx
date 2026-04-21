"use client";

import { useState, useEffect, useMemo } from "react";
import { FileItem } from "@/types";
import { getFiles, deleteFile, clearFileHistory } from "@/lib/api";

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
    type: "delete" | "clear_history";
  } | null>(null);
  const [searchTerms, setSearchTerms] = useState<Record<FileCategory, string>>({
    documents: "",
    images: "",
    videos: "",
  });
  const [searchOpen, setSearchOpen] = useState<Record<FileCategory, boolean>>({
    documents: false,
    images: false,
    videos: false,
  });

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

  const handleAction = async (filename: string, type: "delete" | "clear_history") => {
    setActionLoading(filename);
    try {
      if (type === "delete") {
        await deleteFile(filename);
      } else if (type === "clear_history") {
        await clearFileHistory(filename);
      }
      setConfirmAction(null);
      await fetchFiles();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro na operação");
    } finally {
      setActionLoading(null);
    }
  };

  // Group and filter files by category
  const grouped = useMemo(() => {
    const result: Record<FileCategory, { active: FileItem[]; deleted: FileItem[] }> = {
      documents: { active: [], deleted: [] },
      images: { active: [], deleted: [] },
      videos: { active: [], deleted: [] },
    };

    for (const file of files) {
      const cat = getCategory(file.extension);
      const term = searchTerms[cat].toLowerCase();

      // Apply search filter
      if (term && !file.name.toLowerCase().includes(term)) {
        continue;
      }

      if (file.status === "deleted") {
        result[cat].deleted.push(file);
      } else {
        result[cat].active.push(file);
      }
    }

    return result;
  }, [files, searchTerms]);

  const totalActive = files.filter((f) => f.status === "active").length;
  const totalDeleted = files.filter((f) => f.status === "deleted").length;

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
          {totalDeleted > 0 && (
            <span className="files-count files-count-deleted">
              <span className="status-dot status-deleted" />
              {totalDeleted} no histórico
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
                ? "⚠️ Excluir da Base de Treinamento"
                : "🗑️ Limpar do Histórico"}
            </h3>
            <p>
              {confirmAction.type === "delete"
                ? `Tem certeza que deseja excluir "${confirmAction.filename}" da base de treinamento? A IA deixará de conhecer este arquivo. O registro ficará no histórico de exclusões.`
                : `Remover "${confirmAction.filename}" do histórico de exclusões?`}
            </p>
            <div className="confirm-actions">
              <button className="btn-cancel" onClick={() => setConfirmAction(null)}>
                Cancelar
              </button>
              <button
                className={confirmAction.type === "delete" ? "btn-danger" : "btn-warning"}
                onClick={() => handleAction(confirmAction.filename, confirmAction.type)}
                disabled={actionLoading === confirmAction.filename}
              >
                {actionLoading === confirmAction.filename
                  ? "Processando..."
                  : confirmAction.type === "delete"
                    ? "Excluir"
                    : "Limpar"}
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
            const totalCat = catFiles.active.length + catFiles.deleted.length;
            const isSearchOpen = searchOpen[cat.key];

            return (
              <div key={cat.key} className="files-column" data-category={cat.key}>
                <div className="column-header" style={{ borderColor: cat.accentColor }}>
                  <div className="column-header-left">
                    <span className="column-icon">{cat.icon}</span>
                    <span className="column-title">{cat.label}</span>
                    <span className="column-count">{catFiles.active.length}</span>
                  </div>
                  <button
                    className={`column-search-toggle ${isSearchOpen ? "active" : ""}`}
                    onClick={() =>
                      setSearchOpen((prev) => ({ ...prev, [cat.key]: !prev[cat.key] }))
                    }
                    title="Pesquisar"
                  >
                    🔍
                  </button>
                </div>

                {isSearchOpen && (
                  <div className="column-search">
                    <input
                      type="text"
                      placeholder="Buscar arquivo..."
                      value={searchTerms[cat.key]}
                      onChange={(e) =>
                        setSearchTerms((prev) => ({ ...prev, [cat.key]: e.target.value }))
                      }
                      autoFocus
                    />
                    {searchTerms[cat.key] && (
                      <button
                        className="search-clear"
                        onClick={() =>
                          setSearchTerms((prev) => ({ ...prev, [cat.key]: "" }))
                        }
                      >
                        ✕
                      </button>
                    )}
                  </div>
                )}

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
                          key={file.name}
                          file={file}
                          accentColor={cat.accentColor}
                          actionLoading={actionLoading}
                          onDelete={() =>
                            setConfirmAction({
                              filename: file.name,
                              type: "delete",
                            })
                          }
                        />
                      ))}
                    </div>
                  )}

                  {/* Deletion history */}
                  {catFiles.deleted.length > 0 && (
                    <div className="column-section column-section-history">
                      <div className="section-label section-label-deleted">
                        <span className="status-dot status-deleted" />
                        Histórico de Exclusão ({catFiles.deleted.length})
                      </div>
                      {catFiles.deleted.map((file) => (
                        <DeletedFileCard
                          key={`deleted-${file.name}-${file.deleted_at}`}
                          file={file}
                          actionLoading={actionLoading}
                          onClearHistory={() =>
                            setConfirmAction({
                              filename: file.name,
                              type: "clear_history",
                            })
                          }
                        />
                      ))}
                    </div>
                  )}

                  {totalCat === 0 && (
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

/* ── Active File Card ── */

interface FileCardProps {
  file: FileItem;
  accentColor: string;
  actionLoading: string | null;
  onDelete: () => void;
}

function FileCard({ file, accentColor, actionLoading, onDelete }: FileCardProps) {
  return (
    <div
      className="file-card-v2"
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
        <span className="file-status-badge badge-active">Ativo</span>
      </div>
      <div className="file-card-actions">
        <button
          className="btn-file-delete"
          title="Excluir da base de treinamento"
          onClick={onDelete}
          disabled={actionLoading !== null}
        >
          🗑️ Excluir
        </button>
      </div>
    </div>
  );
}

/* ── Deleted File Card (History) ── */

interface DeletedFileCardProps {
  file: FileItem;
  actionLoading: string | null;
  onClearHistory: () => void;
}

function DeletedFileCard({ file, actionLoading, onClearHistory }: DeletedFileCardProps) {
  const deletedDate = file.deleted_at
    ? new Date(file.deleted_at).toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      })
    : "";

  return (
    <div className="file-card-deleted">
      <div className="file-card-top">
        <div className="file-card-info">
          <span className="file-card-name file-card-name-deleted" title={file.name}>
            {file.name}
          </span>
          <span className="file-card-meta">
            {file.size_mb} MB
            {file.vectors_count > 0 && ` • ${file.vectors_count} vetores removidos`}
            {deletedDate && ` • excluído em ${deletedDate}`}
          </span>
        </div>
        <button
          className="btn-clear-history"
          title="Remover do histórico"
          onClick={onClearHistory}
          disabled={actionLoading !== null}
        >
          ✕
        </button>
      </div>
    </div>
  );
}
