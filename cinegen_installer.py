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
            --card-bg: rgba(14, 18, 27, 0.85);
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
                radial-gradient(circle at 15% 15%, rgba(124, 77, 255, 0.15) 0%, transparent 40%),
                radial-gradient(circle at 85% 85%, rgba(0, 240, 255, 0.12) 0%, transparent 40%);
            color: var(--text);
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            width: 100%;
            max-width: 820px;
            background: var(--card-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 35px 40px;
            box-shadow: 0 25px 60px rgba(0, 0, 0, 0.6), 0 0 40px rgba(0, 240, 255, 0.08);
            position: relative;
            overflow: hidden;
        }
        .container::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, var(--accent), var(--primary), var(--success));
        }
        .header {
            text-align: center;
            margin-bottom: 25px;
        }
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
            font-size: 2.4rem;
            font-weight: 900;
            letter-spacing: -0.5px;
            background: linear-gradient(135deg, #fff 40%, var(--primary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle {
            color: var(--text-dim);
            font-size: 0.9rem;
            margin-top: 6px;
        }
        .specs-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 25px;
        }
        .spec-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 14px;
            text-align: center;
        }
        .spec-icon { font-size: 1.4rem; margin-bottom: 4px; }
        .spec-title { font-size: 0.7rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 1px; }
        .spec-val { font-family: 'Outfit', sans-serif; font-size: 0.95rem; font-weight: 700; color: #fff; margin-top: 2px; }
        
        .btn-install {
            width: 100%;
            padding: 18px 25px;
            background: linear-gradient(135deg, #00d2ff, #0077ff);
            border: none;
            border-radius: 14px;
            color: #030a16;
            font-family: 'Outfit', sans-serif;
            font-size: 1.15rem;
            font-weight: 900;
            letter-spacing: 0.5px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            box-shadow: 0 10px 25px rgba(0, 180, 255, 0.35);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            margin-bottom: 25px;
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
        
        .progress-section {
            margin-bottom: 20px;
        }
        .progress-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            font-size: 0.85rem;
        }
        .status-msg {
            color: var(--primary);
            font-weight: 600;
        }
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
            position: relative;
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
            height: 220px;
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
        
        .footer-note {
            text-align: center;
            font-size: 0.75rem;
            color: var(--text-dim);
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="tagline">NarraVox Studios :: Official Setup</div>
            <h1>CINEGEN STUDIO</h1>
            <div class="subtitle">Instalador Oficial com Aceleração de Hardware (NVIDIA RTX 6GB VRAM)</div>
        </div>

        <div class="specs-grid">
            <div class="spec-card">
                <div class="spec-icon">⚡</div>
                <div class="spec-title">Aceleração</div>
                <div class="spec-val">NVIDIA CUDA 12</div>
            </div>
            <div class="spec-card">
                <div class="spec-icon">🎮</div>
                <div class="spec-title">Alvo de Memória</div>
                <div class="spec-val">6 GB VRAM</div>
            </div>
            <div class="spec-card">
                <div class="spec-icon">🤖</div>
                <div class="spec-title">Direção</div>
                <div class="spec-val">Agentes Autônomos</div>
            </div>
        </div>

        <button class="btn-install" id="btn-start" onclick="iniciarInstalacao()">
            <span>🚀</span> INICIAR INSTALAÇÃO DO CINEGEN
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
            <div class="log-entry log-info">[CINEGEN] Inicializador carregado. Clique no botão acima para iniciar a instalação.</div>
        </div>

        <div class="footer-note">
            CineGen v0.2.0 • Código aberto sob licença Apache 2.0 • Desenvolvido por Paulo Henrik (NarraVox Studios)
        </div>
    </div>

    <script>
        let pollingInterval = null;

        function appendLog(text, type='info') {
            const term = document.getElementById('terminal');
            const div = document.createElement('div');
            div.className = `log-entry log-${type}`;
            div.textContent = text;
            term.appendChild(div);
            term.scrollTop = term.scrollHeight;
        }

        async function iniciarInstalacao() {
            const btn = document.getElementById('btn-start');
            btn.disabled = true;
            btn.innerHTML = '<span>⏳</span> INSTALANDO CINEGEN STUDIO...';

            try {
                const res = await fetch('/api/start_install', { method: 'POST' });
                const data = await res.json();
                if (data.status === 'started' || data.status === 'running') {
                    startPolling();
                }
            } catch (err) {
                appendLog(`❌ Erro de conexão com o instalador: ${err}`, 'error');
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
                        if (l.includes('✅') || l.includes('sucesso') || l.includes('CONCLUÍDA')) type = 'success';
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
                            btn.innerHTML = '<span>🎬</span> INSTALAÇÃO CONCLUÍDA COM SUCESSO!';
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

def run_installation_worker():
    global IS_INSTALLING, INSTALL_FINISHED, INSTALL_SUCCESS
    IS_INSTALLING = True
    INSTALL_FINISHED = False
    INSTALL_SUCCESS = False

    try:
        log("🚀 [1/5] Verificando hardware e ambiente do sistema...")
        update_status(10, "Verificando hardware e aceleração GPU...")
        time.sleep(1)

        # Checa Python
        py_ver = sys.version.split()[0]
        log(f"   • Python detectado: {py_ver}")

        # Checa nvidia-smi
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
        log("📦 [2/5] Criando ambiente virtual isolado (venv_cinegen)...")
        update_status(25, "Criando ambiente virtual isolado...")

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

        update_status(40, "Atualizando gerenciador de pacotes pip...")
        subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        log("🧠 [3/5] Instalando PyTorch com aceleração CUDA 12...")
        update_status(55, "Instalando PyTorch CUDA 12...")

        # Instala Torch CUDA
        torch_cmd = [str(venv_python), "-m", "pip", "install", "torch", "torchvision", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cu124"]
        log("   • Baixando e instalando PyTorch CUDA 12.4 (aguarde alguns instantes)...")
        proc_torch = subprocess.Popen(torch_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc_torch.stdout:
            if "Successfully installed" in line or "Collecting" in line:
                log(f"     -> {line.strip()[:80]}")
        proc_torch.wait()

        log("📚 [4/5] Instalando dependências multimodais (Diffusers, Transformers, FastAPI)...")
        update_status(75, "Instalando dependências multimodais...")

        req_path = BASE_DIR / "requirements.txt"
        if req_path.exists():
            proc_req = subprocess.Popen([str(venv_python), "-m", "pip", "install", "-r", str(req_path)],
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in proc_req.stdout:
                if "Successfully installed" in line or "Requirement already" in line:
                    log(f"     -> {line.strip()[:80]}")
            proc_req.wait()
            log("   • Dependências multimodais instaladas com sucesso! ✅")

        log("📂 [5/5] Estruturando pastas de modelos e fila de produção dos Agentes...")
        update_status(90, "Estruturando diretórios de produção...")
        time.sleep(1)

        for p in ["models/images", "models/videos", "queue/inbox", "queue/completed", "projects"]:
            (BASE_DIR / p).mkdir(parents=True, exist_ok=True)
        log("   • Pastas do estúdio criadas com sucesso! ✅")

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

        update_status(100, "🎉 Instalação concluída com sucesso!")
        log("=========================================================================")
        log("🎉 PARABÉNS! O CINEGEN STUDIO ESTÁ 100% PRONTO PARA USO!")
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
                "logs": INSTALL_LOGS[-35:],
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
            if not IS_INSTALLING:
                t = threading.Thread(target=run_installation_worker, daemon=True)
                t.start()
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "started"}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Silencia logs HTTP no terminal

def main():
    print(f"🎬 Iniciando Servidor Visual do Instalador CineGen em http://127.0.0.1:{PORT} ...")
    server = HTTPServer(("127.0.0.1", PORT), SetupHTTPHandler)

    # Abre a interface visual
    def open_ui():
        time.sleep(0.8)
        try:
            import webview
            webview.create_window("CineGen Studio - Setup Oficial", f"http://127.0.0.1:{PORT}", width=880, height=720)
            webview.start()
            # Quando a janela fechar, finaliza o servidor
            server.shutdown()
        except ImportError:
            # Fallback seguro para navegador padrão
            webbrowser.open(f"http://127.0.0.1:{PORT}")

    t = threading.Thread(target=open_ui, daemon=True)
    t.start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
