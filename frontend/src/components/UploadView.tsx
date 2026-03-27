"use client";

import { useState, useRef } from "react";
import { uploadFiles } from "@/lib/api";
import { UploadResult } from "@/types";

export default function UploadView() {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<UploadResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = async (files: FileList) => {
    setIsUploading(true);
    setProgress(40);
    setResult(null);

    try {
      const res = await uploadFiles(files);
      setProgress(100);
      setResult(res);
    } catch (err) {
      setResult({ success: [], errors: [{ file: "upload", error: String(err) }] });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="view-content">
      <div className="view-header">
        <h1>Upload de Arquivos</h1>
        <p className="view-subtitle">Adicione documentos, imagens e videos ao banco vetorial</p>
      </div>

      <div
        className={`upload-zone ${isDragOver ? "drag-over" : ""}`}
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragOver(false);
          if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files);
        }}
      >
        <div className="upload-zone-content">
          <div style={{ fontSize: "2.5rem", marginBottom: "12px" }}>📤</div>
          <h3>Arraste arquivos aqui</h3>
          <p>ou clique para selecionar</p>
          <div className="upload-formats">
            {["PDF", "PNG", "JPEG", "MP4", "MP3", "WebP"].map((f) => (
              <span key={f} className="format-tag">{f}</span>
            ))}
          </div>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.png,.jpg,.jpeg,.mp4,.mp3,.wav,.webp"
          hidden
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
        />
      </div>

      {isUploading && (
        <div className="upload-progress">
          <div className="progress-header">
            <span>Gerando embeddings e armazenando...</span>
          </div>
          <div className="progress-bar-track">
            <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
          </div>
        </div>
      )}

      {result && (
        <div className="upload-results">
          {result.success.map((f, i) => (
            <div key={i} className="upload-result-item success">✅ {f} — ingerido com sucesso</div>
          ))}
          {result.errors.map((e, i) => (
            <div key={i} className="upload-result-item error">❌ {e.file}: {e.error}</div>
          ))}
        </div>
      )}
    </div>
  );
}
