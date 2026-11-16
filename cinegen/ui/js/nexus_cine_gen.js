// NEXUS CINE-GEN :: CONTROLADOR DE INTERFACE AUDIOVISUAL (v2026.DIRECTOR)

function addActor(name = '', gender = 'Feminino', previewSrc = null) {
    const list = document.getElementById('character-list');
    const id = Date.now() + Math.floor(Math.random() * 1000);
    const div = document.createElement('div');
    div.className = 'scene-item';
    div.id = `actor-card-${id}`;
    div.style = 'padding: 10px; flex-direction: column; align-items: stretch; position: relative; border-radius: 8px;';
    
    div.innerHTML = `
        <button onclick="document.getElementById('actor-card-${id}').remove()" style="position: absolute; top: 6px; right: 6px; background: none; border: none; color: var(--danger); cursor: pointer; font-weight: 800; font-size: 0.9rem;" title="Remover Personagem">×</button>
        <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 6px;">
            <img id="actor-preview-${id}" class="actor-preview" src="${previewSrc || ''}" style="${previewSrc ? 'display: block;' : 'display: none;'}">
            <input type="text" class="actor-name vram-badge" placeholder="Nome (Ex: Paulo)" value="${name}" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); color: #fff; width: 100%; font-family: 'Outfit'; font-size: 0.8rem;">
        </div>
        <div style="display: flex; gap: 8px; align-items: center;">
            <select class="actor-gender vram-badge" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); color: var(--text-dim); width: 100px; font-family: 'Outfit'; font-size: 0.75rem; cursor: pointer;">
                <option value="Feminino" ${gender === 'Feminino' ? 'selected' : ''}>Feminino</option>
                <option value="Masculino" ${gender === 'Masculino' ? 'selected' : ''}>Masculino</option>
            </select>
            <input type="file" class="actor-img" accept="image/*" onchange="previewActorImage(this, '${id}')" style="font-size: 0.7rem; color: var(--text-dim); width: 100%;">
        </div>
    `;
    list.appendChild(div);
}

function previewActorImage(input, id) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById(`actor-preview-${id}`);
            preview.src = e.target.result;
            preview.style.display = 'block';
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// Inicialização com personagens padrão
window.onload = () => {
    addActor('Paulo', 'Masculino');
    addActor('Carol', 'Feminino');
    loadSavedProjects();
};

async function loadSavedProjects() {
    try {
        const res = await fetch('/api/cine/projects');
        const data = await res.json();
        const select = document.getElementById('saved-projects-select');
        if (data.success && data.projects && data.projects.length > 0) {
            select.innerHTML = '<option value="">Selecione um projeto salvo para retomar ou visualizar...</option>';
            data.projects.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.job_id;
                const statusTag = p.completed ? '✅ Concluído' : `⏳ ${p.current_stage}`;
                opt.textContent = `[${p.progress || 0}%] ${p.title || p.job_id} (${statusTag})`;
                select.appendChild(opt);
            });
        } else {
            select.innerHTML = '<option value="">Nenhum projeto salvo encontrado</option>';
        }
    } catch(e) {
        console.error("Erro ao carregar projetos:", e);
    }
}

async function resumeSelectedProject() {
    const select = document.getElementById('saved-projects-select');
    const jobId = select.value;
    if (!jobId) {
        alert("Por favor, selecione um projeto salvo na lista.");
        return;
    }

    const btn = document.getElementById('resume-btn');
    btn.disabled = true;
    btn.textContent = "⏳ Retomando...";

    try {
        const res = await fetch('/api/cine/resume-project', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ job_id: jobId })
        });
        const data = await res.json();
        if (data.success) {
            document.getElementById('global-status-text').textContent = `🔄 Retomando projeto ${jobId}...`;
        } else {
            alert(data.error || "Falha ao retomar projeto.");
        }
    } catch(e) {
        console.error("Erro ao retomar:", e);
    } finally {
        btn.disabled = false;
        btn.textContent = "🔄 RETOMAR";
    }
}

async function startGeneration() {
    const script = document.getElementById('script-input').value.trim();
    if(!script) {
        alert("Por favor, digite ou cole o roteiro antes de iniciar.");
        return;
    }

    const btn = document.getElementById('start-btn');
    const statusText = document.getElementById('global-status-text');
    
    btn.disabled = true;
    btn.style.opacity = '0.5';
    btn.style.cursor = 'not-allowed';
    statusText.textContent = 'Orquestrando: Qwen 3.5 -> FLUX.3 -> Kandinsky 6.0 -> 2x SPAN...';

    const actorCards = document.querySelectorAll('#character-list .scene-item');
    const actors = [];
    
    for (let card of actorCards) {
        const nameInput = card.querySelector('.actor-name');
        const name = (nameInput && nameInput.value) ? nameInput.value.trim() : "Personagem";
        const gender = card.querySelector('.actor-gender').value;
        const fileInput = card.querySelector('.actor-img');
        let base64Img = null;
        
        if (fileInput.files && fileInput.files[0]) {
            base64Img = await new Promise((resolve) => {
                const reader = new FileReader();
                reader.onloadend = () => resolve(reader.result);
                reader.readAsDataURL(fileInput.files[0]);
            });
        }
        
        actors.push({ name, gender, image: base64Img });
    }

    try {
        const res = await fetch('/api/start-cine', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ 
                script: script,
                actors: actors
            })
        });
        const data = await res.json();
        if(!data.success) {
            alert(data.error || "Erro ao iniciar produção.");
            btn.disabled = false;
            btn.style.opacity = '1';
            btn.style.cursor = 'pointer';
        } else {
            setTimeout(loadSavedProjects, 2000);
        }
    } catch(e) {
        console.error("Erro na produção:", e);
        btn.disabled = false;
        btn.style.opacity = '1';
        btn.style.cursor = 'pointer';
    }
}

