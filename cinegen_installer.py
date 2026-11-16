# Copyright (c) 2026 Paulo Henrik Carvalho Araújo
# NarraVox Studios - CineGen Setup Professional
# Licença Apache 2.0

import os
import sys
import time
import json
import shutil
import subprocess
import threading
import urllib.request
import webbrowser
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 9123
CURRENT_PROGRESS = 0
CURRENT_STATUS = "Aguardando início da instalação..."
INSTALL_LOGS = []
IS_INSTALLING = False
INSTALL_FINISHED = False
INSTALL_SUCCESS = False

BASE_DIR = Path(__file__).resolve().parent

# =========================================================================
# CATÁLOGO DE MODELOS OFICIAIS DO CINEGEN
# =========================================================================
MODEL_TARGETS = {
    "flux": [
        {
            "name": "flux-3-image-klein-Q4_K_M.gguf (3.66 GB)",
            "repo": "unsloth/flux-3-image-klein-GGUF",
            "file": "flux-3-image-klein-Q4_K_M.gguf",
            "dest": BASE_DIR / "models" / "images" / "flux-3-image-klein-Q4_K_M.gguf",
            "comfy_copy": BASE_DIR / "comfyui" / "models" / "diffusion_models" / "flux-3-image-klein-Q4_K_M.gguf"
        },
        {
            "name": "ae.safetensors (VAE FLUX - 336 MB)",
            "repo": "black-forest-labs/FLUX.1-schnell",
            "file": "ae.safetensors",
            "dest": BASE_DIR / "models" / "images" / "ae.safetensors",
            "comfy_copy": BASE_DIR / "comfyui" / "models" / "vae" / "ae.safetensors"
        }
    ],
    "kandinsky": [
        {
            "name": "Kandinsky-6.0-Lite-Distilled-5s-int8-convrot.safetensors (3.24 GB)",
            "repo": "WaveCut/Kandinsky-6.0-Lite-distill-5s-OrbitQuant-W4A4",
            "file": "Kandinsky-6.0-Lite-Distilled-5s-int8-convrot.safetensors",
            "dest": BASE_DIR / "models" / "videos" / "Kandinsky-6.0-Lite-Distilled-5s-int8-convrot.safetensors",
            "comfy_copy": BASE_DIR / "comfyui" / "models" / "diffusion_models" / "Kandinsky-6.0-Lite-Distilled-5s-int8-convrot.safetensors"
        }
    ],
    "aux": [
        {
            "name": "clip_l.safetensors (246 MB)",
            "repo": "Comfy-Org/HunyuanVideo_repackaged",
            "file": "split_files/text_encoders/clip_l.safetensors",
            "dest": BASE_DIR / "comfyui" / "models" / "text_encoders" / "clip_l.safetensors"
        },
        {
            "name": "hunyuan_video_vae_bf16.safetensors (493 MB)",
            "repo": "Comfy-Org/HunyuanVideo_repackaged",
            "file": "split_files/vae/hunyuan_video_vae_bf16.safetensors",
            "dest": BASE_DIR / "comfyui" / "models" / "vae" / "hunyuan_video_vae_bf16.safetensors"
        },
        {
            "name": "bigvgan_generator.pt (489 MB)",
            "repo": "nvidia/bigvgan_v2_44khz_128band_512x",
            "file": "bigvgan_generator.pt",
            "dest": BASE_DIR / "comfyui" / "models" / "audio_vae" / "bigvgan_vocoder" / "bigvgan_generator.pt"
        },
        {
            "name": "2xNomosUni_span_multijpg.safetensors (4.4 MB)",
            "repo": "uwg/upscaler",
            "file": "2xNomosUni_span_multijpg.safetensors",
            "dest": BASE_DIR / "comfyui" / "models" / "upscale_models" / "2xNomosUni_span_multijpg.safetensors"
        }
    ]
}

