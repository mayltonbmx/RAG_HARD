/**
 * app.js — RAG Chat Frontend Logic
 */

// =================== NAVIGATION ===================

const navItems = document.querySelectorAll('.nav-item');
const views = document.querySelectorAll('.view');

navItems.forEach(item => {
    item.addEventListener('click', () => {
        const target = item.dataset.view;
        navItems.forEach(n => n.classList.remove('active'));
        item.classList.add('active');
        views.forEach(v => v.classList.remove('active'));
        document.getElementById(`view${capitalize(target)}`).classList.add('active');
        if (target === 'files') loadFiles();
        if (target === 'stats') loadStats();
    });
});

function capitalize(s) {
    return s.charAt(0).toUpperCase() + s.slice(1);
}

// =================== CHAT ===================

const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const btnSend = document.getElementById('btnSend');
const btnNewChat = document.getElementById('btnNewChat');
const welcomeScreen = document.getElementById('welcomeScreen');

let chatHistory = [];
let isWaiting = false;

// Auto-resize textarea
chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 160) + 'px';
});

// Send on Enter (Shift+Enter for newline)
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

btnSend.addEventListener('click', sendMessage);

// Suggestion chips
document.querySelectorAll('.suggestion-chip').forEach(chip => {
    chip.addEventListener('click', () => {
        chatInput.value = chip.dataset.question;
        sendMessage();
    });
});

// New Chat
btnNewChat.addEventListener('click', () => {
    chatHistory = [];
    chatMessages.innerHTML = '';
    chatMessages.appendChild(createWelcomeScreen());
    chatInput.value = '';
    chatInput.style.height = 'auto';
});

async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message || isWaiting) return;

    // Hide welcome screen
    const welcome = document.getElementById('welcomeScreen');
    if (welcome) welcome.remove();

    // Add user message
    appendMessage('user', message);
    chatHistory.push({ role: 'user', content: message });

    // Clear input
    chatInput.value = '';
    chatInput.style.height = 'auto';

    // Show thinking indicator
    const thinkingEl = appendThinking();
    isWaiting = true;
    btnSend.disabled = true;

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                history: chatHistory.slice(0, -1), // Exclude current message (already in prompt)
                top_k: 5,
            }),
        });

        const data = await res.json();

        // Remove thinking indicator
        thinkingEl.remove();

        if (data.error) {
            appendMessage('assistant', `❌ Erro: ${data.error}`);
        } else {
            appendMessage('assistant', data.answer, data.sources);
            chatHistory.push({ role: 'assistant', content: data.answer });
        }

    } catch (err) {
        thinkingEl.remove();
        appendMessage('assistant', '❌ Erro de conexão com o servidor. Verifique se o servidor está rodando.');
    } finally {
        isWaiting = false;
        btnSend.disabled = false;
        chatInput.focus();
    }
}