// Polling de monitoramento em tempo real a cada 1.5s
setInterval(async () => {
    try {
        const res = await fetch('/api/get-scenes');
        const data = await res.json();
        
        updateProgress(data.progress);
        updateSceneList(data.scenes);
        
        if (data.status) {
            document.getElementById('global-status-text').textContent = data.status;
        }

        // Atualiza Badges de Estatística
        const stageElem = document.getElementById('badge-stage-val');
        if (data.current_stage) {
            stageElem.textContent = data.current_stage.toUpperCase();
        }

        if (data.scenes && data.scenes.length > 0) {
            document.getElementById('badge-shots-val').textContent = data.scenes.length;
            const uniqueImgs = new Set(data.scenes.map(s => s.image_id)).size;
            const reusedCount = data.scenes.filter(s => s.is_reused).length;
            document.getElementById('badge-imgs-val').textContent = `${uniqueImgs} (${reusedCount} reusos)`;
        }

        // Verifica se concluiu e exibe player de vídeo
        if (data.completed && data.final_video) {
            showFinalVideo(data.final_video);
            const btn = document.getElementById('start-btn');
            btn.disabled = false;
            btn.style.opacity = '1';
            btn.style.cursor = 'pointer';
        }
    } catch(e) {}
}, 1500);

function updateSceneList(scenes) {
    const container = document.getElementById('scene-list');
    if(!scenes || scenes.length === 0) return;
    
    container.innerHTML = '';
    scenes.forEach(scene => {
        const div = document.createElement('div');
        div.className = 'scene-item';
        div.style = 'display: flex; justify-content: space-between; align-items: center; padding: 10px; margin-bottom: 8px; border-radius: 8px;';
        
        const badgeColor = scene.video_ready ? 'var(--accent)' : (scene.image_ready ? '#ffd700' : 'rgba(255,255,255,0.2)');
        const reuseBadge = scene.is_reused ? '<span style="background: rgba(124, 77, 255, 0.2); color: #b388ff; border: 1px solid #7c4dff; padding: 1px 6px; border-radius: 4px; font-size: 0.65rem; margin-left: 6px;">Reuso</span>' : '';
        
        div.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <div class="scene-thumb" style="width: 38px; height: 38px; background: rgba(0, 240, 255, 0.1); color: ${badgeColor}; font-weight: 800; font-size: 0.7rem; display: flex; align-items: center; justify-content: center; border-radius: 6px; border: 1px solid ${badgeColor};">
                    ${scene.id || 'SHOT'}
                </div>
                <div class="scene-info">
                    <h4 style="font-size: 0.85rem; margin: 0; color: #fff;">${scene.name} ${reuseBadge}</h4>
                    <p style="color: var(--text-dim); font-size: 0.72rem; margin-top: 3px; max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        ${scene.dialogue ? `"${scene.dialogue}"` : (scene.status || 'Pendente')}
                    </p>
                </div>
            </div>
            <div>
                ${scene.active ? '<span class="tag-active" style="background: var(--accent); color: #000; padding: 3px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 800; animation: pulse 1s infinite;">Processando</span>' : 
                  (scene.video_ready ? '<span style="color: var(--accent); font-size: 0.75rem; font-weight: 800;">✅ 1080p</span>' : 
                   `<span style="color: var(--text-dim); font-size: 0.7rem;">${scene.status}</span>`)}
            </div>
        `;
        container.appendChild(div);
    });
}

function updateProgress(p) {
    p = p || 0;
    document.getElementById('progress-bar').style.width = p + '%';
    document.getElementById('progress-text').textContent = p + '%';
}

function showFinalVideo(videoPath) {
    const box = document.getElementById('final-video-box');
    const player = document.getElementById('final-video-player');
    const link = document.getElementById('final-video-link');
    
    // Converte caminho local para rota servida pelo FastAPI
    const cleanPath = videoPath.replace(/\\/g, '/');
    let webUrl = cleanPath;
    if (cleanPath.includes('/projects/')) {
        webUrl = '/projects/' + cleanPath.split('/projects/')[1];
    }
    
    if (player.src !== window.location.origin + webUrl && !player.src.endsWith(webUrl)) {
        player.src = webUrl;
        link.href = webUrl;
        box.style.display = 'block';
    }
}