HTML_CONTENT = """<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎬 CineGen Studio - Instalador Oficial</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Outfit:wght@400;700;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #07090e;
            --card-bg: rgba(14, 18, 27, 0.90);
            --primary: #00f0ff;
            --accent: #7c4dff;
            --success: #00ff88;
            --danger: #ff0055;
            --text: #f0f4f8;
            --text-dim: #7e8b9b;
            --border: rgba(0, 240, 255, 0.2);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg);
            background-image: 
                radial-gradient(circle at 15% 15%, rgba(124, 77, 255, 0.18) 0%, transparent 40%),
                radial-gradient(circle at 85% 85%, rgba(0, 240, 255, 0.15) 0%, transparent 40%);
            color: var(--text);
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 25px;
        }
        .container {
            width: 100%;
            max-width: 860px;
            background: var(--card-bg);
            backdrop-filter: blur(25px);
            border: 1px solid var(--border);
            border-radius: 22px;
            padding: 35px 40px;
            box-shadow: 0 25px 60px rgba(0, 0, 0, 0.7), 0 0 50px rgba(0, 240, 255, 0.1);
            position: relative;
            overflow: hidden;
        }
        .container::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, var(--accent), var(--primary), var(--success));
        }
        .header { text-align: center; margin-bottom: 22px; }
        .tagline {
            font-size: 0.75rem;
            font-weight: 800;
            color: var(--primary);
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-bottom: 6px;
        }
        h1 {
            font-family: 'Outfit', sans-serif;
            font-size: 2.3rem;
            font-weight: 900;
            letter-spacing: -0.5px;
            background: linear-gradient(135deg, #fff 40%, var(--primary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle { color: var(--text-dim); font-size: 0.88rem; margin-top: 5px; }

        .token-card {
            background: rgba(124, 77, 255, 0.08);
            border: 1px solid rgba(124, 77, 255, 0.3);
            border-radius: 14px;
            padding: 16px 20px;
            margin-bottom: 20px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .token-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.85rem;
            font-weight: 700;
            color: #d1b8ff;
        }
        .token-input-group {
            display: flex;
            gap: 10px;
        }
        .token-input {
            flex: 1;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 8px;
            padding: 10px 14px;
            color: #fff;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            outline: none;
            transition: all 0.3s;
        }
        .token-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 15px rgba(0, 240, 255, 0.25);
        }

        .modules-card {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 14px;
            padding: 16px 20px;
            margin-bottom: 22px;
        }
        .modules-title {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: var(--text-dim);
            font-weight: 800;
            margin-bottom: 12px;
        }
        .modules-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        .mod-item {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.85rem;
            color: #ddd;
            cursor: pointer;
            user-select: none;
        }
        .mod-item input { accent-color: var(--primary); width: 16px; height: 16px; }

        .btn-install {
            width: 100%;
            padding: 18px 25px;
            background: linear-gradient(135deg, #00d2ff, #0077ff);
            border: none;
            border-radius: 14px;
            color: #030a16;
            font-family: 'Outfit', sans-serif;
            font-size: 1.2rem;
            font-weight: 900;
            letter-spacing: 0.5px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            box-shadow: 0 10px 25px rgba(0, 180, 255, 0.35);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            margin-bottom: 22px;
        }
        .btn-install:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 15px 35px rgba(0, 180, 255, 0.5);
            background: linear-gradient(135deg, #33dcff, #1a8cff);
        }
        .btn-install:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        .progress-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            font-size: 0.85rem;
        }
        .status-msg { color: var(--primary); font-weight: 600; }
        .percent-badge {
            font-family: 'Outfit', sans-serif;
            font-weight: 800;
            color: #fff;
            background: rgba(0, 240, 255, 0.15);
            padding: 2px 10px;
            border-radius: 20px;
            border: 1px solid var(--primary);
        }
        .progress-bar-bg {
            width: 100%;
            height: 10px;
            background: rgba(255, 255, 255, 0.06);
            border-radius: 6px;
            overflow: hidden;
            margin-bottom: 18px;
        }
        .progress-bar-fill {
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, var(--accent), var(--primary), var(--success));
            border-radius: 6px;
            transition: width 0.3s ease;
        }

        .terminal-box {
            background: #04060a;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 16px;
            height: 230px;
            overflow-y: auto;
            font-family: 'JetBrains Mono', 'Consolas', monospace;
            font-size: 0.78rem;
            color: #9cb0c6;
            line-height: 1.5;
            scroll-behavior: smooth;
        }
        .terminal-box::-webkit-scrollbar { width: 6px; }
        .terminal-box::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 3px; }
        .log-entry { margin-bottom: 4px; word-break: break-all; }
        .log-info { color: #8ec8ff; }
        .log-success { color: var(--success); font-weight: 700; }
        .log-warn { color: #ffd15c; }
        .log-error { color: var(--danger); font-weight: 700; }

        .footer-note { text-align: center; font-size: 0.75rem; color: var(--text-dim); margin-top: 18px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="tagline">NarraVox Studios :: Official Setup</div>
            <h1>CINEGEN STUDIO</h1>
            <div class="subtitle">Instalador Completo de 1 Clique: Python, Dependências e Modelos Neurais</div>
        </div>

        <!-- Autenticação Hugging Face (Opcional / Modelos Gated) -->
        <div class="token-card">
            <div class="token-header">
                <span>🔑 Token Hugging Face (Opcional para Modelos Autorizados)</span>
                <a href="https://huggingface.co/settings/tokens" target="_blank" style="color: var(--primary); text-decoration: none; font-size: 0.75rem;">Obter Token ↗</a>
            </div>
            <div class="token-input-group">
                <input type="password" id="hf-token" class="token-input" placeholder="Cole seu token hf_... aqui se for baixar modelos autenticados">
            </div>
        </div>

        <!-- Módulos de Download -->
        <div class="modules-card">
            <div class="modules-title">Recursos da Instalação (Selecione o que deseja preparar):</div>
            <div class="modules-grid">
                <label class="mod-item">
                    <input type="checkbox" id="chk-deps" checked disabled>
                    <span>📦 Ambiente & PyTorch CUDA 12.4 (Obrigatório)</span>
                </label>
                <label class="mod-item">
                    <input type="checkbox" id="chk-flux" checked>
                    <span>🖼️ FLUX.3 Klein (4B GGUF + VAE)</span>
                </label>
                <label class="mod-item">
                    <input type="checkbox" id="chk-kandinsky" checked>
                    <span>🎬 Kandinsky 6.0 Lite (AV-DiT 24fps)</span>
                </label>
                <label class="mod-item">
                    <input type="checkbox" id="chk-aux" checked>
                    <span>✨ Upscale SPAN 1080p & Vocoder BigVGAN</span>
                </label>
            </div>
        </div>

        <button class="btn-install" id="btn-start" onclick="iniciarInstalacao()">
            <span>🚀</span> INICIAR INSTALAÇÃO COMPLETA (1 CLIQUE)
        </button>

        <div class="progress-section">
            <div class="progress-header">
                <span class="status-msg" id="status-label">Pronto para iniciar</span>
                <span class="percent-badge" id="percent-label">0%</span>
            </div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" id="progress-bar"></div>
            </div>
        </div>

        <div class="terminal-box" id="terminal">
            <div class="log-entry log-info">[CINEGEN] Inicializador carregado. Clique no botão acima para iniciar tudo de forma 100% automatizada.</div>
        </div>

        <div class="footer-note">
            CineGen v0.2.0 • Código aberto sob licença Apache 2.0 • Desenvolvido por Paulo Henrik (NarraVox Studios)
        </div>
    </div>

    <script>
        let pollingInterval = null;

        async function iniciarInstalacao() {
            const btn = document.getElementById('btn-start');
            btn.disabled = true;
            btn.innerHTML = '<span>⏳</span> EXECUTANDO INSTALAÇÃO & DOWNLOADS...';

            const payload = {
                token: document.getElementById('hf-token').value.trim(),
                download_flux: document.getElementById('chk-flux').checked,
                download_kandinsky: document.getElementById('chk-kandinsky').checked,
                download_aux: document.getElementById('chk-aux').checked
            };

            try {
                const res = await fetch('/api/start_install', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.status === 'started' || data.status === 'running') {
                    startPolling();
                }
            } catch (err) {
                alert(`Erro de conexão com o instalador: ${err}`);
                btn.disabled = false;
            }
        }

        function startPolling() {
            if (pollingInterval) clearInterval(pollingInterval);
            pollingInterval = setInterval(async () => {
                try {
                    const res = await fetch('/api/status');
                    const data = await res.json();
                    
                    document.getElementById('status-label').textContent = data.status;
                    document.getElementById('percent-label').textContent = `${data.progress}%`;
                    document.getElementById('progress-bar').style.width = `${data.progress}%`;

                    const term = document.getElementById('terminal');
                    term.innerHTML = '';
                    data.logs.forEach(l => {
                        const div = document.createElement('div');
                        let type = 'info';
                        if (l.includes('✅') || l.includes('sucesso') || l.includes('CONCLUÍDA') || l.includes('Pronto')) type = 'success';
                        else if (l.includes('⚠️') || l.includes('aviso')) type = 'warn';
                        else if (l.includes('❌') || l.includes('ERRO') || l.includes('falha')) type = 'error';
                        div.className = `log-entry log-${type}`;
                        div.textContent = l;
                        term.appendChild(div);
                    });
                    term.scrollTop = term.scrollHeight;

                    if (data.finished) {
                        clearInterval(pollingInterval);
                        const btn = document.getElementById('btn-start');
                        if (data.success) {
                            btn.disabled = false;
                            btn.style.background = 'linear-gradient(135deg, #00ff88, #00bb55)';
                            btn.innerHTML = '<span>🎬</span> INSTALAÇÃO & MODELOS CONCLUÍDOS COM SUCESSO!';
                            btn.onclick = () => alert('Basta executar INICIAR_CINEGEN.bat para começar a criar seus filmes!');
                        } else {
                            btn.disabled = false;
                            btn.style.background = 'linear-gradient(135deg, #ff0055, #bb0033)';
                            btn.innerHTML = '<span>❌</span> INSTALAÇÃO INTERROMPIDA (VER LOGS)';
                        }
                    }
                } catch(e) {}
            }, 800);
        }
    </script>
</body>
</html>
"""

