"use client";

import { useState, useEffect } from "react";
import { Persona } from "@/types";
import { getPersonas, createPersona, updatePersona, deletePersona } from "@/lib/api";

const ACCESS_LABELS: Record<string, string> = {
  public: "🌐 Público",
  logged_in: "🔑 Logados",
  admin: "🛡️ Admin",
};

const TEMP_LABELS = [
  "Ultra Preciso",
  "Muito Preciso",
  "Preciso",
  "Balanceado-",
  "Balanceado",
  "Balanceado+",
  "Criativo-",
  "Criativo",
  "Muito Criativo",
  "Ultra Criativo",
  "Máx. Criativo",
];

function getTempLabel(val: number): string {
  const idx = Math.round(val * 10);
  return TEMP_LABELS[Math.min(idx, 10)];
}

function getTempColor(val: number): string {
  if (val <= 0.3) return "#34d399";
  if (val <= 0.6) return "#818cf8";
  return "#fbbf24";
}

const EMPTY_FORM: Omit<Persona, "id"> = {
  name: "",
  description: "",
  identity: "",
  rules: [],
  temperature: 0.5,
  access_level: "logged_in",
  is_default: false,
};

export default function PersonasView() {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Editor state
  const [editing, setEditing] = useState<Persona | null>(null);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState<Omit<Persona, "id">>(EMPTY_FORM);
  const [newRule, setNewRule] = useState("");
  const [saving, setSaving] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  useEffect(() => {
    loadPersonas();
  }, []);

  async function loadPersonas() {
    try {
      setLoading(true);
      const data = await getPersonas();
      setPersonas(data.personas);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Erro ao carregar especialistas");
    } finally {
      setLoading(false);
    }
  }

  function openCreate() {
    setEditing(null);
    setForm({ ...EMPTY_FORM });
    setNewRule("");
    setCreating(true);
  }

  function openEdit(persona: Persona) {
    setCreating(false);
    setEditing(persona);
    setForm({
      name: persona.name,
      description: persona.description,
      identity: persona.identity,
      rules: [...persona.rules],
      temperature: persona.temperature,
      access_level: persona.access_level,
      is_default: persona.is_default,
    });
    setNewRule("");
  }

  function closeEditor() {
    setEditing(null);
    setCreating(false);
  }

  function addRule() {
    if (!newRule.trim() || form.rules.length >= 15) return;
    setForm({ ...form, rules: [...form.rules, newRule.trim()] });
    setNewRule("");
  }

  function removeRule(index: number) {
    setForm({ ...form, rules: form.rules.filter((_, i) => i !== index) });
  }

  async function handleSave() {
    if (!form.name.trim()) return;
    setSaving(true);
    try {
      if (editing) {
        await updatePersona(editing.id, form);
      } else {
        await createPersona(form);
      }
      await loadPersonas();
      closeEditor();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Erro ao salvar");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string) {
    try {
      await deletePersona(id);
      setDeleteConfirm(null);
      await loadPersonas();
      if (editing?.id === id) closeEditor();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Erro ao remover");
    }
  }

  const isEditorOpen = creating || editing !== null;

  if (loading) {
    return (
      <div className="personas-view">
        <div className="analytics-loading">
          <div className="loading-spinner" />
          <span>Carregando especialistas...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="personas-view">
      {/* Header */}
      <div className="personas-header">
        <div>
          <h2>Especialistas Virtuais</h2>
          <p className="personas-subtitle">
            Gerencie as personas de IA que interagem com sua equipe
          </p>
        </div>
        <button className="btn-create-persona" onClick={openCreate}>
          + Novo Especialista
        </button>
      </div>

      {error && (
        <div className="personas-error">
          {error}
          <button onClick={() => setError("")} className="btn-dismiss">✕</button>
        </div>
      )}

      {/* Galeria de Cards */}
      <div className="personas-gallery">
        {personas.map((p) => (
          <div
            key={p.id}
            className={`persona-card ${editing?.id === p.id ? "active" : ""}`}
            onClick={() => openEdit(p)}
          >
            <div className="persona-card-header">
              <div className="persona-avatar">
                {p.name.charAt(0).toUpperCase()}
              </div>
              <div className="persona-card-badges">
                {p.is_default && <span className="badge-default">PADRÃO</span>}
                <span className={`badge-access ${p.access_level}`}>
                  {ACCESS_LABELS[p.access_level]}
                </span>
              </div>
            </div>
            <h3 className="persona-card-name">{p.name}</h3>
            <p className="persona-card-desc">{p.description || "Sem descrição"}</p>
            <div className="persona-card-footer">
              <div className="persona-temp-indicator">
                <div
                  className="temp-dot"
                  style={{ background: getTempColor(p.temperature) }}
                />
                <span>{getTempLabel(p.temperature)}</span>
              </div>
              <span className="persona-rules-count">{p.rules.length} regras</span>
            </div>
          </div>
        ))}
      </div>

      {/* Editor / Criador */}
      {isEditorOpen && (
        <div className="persona-editor-overlay" onClick={closeEditor}>
          <div className="persona-editor" onClick={(e) => e.stopPropagation()}>
            <div className="editor-header">
              <h3>{editing ? `Editar: ${editing.name}` : "Novo Especialista"}</h3>
              <button className="btn-close-editor" onClick={closeEditor}>✕</button>
            </div>

            <div className="editor-body">
              {/* Nome e Descrição */}
              <div className="editor-row">
                <label>Nome do Especialista</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="Ex: Engenheiro de Aplicação"
                  maxLength={100}
                />
              </div>

              <div className="editor-row">
                <label>Descrição resumida</label>
                <input
                  type="text"
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="Aparece no menu de seleção do chat"
                  maxLength={300}
                />
              </div>

              {/* Nível de Acesso */}
              <div className="editor-row">
                <label>Nível de Acesso</label>
                <div className="access-selector">
                  {(["public", "logged_in", "admin"] as const).map((level) => (
                    <button
                      key={level}
                      className={`access-option ${form.access_level === level ? "active" : ""}`}
                      onClick={() => setForm({ ...form, access_level: level })}
                    >
                      {ACCESS_LABELS[level]}
                    </button>
                  ))}
                </div>
              </div>

              {/* Identidade */}
              <div className="editor-row">
                <label>
                  Identidade
                  <span className="label-hint">Quem esse especialista é?</span>
                </label>
                <textarea
                  value={form.identity}
                  onChange={(e) => setForm({ ...form, identity: e.target.value })}
                  placeholder="Você é um engenheiro sênior da Hard Produtos para Construção com 20 anos de experiência em fixadores e selantes..."
                  rows={5}
                />
              </div>

              {/* Regras */}
              <div className="editor-row">
                <label>
                  Regras de Comportamento
                  <span className="label-hint">{form.rules.length}/15</span>
                </label>
                <div className="rules-list">
                  {form.rules.map((rule, i) => (
                    <div key={i} className="rule-item">
                      <span className="rule-number">{i + 1}.</span>
                      <span className="rule-text">{rule}</span>
                      <button className="rule-remove" onClick={() => removeRule(i)}>✕</button>
                    </div>
                  ))}
                </div>
                {form.rules.length < 15 && (
                  <div className="rule-add-row">
                    <input
                      type="text"
                      value={newRule}
                      onChange={(e) => setNewRule(e.target.value)}
                      placeholder="Adicionar nova regra..."
                      onKeyDown={(e) => e.key === "Enter" && addRule()}
                      maxLength={200}
                    />
                    <button className="btn-add-rule" onClick={addRule} disabled={!newRule.trim()}>
                      +
                    </button>
                  </div>
                )}
              </div>

              {/* Temperatura (Slider Visual) */}
              <div className="editor-row">
                <label>
                  Temperamento
                  <span className="label-hint" style={{ color: getTempColor(form.temperature) }}>
                    {getTempLabel(form.temperature)} ({Math.round(form.temperature * 10)}/10)
                  </span>
                </label>
                <div className="temp-slider-container">
                  <span className="temp-label-left">🎯 Exato</span>
                  <input
                    type="range"
                    min="0"
                    max="10"
                    step="1"
                    value={Math.round(form.temperature * 10)}
                    onChange={(e) =>
                      setForm({ ...form, temperature: parseInt(e.target.value) / 10 })
                    }
                    className="temp-slider"
                    style={{
                      background: `linear-gradient(to right, #34d399 0%, #818cf8 50%, #fbbf24 100%)`,
                    }}
                  />
                  <span className="temp-label-right">🎨 Criativo</span>
                </div>
              </div>

              {/* Default */}
              <div className="editor-row-inline">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={form.is_default}
                    onChange={(e) => setForm({ ...form, is_default: e.target.checked })}
                  />
                  <span>Persona padrão ao abrir o chat</span>
                </label>
              </div>
            </div>

            {/* Footer do Editor */}
            <div className="editor-footer">
              {editing && (
                deleteConfirm === editing.id ? (
                  <div className="delete-confirm">
                    <span>Remover permanentemente?</span>
                    <button className="btn-confirm-delete" onClick={() => handleDelete(editing.id)}>
                      Sim, remover
                    </button>
                    <button className="btn-cancel-delete" onClick={() => setDeleteConfirm(null)}>
                      Cancelar
                    </button>
                  </div>
                ) : (
                  <button
                    className="btn-delete-persona"
                    onClick={() => setDeleteConfirm(editing.id)}
                  >
                    Remover
                  </button>
                )
              )}
              <div className="editor-actions">
                <button className="btn-cancel" onClick={closeEditor}>Cancelar</button>
                <button
                  className="btn-save-persona"
                  onClick={handleSave}
                  disabled={saving || !form.name.trim()}
                >
                  {saving ? "Salvando..." : editing ? "Salvar Alterações" : "Criar Especialista"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