function appendMessage(role, content, sources = null) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-msg ${role}`;

    const avatarLabel = role === 'user' ? 'Eu' : 'AI';
    const renderedContent = role === 'assistant' ? renderMarkdown(content) : escapeHtml(content);

    let sourcesHtml = '';
    if (sources && sources.length > 0) {
        const sourceItems = sources.map(s => {
            const tagClass = getTagClass(s.file_type);
            return `<div class="source-item">
                <span class="source-score">${(s.score * 100).toFixed(1)}%</span>
                <span class="tag ${tagClass}">${(s.file_type || '').replace('.', '').toUpperCase()}</span>
                <span>${escapeHtml(s.filename)}</span>
            </div>`;
        }).join('');

        sourcesHtml = `
            <div class="msg-sources">
                <div class="msg-sources-title">📚 Documentos consultados</div>
                ${sourceItems}
            </div>
        `;
    }

    msgDiv.innerHTML = `
        <div class="msg-avatar">${avatarLabel}</div>
        <div class="msg-content">
            <div class="msg-bubble">${renderedContent}</div>
            ${sourcesHtml}
        </div>
    `;

    chatMessages.appendChild(msgDiv);
    scrollToBottom();
}

function appendThinking() {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-msg assistant';
    msgDiv.innerHTML = `
        <div class="msg-avatar">AI</div>
        <div class="msg-content">
            <div class="thinking-indicator">
                <div class="thinking-dots">
                    <span></span><span></span><span></span>
                </div>
                Buscando nos documentos e gerando resposta...
            </div>
        </div>
    `;
    chatMessages.appendChild(msgDiv);
    scrollToBottom();
    return msgDiv;
}

function scrollToBottom() {
    requestAnimationFrame(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
}

function createWelcomeScreen() {
    const div = document.createElement('div');
    div.className = 'welcome-screen';
    div.id = 'welcomeScreen';
    div.innerHTML = `
        <div class="welcome-icon">
            <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <polygon points="12 2 2 7 12 12 22 7 12 2"/>
                <polyline points="2 17 12 22 22 17"/>
                <polyline points="2 12 12 17 22 12"/>
            </svg>
        </div>
        <h2>Olá! Sou o assistente Hard CMP</h2>
        <p>Faça perguntas sobre catálogos, desenhos técnicos, fixadores e produtos. Eu busco nos seus documentos e respondo com inteligência.</p>
        <div class="welcome-suggestions">
            <button class="suggestion-chip" data-question="Quais fixadores autoperfurantes estão disponíveis?">🔩 Fixadores autoperfurantes</button>
            <button class="suggestion-chip" data-question="Como evitar goteiras na cobertura?">🏠 Coberturas sem goteiras</button>
            <button class="suggestion-chip" data-question="Quais são as linhas de produtos da Hard?">📋 Linhas de produtos</button>
            <button class="suggestion-chip" data-question="Me fale sobre a linha ZAPHIR">⚙️ Linha ZAPHIR</button>
        </div>
    `;

    // Re-attach click handlers for new chips
    setTimeout(() => {
        div.querySelectorAll('.suggestion-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                chatInput.value = chip.dataset.question;
                sendMessage();
            });
        });
    }, 0);

    return div;
}

// =================== MARKDOWN RENDERING ===================

function renderMarkdown(text) {
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,
            gfm: true,
        });
        return marked.parse(text);
    }
    // Fallback: basic formatting
    return escapeHtml(text).replace(/\n/g, '<br>');
}

// =================== UPLOAD ===================

const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const uploadProgress = document.getElementById('uploadProgress');
const uploadProgressBar = document.getElementById('uploadProgressBar');
const uploadStatusText = document.getElementById('uploadStatusText');
const uploadResults = document.getElementById('uploadResults');

if (uploadZone) {
    uploadZone.addEventListener('click', () => fileInput.click());
    uploadZone.addEventListener('dragover', (e) => { e.preventDefault(); uploadZone.classList.add('drag-over'); });
    uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault(); uploadZone.classList.remove('drag-over');
        if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files);
    });
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) handleFiles(fileInput.files);
    });
}

async function handleFiles(files) {
    uploadProgress.classList.remove('hidden');
    uploadProgressBar.style.width = '10%';
    uploadStatusText.textContent = `Enviando ${files.length} arquivo(s)...`;
    uploadResults.innerHTML = '';

    const formData = new FormData();
    for (const file of files) formData.append('files', file);

    try {
        uploadProgressBar.style.width = '40%';
        uploadStatusText.textContent = 'Gerando embeddings e armazenando...';

        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        uploadProgressBar.style.width = '100%';
        const data = await res.json();

        if (data.error) {
            uploadStatusText.textContent = 'Erro!';
            uploadResults.innerHTML = `<div class="upload-result-item error">❌ ${escapeHtml(data.error)}</div>`;
            return;
        }

        uploadStatusText.textContent = 'Concluído!';
        let html = '';
        if (data.success) data.success.forEach(f => {
            html += `<div class="upload-result-item success">✅ ${escapeHtml(f)} — ingerido com sucesso</div>`;
        });
        if (data.errors) data.errors.forEach(e => {
            html += `<div class="upload-result-item error">❌ ${escapeHtml(e.file)}: ${escapeHtml(e.error)}</div>`;
        });
        uploadResults.innerHTML = html;

    } catch (err) {
        uploadStatusText.textContent = 'Erro!';
        uploadResults.innerHTML = `<div class="upload-result-item error">❌ Erro de conexão.</div>`;
    }
    fileInput.value = '';
}

// =================== FILES ===================

async function loadFiles() {
    const grid = document.getElementById('filesGrid');
    grid.innerHTML = '<div class="loading-container"><div class="loading-spinner"></div><p>Carregando...</p></div>';

    try {
        const res = await fetch('/api/files');
        const data = await res.json();

        if (!data.files || data.files.length === 0) {
            grid.innerHTML = '<div class="no-results" style="grid-column:1/-1;"><h3>Nenhum arquivo</h3><p>Use Upload para adicionar.</p></div>';
            return;
        }
        grid.innerHTML = data.files.map(f => renderFileCard(f)).join('');
    } catch (err) {
        grid.innerHTML = '<div class="no-results" style="grid-column:1/-1;"><h3>Erro</h3></div>';
    }
}

function renderFileCard(file) {
    const ext = file.extension || '';
    const iconClass = ext === '.pdf' ? 'pdf' : ['.png','.jpg','.jpeg','.webp'].includes(ext) ? 'image' : ext === '.mp4' ? 'video' : 'audio';
    return `<div class="file-card">
        <div class="file-card-icon ${iconClass}">${getFileIcon(ext)}</div>
        <div class="file-card-name">${escapeHtml(file.name)}</div>
        <div class="file-card-meta">
            <span class="tag ${getTagClass(ext)}">${ext.replace('.','').toUpperCase()}</span>
            <span>${file.size_mb} MB</span>
        </div>
    </div>`;
}

// =================== STATS ===================

async function loadStats() {
    const grid = document.getElementById('statsGrid');
    grid.innerHTML = '<div class="loading-container"><div class="loading-spinner"></div><p>Carregando...</p></div>';

    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        if (data.error) { grid.innerHTML = `<div class="no-results"><h3>Erro</h3><p>${escapeHtml(data.error)}</p></div>`; return; }

        grid.innerHTML = `
            <div class="stat-card"><span class="stat-label">Vetores</span><span class="stat-value">${data.total_vectors}</span><span class="stat-detail">documentos indexados</span></div>
            <div class="stat-card"><span class="stat-label">Dimensão</span><span class="stat-value">${data.dimension}</span><span class="stat-detail">dimensões por vetor</span></div>
            <div class="stat-card"><span class="stat-label">Arquivos</span><span class="stat-value">${data.total_files || '—'}</span><span class="stat-detail">no diretório data/</span></div>
            <div class="stat-card"><span class="stat-label">Modelo</span><span class="stat-value" style="font-size:1.1rem">${escapeHtml(data.model)}</span><span class="stat-detail">Gemini Embedding</span></div>
        `;
    } catch (err) {
        grid.innerHTML = '<div class="no-results"><h3>Erro de conexão</h3></div>';
    }
}

// =================== UTILITIES ===================

function getFileIcon(ext) {
    const icons = { '.pdf':'📄', '.png':'🖼️', '.jpg':'🖼️', '.jpeg':'🖼️', '.webp':'🖼️', '.mp4':'🎬', '.mp3':'🎵', '.wav':'🎵' };
    return icons[ext] || '📁';
}

function getTagClass(ext) {
    if (ext === '.pdf') return 'tag-pdf';
    if (['.png','.jpg','.jpeg','.webp'].includes(ext)) return 'tag-image';
    if (ext === '.mp4') return 'tag-video';
    if (['.mp3','.wav'].includes(ext)) return 'tag-audio';
    return '';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