def log(msg):
    global INSTALL_LOGS
    INSTALL_LOGS.append(msg)
    print(msg, flush=True)

def update_status(progress, status_msg):
    global CURRENT_PROGRESS, CURRENT_STATUS
    CURRENT_PROGRESS = progress
    CURRENT_STATUS = status_msg

def download_file_with_resume(url, dest_path, token=None):
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp, open(dest_path, "wb") as f:
        total_size = int(resp.headers.get("content-length", 0))
        downloaded = 0
        last_log_time = time.time()
        
        while True:
            chunk = resp.read(1024 * 1024)  # 1MB chunks
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            
            if time.time() - last_log_time > 2.0:
                last_log_time = time.time()
                pct = int((downloaded / total_size) * 100) if total_size > 0 else 0
                mb = downloaded / (1024 * 1024)
                tot_mb = total_size / (1024 * 1024)
                log(f"   ⬇️ {dest_path.name}: {mb:.1f}MB / {tot_mb:.1f}MB ({pct}%)")

def download_model_target(target, token=None):
    dest = Path(target["dest"])
    dest.parent.mkdir(parents=True, exist_ok=True)

    # 1. Checa se o arquivo já existe no destino direto
    if dest.exists() and dest.stat().st_size > 1024 * 1024:
        log(f"   ✅ {target['name']} já existe ({dest.stat().st_size / 1e6:.1f} MB), pulando.")
        return

    # 2. Checa se já existe na pasta ComfyUI e faz link/cópia rápida
    if "comfy_copy" in target:
        comfy_p = Path(target["comfy_copy"])
        if comfy_p.exists() and comfy_p.stat().st_size > 1024 * 1024:
            log(f"   ⚡ Encontrada cópia local em ComfyUI ({comfy_p.name}). Sincronizando...")
            try:
                os.link(str(comfy_p), str(dest))
            except Exception:
                shutil.copy2(str(comfy_p), str(dest))
            log(f"   ✅ {target['name']} sincronizado com sucesso!")
            return

    # 3. Download via Hugging Face Hub
    log(f"   🌐 Baixando {target['name']} de {target['repo']}...")
    try:
        from huggingface_hub import hf_hub_download
        downloaded_path = hf_hub_download(
            repo_id=target["repo"],
            filename=target["file"],
            token=token,
            local_dir=str(dest.parent),
            local_dir_use_symlinks=False
        )
        # Se baixou com subpasta, move para o destino final
        dl_p = Path(downloaded_path)
        if dl_p != dest and dl_p.exists():
            shutil.move(str(dl_p), str(dest))
        log(f"   ✅ Download de {target['name']} concluído com sucesso!")
    except Exception as e:
        log(f"   ⚠️ Falha ao baixar {target['name']}: {e}")

def run_installation_worker(config):
    global IS_INSTALLING, INSTALL_FINISHED, INSTALL_SUCCESS
    IS_INSTALLING = True
    INSTALL_FINISHED = False
    INSTALL_SUCCESS = False

    hf_token = config.get("token") or None
    if hf_token:
        log("🔑 Token do Hugging Face detectado. Autenticando...")
        try:
            from huggingface_hub import login
            login(token=hf_token)
            log("   • Autenticação no Hugging Face realizada com sucesso! ✅")
        except Exception:
            pass

    try:
        log("🚀 [1/6] Verificando hardware e ambiente do sistema...")
        update_status(10, "Verificando hardware e aceleração GPU...")
        time.sleep(1)

        py_ver = sys.version.split()[0]
        log(f"   • Python detectado: {py_ver}")

        try:
            gpu_res = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
            if gpu_res.returncode == 0:
                gpu_info = gpu_res.stdout.strip()
                log(f"   • GPU NVIDIA Detectada: {gpu_info} ✅")
            else:
                log("   • ⚠️ Placa NVIDIA não detectada via nvidia-smi (modo CPU).")
        except Exception:
            log("   • ⚠️ nvidia-smi indisponível.")

        time.sleep(1)
        log("📦 [2/6] Criando ambiente virtual isolado (venv_cinegen)...")
        update_status(20, "Criando ambiente virtual isolado...")

        venv_dir = BASE_DIR / "venv_cinegen"
        venv_python = venv_dir / "Scripts" / "python.exe"

        if not venv_python.exists():
            res = subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if res.returncode != 0:
                log(f"   ❌ Erro ao criar venv: {res.stderr.decode('utf-8', errors='ignore')}")
                INSTALL_FINISHED = True
                return
            log("   • Ambiente virtual venv_cinegen criado com sucesso! ✅")
        else:
            log("   • Ambiente virtual já existente. Prosseguindo...")

        update_status(30, "Atualizando pip e instalando PyTorch CUDA 12...")
        subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        log("🧠 [3/6] Instalando PyTorch com aceleração CUDA 12...")
        torch_cmd = [str(venv_python), "-m", "pip", "install", "torch", "torchvision", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cu124"]
        log("   • Configurando PyTorch CUDA 12.4 (aguarde alguns instantes)...")
        proc_torch = subprocess.Popen(torch_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc_torch.stdout:
            if "Successfully installed" in line or "Collecting" in line:
                log(f"     -> {line.strip()[:80]}")
        proc_torch.wait()

        log("📚 [4/6] Instalando dependências multimodais (Diffusers, Transformers, FastAPI)...")
        update_status(45, "Instalando dependências multimodais...")

        req_path = BASE_DIR / "requirements.txt"
        if req_path.exists():
            proc_req = subprocess.Popen([str(venv_python), "-m", "pip", "install", "-r", str(req_path)],
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in proc_req.stdout:
                if "Successfully installed" in line or "Requirement already" in line:
                    log(f"     -> {line.strip()[:80]}")
            proc_req.wait()
            log("   • Dependências multimodais instaladas com sucesso! ✅")

        # Garante huggingface_hub no ambiente
        subprocess.run([str(venv_python), "-m", "pip", "install", "huggingface_hub"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        log("📂 [5/6] Estruturando pastas de modelos e fila de produção dos Agentes...")
        update_status(55, "Estruturando diretórios de produção...")
        for p in ["models/images", "models/videos", "queue/inbox", "queue/completed", "projects"]:
            (BASE_DIR / p).mkdir(parents=True, exist_ok=True)
        log("   • Pastas do estúdio criadas com sucesso! ✅")

        # 6. DOWNLOAD DOS MODELOS OFICIAIS SELECIONADOS
        log("🎬 [6/6] Verificando e baixando modelos neurais oficiais...")
        
        # A. FLUX.3 Klein
        if config.get("download_flux", True):
            update_status(65, "Baixando modelos do FLUX.3 Klein...")
            log("   --- [FLUX.3 Klein (4B GGUF + VAE)] ---")
            for t in MODEL_TARGETS["flux"]:
                download_model_target(t, token=hf_token)

        # B. Kandinsky 6.0 Lite
        if config.get("download_kandinsky", True):
            update_status(80, "Baixando modelos do Kandinsky 6.0 Lite...")
            log("   --- [Kandinsky 6.0 Lite AV-DiT (Vídeo + Áudio)] ---")
            for t in MODEL_TARGETS["kandinsky"]:
                download_model_target(t, token=hf_token)

        # C. Auxiliares & Upscale SPAN
        if config.get("download_aux", True):
            update_status(90, "Baixando componentes auxiliares e Upscale 1080p...")
            log("   --- [Upscale SPAN 1080p & Vocoder BigVGAN] ---")
            for t in MODEL_TARGETS["aux"]:
                download_model_target(t, token=hf_token)

        # Cria launcher rápido
        launcher_bat = BASE_DIR / "INICIAR_CINEGEN.bat"
        launcher_content = """@echo off
chcp 65001 >nul
title 🎬 CINEGEN STUDIO - INICIALIZADOR
color 0a
cls
echo =========================================================================
echo              🎬 CINEGEN - AUTONOMOUS AI CINEMA STUDIO
echo =========================================================================
echo.
echo Escolha o modo de operação:
echo  [1] Iniciar Estúdio Web Completo (FastAPI + Interface Gráfica)
echo  [2] Iniciar Fila de Produção Automática (Watcher de Cenas Bionic)
echo  [3] Abrir Terminal do Ambiente Virtual CineGen
echo  [4] Sair
echo.
echo =========================================================================
set /p MODO="Digite o número da opção (1-4): "
if "%MODO%"=="1" (
    cls
    echo 🚀 Iniciando CineGen Studio em http://127.0.0.1:8000 ...
    call venv_cinegen\\Scripts\\activate.bat
    python -m cinegen serve --port 8000
)
if "%MODO%"=="2" (
    cls
    echo 🤖 Iniciando Motor de Fila Automática de Cenas...
    call venv_cinegen\\Scripts\\activate.bat
    python scripts\\cinegen_auto_engine.py
)
if "%MODO%"=="3" (
    cls
    echo 💻 Terminal ativado no ambiente CineGen. Digite 'deactivate' para sair.
    cmd /k venv_cinegen\\Scripts\\activate.bat
)
"""
        launcher_bat.write_text(launcher_content, encoding="utf-8")
        log(f"   • Inicializador rápido criado: {launcher_bat.name} ✅")

        update_status(100, "🎉 Instalação e modelos prontos com sucesso!")
        log("=========================================================================")
        log("🎉 PARABÉNS! O CINEGEN STUDIO E TODOS OS MODELOS ESTÃO PRONTOS!")
        log("   Para criar seus filmes, basta dar 2 cliques em INICIAR_CINEGEN.bat")
        log("=========================================================================")
        INSTALL_SUCCESS = True

    except Exception as e:
        log(f"❌ Erro fatal durante a instalação: {e}")
        update_status(CURRENT_PROGRESS, "Erro na instalação.")
    finally:
        IS_INSTALLING = False
        INSTALL_FINISHED = True

class SetupHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global CURRENT_PROGRESS, CURRENT_STATUS, INSTALL_LOGS, INSTALL_FINISHED, INSTALL_SUCCESS
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode("utf-8"))
        elif self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            data = {
                "progress": CURRENT_PROGRESS,
                "status": CURRENT_STATUS,
                "logs": INSTALL_LOGS[-45:],
                "finished": INSTALL_FINISHED,
                "success": INSTALL_SUCCESS
            }
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global IS_INSTALLING
        if self.path == "/api/start_install":
            content_len = int(self.headers.get("content-length", 0))
            body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
            try:
                config = json.loads(body)
            except Exception:
                config = {}

            if not IS_INSTALLING:
                t = threading.Thread(target=run_installation_worker, args=(config,), daemon=True)
                t.start()

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "started"}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

def main():
    print(f"🎬 Iniciando Servidor Visual do Instalador CineGen em http://127.0.0.1:{PORT} ...")
    server = HTTPServer(("127.0.0.1", PORT), SetupHTTPHandler)

    def open_ui():
        time.sleep(0.8)
        try:
            import webview
            webview.create_window("CineGen Studio - Setup Oficial", f"http://127.0.0.1:{PORT}", width=900, height=760)
            webview.start()
            server.shutdown()
        except ImportError:
            webbrowser.open(f"http://127.0.0.1:{PORT}")

    t = threading.Thread(target=open_ui, daemon=True)
    t.start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
